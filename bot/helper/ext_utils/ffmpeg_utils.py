from os import path as ospath, walk
from shlex import split
from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from aiofiles.os import path as aiopath, remove, makedirs, listdir
from aioshutil import move

from bot import LOGGER, user_data, config_dict
from bot.helper.ext_utils.leech_utils import get_document_type
from bot.helper.ext_utils.bot_utils import cmd_exec


async def resolve_ffmpeg_cmds(ffmpeg_cmds, user_id):
    """Resolve named ffmpeg command keys (e.g., 'keep_japanese') to actual command strings.

    Args:
        ffmpeg_cmds: Either a string key name or a list of command strings.
        user_id: The user ID to look up FFMPEG_CMDS dict from user_data.

    Returns:
        A list of raw ffmpeg command strings, or None if resolution fails.
    """
    if isinstance(ffmpeg_cmds, list):
        return ffmpeg_cmds

    if isinstance(ffmpeg_cmds, str):
        user_dict = user_data.get(user_id, {})
        ffmpeg_dict = user_dict.get("ffmpeg_cmds", {})

        if not ffmpeg_dict:
            ffmpeg_dict = config_dict.get("FFMPEG_CMDS", {})

        if not ffmpeg_dict:
            LOGGER.error(f"No FFMPEG_CMDS configured for user {user_id}")
            return None

        keys = [k.strip() for k in ffmpeg_cmds.split(",")]
        resolved = []
        for key in keys:
            if key in ffmpeg_dict:
                resolved.extend(ffmpeg_dict[key])
            else:
                LOGGER.error(f"FFmpeg key '{key}' not found in user's FFMPEG_CMDS dict")
                return None
        return resolved if resolved else None

    return None


async def proceed_ffmpeg(listener, dl_path, ffmpeg_cmds, gid):
    """Run custom ffmpeg commands on downloaded files.

    This processes all video/audio files in dl_path with the given ffmpeg commands.
    Supports the 'mltb' placeholder for dynamic file naming and '-del' for deleting originals.

    Args:
        listener: The MirrorLeechListener instance.
        dl_path: Path to the downloaded file or directory.
        ffmpeg_cmds: List of raw ffmpeg command strings.
        gid: The download GID for status tracking.

    Returns:
        Updated dl_path after ffmpeg processing, or False if cancelled.
    """
    from bot.helper.ext_utils.fs_utils import get_path_size

    cmds = []
    for item in ffmpeg_cmds:
        parts = [p.strip() for p in split(item) if p.strip()]
        cmds.append(parts)

    for ffmpeg_cmd in cmds:
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
        ] + ffmpeg_cmd

        # Check for -del flag
        delete_files = False
        if "-del" in cmd:
            cmd.remove("-del")
            delete_files = True

        # Find the input file placeholder position
        if "-i" not in cmd:
            LOGGER.error(f"FFmpeg cmd missing -i: {ffmpeg_cmd}")
            continue

        index = cmd.index("-i")
        input_file = cmd[index + 1]

        # Determine file extension filter
        if input_file.strip().endswith(".video"):
            ext = "video"
        elif input_file.strip().endswith(".audio"):
            ext = "audio"
        elif "." not in input_file:
            ext = "all"
        else:
            ext = ospath.splitext(input_file)[-1].lower()

        if await aiopath.isfile(dl_path):
            # Single file
            is_video, is_audio, _ = await get_document_type(dl_path)
            if not is_video and not is_audio:
                continue
            elif is_video and ext == "audio":
                continue
            elif is_audio and not is_video and ext == "video":
                continue
            elif ext not in ["all", "audio", "video"] and not dl_path.strip().lower().endswith(ext):
                continue

            new_folder = ospath.splitext(dl_path)[0]
            if await aiopath.isfile(new_folder):
                new_folder = f"{new_folder}_temp"
            name = ospath.basename(dl_path)
            await makedirs(new_folder, exist_ok=True)
            file_path = f"{new_folder}/{name}"
            await move(dl_path, file_path)

            LOGGER.info(f"Running ffmpeg cmd for: {file_path}")
            var_cmd = cmd.copy()
            var_cmd[index + 1] = file_path

            # Replace mltb placeholders in output args
            outputs = _replace_mltb(var_cmd, file_path, new_folder)

            if listener.suproc == "cancelled":
                return False

            listener.suproc = await create_subprocess_exec(
                *var_cmd, stdout=PIPE, stderr=PIPE
            )
            code = await listener.suproc.wait()
            if code == -9:
                return False
            elif code != 0:
                stderr = (await listener.suproc.stderr.read()).decode().strip()
                LOGGER.error(f"FFmpeg error: {stderr}. Path: {file_path}")
                # Move file back
                await move(file_path, dl_path)
                from aioshutil import rmtree
                await rmtree(new_folder, ignore_errors=True)
                continue

            if delete_files:
                await remove(file_path)
                remaining = await listdir(new_folder)
                if len(remaining) == 1:
                    folder = new_folder.rsplit("/", 1)[0]
                    out_name = remaining[0]
                    if out_name.startswith("ffmpeg"):
                        out_name = out_name.split(".", 1)[-1]
                    dl_path = ospath.join(folder, out_name)
                    await move(ospath.join(new_folder, remaining[0]), dl_path)
                    from aioshutil import rmtree
                    await rmtree(new_folder, ignore_errors=True)
                    listener.name = ospath.basename(dl_path)
                else:
                    dl_path = new_folder
                    listener.name = new_folder.rsplit("/", 1)[-1]
            else:
                dl_path = new_folder
                listener.name = new_folder.rsplit("/", 1)[-1]
        else:
            # Directory of files
            for dirpath, _, files in walk(dl_path, topdown=False):
                for file_ in files:
                    if listener.suproc == "cancelled":
                        return False
                    f_path = ospath.join(dirpath, file_)
                    is_video, is_audio, _ = await get_document_type(f_path)
                    if not is_video and not is_audio:
                        continue
                    elif is_video and ext == "audio":
                        continue
                    elif is_audio and not is_video and ext == "video":
                        continue
                    elif ext not in ["all", "audio", "video"] and not f_path.strip().lower().endswith(ext):
                        continue

                    LOGGER.info(f"Running ffmpeg cmd for: {f_path}")
                    var_cmd = cmd.copy()
                    var_cmd[index + 1] = f_path

                    outputs = _replace_mltb(var_cmd, f_path, dirpath)

                    listener.suproc = await create_subprocess_exec(
                        *var_cmd, stdout=PIPE, stderr=PIPE
                    )
                    code = await listener.suproc.wait()
                    if code == -9:
                        return False
                    elif code != 0:
                        stderr = (await listener.suproc.stderr.read()).decode().strip()
                        LOGGER.error(f"FFmpeg error: {stderr}. Path: {f_path}")
                        for op in outputs:
                            if await aiopath.exists(op):
                                await remove(op)
                        continue

                    if delete_files:
                        await remove(f_path)
                        for res in outputs:
                            if await aiopath.exists(res):
                                file_name = ospath.basename(res)
                                if file_name.startswith("ffmpeg"):
                                    newname = file_name.split(".", 1)[-1]
                                    newres = ospath.join(dirpath, newname)
                                    await move(res, newres)
    return dl_path


def _replace_mltb(cmd, f_path, out_dir):
    """Replace 'mltb' placeholders in the ffmpeg command with actual file paths.

    Returns a list of output file paths that were substituted.
    """
    base_name, ext = ospath.splitext(ospath.basename(f_path))
    outputs = []

    indices = [
        i for i, item in enumerate(cmd)
        if item.startswith("mltb") or item == "mltb"
    ]

    for idx in indices:
        output_file = cmd[idx]
        if output_file != "mltb" and output_file.startswith("mltb"):
            bo, oext = ospath.splitext(output_file)
            if oext:
                if ext == oext:
                    prefix = f"ffmpeg{idx}." if bo == "mltb" else ""
                else:
                    prefix = ""
                ext_to_use = ""
            else:
                prefix = ""
                ext_to_use = ext
        else:
            prefix = f"ffmpeg{idx}."
            ext_to_use = ext

        output = f"{out_dir}/{prefix}{output_file.replace('mltb', base_name)}{ext_to_use}"
        outputs.append(output)
        cmd[idx] = output

    return outputs
