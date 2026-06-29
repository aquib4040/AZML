#!/usr/bin/env python3
from os import walk, path as ospath
from aiofiles.os import remove as aioremove, path as aiopath, listdir, rmdir, makedirs
from aioshutil import rmtree as aiormtree, move
from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from shutil import rmtree, disk_usage
from magic import Magic
from re import split as re_split, I, search as re_search
from subprocess import run as srun
from sys import exit as sexit
from bot import bot_cache

from .exceptions import NotSupportedExtractionArchive
from bot import aria2, LOGGER, DOWNLOAD_DIR, get_client, GLOBAL_EXTENSION_FILTER, user_data
from bot.helper.ext_utils.bot_utils import sync_to_async, cmd_exec
from bot.helper.ext_utils.subtitle_utils import get_intro_subtitle_filter, create_subtitle_file

ARCH_EXT = [
    ".tar.bz2",
    ".tar.gz",
    ".bz2",
    ".gz",
    ".tar.xz",
    ".tar",
    ".tbz2",
    ".tgz",
    ".lzma2",
    ".zip",
    ".7z",
    ".z",
    ".rar",
    ".iso",
    ".wim",
    ".cab",
    ".apm",
    ".arj",
    ".chm",
    ".cpio",
    ".cramfs",
    ".deb",
    ".dmg",
    ".fat",
    ".hfs",
    ".lzh",
    ".lzma",
    ".mbr",
    ".msi",
    ".mslz",
    ".nsis",
    ".ntfs",
    ".rpm",
    ".squashfs",
    ".udf",
    ".vhd",
    ".xar",
]

FIRST_SPLIT_REGEX = r"(\.|_)part0*1\.rar$|(\.|_)7z\.0*1$|(\.|_)zip\.0*1$|^(?!.*(\.|_)part\d+\.rar$).*\.rar$"

SPLIT_REGEX = r"\.r\d+$|\.7z\.\d+$|\.z\d+$|\.zip\.\d+$"


def is_first_archive_split(file):
    return bool(re_search(FIRST_SPLIT_REGEX, file))


def is_archive(file):
    return file.endswith(tuple(ARCH_EXT))


def is_archive_split(file):
    return bool(re_search(SPLIT_REGEX, file))


async def clean_target(path):
    if await aiopath.exists(path):
        LOGGER.info(f"Cleaning Target: {path}")
        if await aiopath.isdir(path):
            try:
                await aiormtree(path)
            except Exception:
                pass
        elif await aiopath.isfile(path):
            try:
                await aioremove(path)
            except Exception:
                pass


async def clean_download(path):
    if await aiopath.exists(path):
        LOGGER.info(f"Cleaning Download: {path}")
        try:
            await aiormtree(path)
        except Exception:
            pass


async def start_cleanup():
    get_client().torrents_delete(torrent_hashes="all")
    try:
        await aiormtree(DOWNLOAD_DIR)
    except Exception:
        pass
    await makedirs(DOWNLOAD_DIR, exist_ok=True)


def clean_all():
    aria2.remove_all(True)
    get_client().torrents_delete(torrent_hashes="all")
    try:
        rmtree(DOWNLOAD_DIR)
    except Exception:
        pass


def exit_clean_up(signal, frame):
    try:
        LOGGER.info("Please wait, while we clean up and stop the running downloads")
        clean_all()
        srun(["pkill", "-9", "-f", "gunicorn|aria2c|qbittorrent-nox|ffmpeg"])
        sexit(0)
    except KeyboardInterrupt:
        LOGGER.warning("Force Exiting before the cleanup finishes!")
        sexit(1)


async def clean_unwanted(path):
    LOGGER.info(f"Cleaning unwanted files/folders: {path}")
    for dirpath, _, files in await sync_to_async(walk, path, topdown=False):
        for filee in files:
            if (
                filee.endswith(".!qB")
                or filee.endswith(".parts")
                and filee.startswith(".")
            ):
                await aioremove(ospath.join(dirpath, filee))
        if dirpath.endswith((".unwanted", "splited_files_mltb", "copied_mltb")):
            await aiormtree(dirpath)
    for dirpath, _, files in await sync_to_async(walk, path, topdown=False):
        if not await listdir(dirpath):
            await rmdir(dirpath)


async def get_path_size(path):
    if await aiopath.isfile(path):
        return await aiopath.getsize(path)
    total_size = 0
    for root, dirs, files in await sync_to_async(walk, path):
        for f in files:
            abs_path = ospath.join(root, f)
            total_size += await aiopath.getsize(abs_path)
    return total_size


async def count_files_and_folders(path):
    total_files = 0
    total_folders = 0
    for _, dirs, files in await sync_to_async(walk, path):
        total_files += len(files)
        for f in files:
            if f.endswith(tuple(GLOBAL_EXTENSION_FILTER)):
                total_files -= 1
        total_folders += len(dirs)
    return total_folders, total_files


def get_base_name(orig_path):
    extension = next((ext for ext in ARCH_EXT if orig_path.lower().endswith(ext)), "")
    if extension != "":
        return re_split(f"{extension}$", orig_path, maxsplit=1, flags=I)[0]
    else:
        raise NotSupportedExtractionArchive("File format not supported for extraction")


def get_mime_type(file_path):
    mime = Magic(mime=True)
    mime_type = mime.from_file(file_path)
    mime_type = mime_type or "text/plain"
    return mime_type


async def fix_archive_extension(file_path):
    if is_archive(file_path):
        return file_path
    ext = ""
    mime_type = await sync_to_async(get_mime_type, file_path)
    if mime_type == "application/zip":
        ext = ".zip"
    elif mime_type in ["application/x-rar-compressed", "application/vnd.rar", "application/x-rar"]:
        ext = ".rar"
    elif mime_type == "application/x-7z-compressed":
        ext = ".7z"
    elif mime_type in ["application/x-tar", "application/tar"]:
        ext = ".tar"
    elif mime_type in ["application/gzip", "application/x-gzip"]:
        ext = ".gz"
    elif mime_type in ["application/x-bzip2", "application/bzip2"]:
        ext = ".bz2"

    if ext:
        new_path = file_path + ext
        await move(file_path, new_path)
        LOGGER.info(f"Fixed archive extension: {file_path} -> {new_path}")
        return new_path
    return file_path


def check_storage_threshold(size, threshold, arch=False, alloc=False):
    free = disk_usage(DOWNLOAD_DIR).free
    if not alloc:
        if (
            not arch
            and free - size < threshold
            or arch
            and free - (size * 2) < threshold
        ):
            return False
    elif not arch:
        if free < threshold:
            return False
    elif free - size < threshold:
        return False
    return True


async def join_files(path):
    files = await listdir(path)
    results = []
    for file_ in files:
        if (
            re_search(r"\.0+2$", file_)
            and await sync_to_async(get_mime_type, f"{path}/{file_}")
            == "application/octet-stream"
        ):
            final_name = file_.rsplit(".", 1)[0]
            cmd = f"cat {path}/{final_name}.* > {path}/{final_name}"
            _, stderr, code = await cmd_exec(cmd, True)
            if code != 0:
                LOGGER.error(f"Failed to join {final_name}, stderr: {stderr}")
            else:
                results.append(final_name)
        else:
            LOGGER.warning("No Binary files to join!")
    if results:
        LOGGER.info("Join Completed!")
        for res in results:
            for file_ in files:
                if re_search(rf"{res}\.0[0-9]+$", file_):
                    await aioremove(f"{path}/{file_}")


async def edit_metadata(
    listener, base_dir: str, media_file: str, outfile: str, metadata: str = ""
):
    # Get user intro subtitle settings
    user_id = listener.user_id if hasattr(listener, 'user_id') else None
    intro_settings = {}
    srt_file = None
    
    if user_id:
        intro_settings = user_data.get(user_id, {}).get("intro_subtitle", {})
    
    intro_enabled = intro_settings.get("enabled", True)
    wants_intro = intro_settings.get("text") and intro_enabled
    
    cmd = [
        bot_cache["pkgs"][2],
        "-hide_banner",
        "-loglevel",
        "error",
        "-ignore_unknown",
        "-i",
        media_file,
    ]
    
    # Add intro subtitle file as second input if configured and enabled
    if wants_intro:
        try:
            mode = intro_settings.get("mode", "softsub")
            if mode == "softsub":
                srt_file = create_subtitle_file(intro_settings, media_file)
                if srt_file:
                    cmd.extend(["-i", srt_file])
                    LOGGER.info(f"Added softsub intro subtitle: {srt_file}")
        except Exception as e:
            LOGGER.error(f"Error adding intro subtitle: {e}")
    
    # Add metadata
    cmd.extend([
        "-metadata",
        f"title=Encoded By {metadata}",
        "-metadata:s:v",
        f"title={metadata}",
        "-metadata",
        "Comment=",
        "-metadata",
        "Copyright=",
        "-metadata",
        f"AUTHOR={metadata}",
        "-metadata",
        "Encoded by=",
        "-metadata",
        "SYNOPSIS=",
        "-metadata",
        "ARTIST=",
        "-metadata",
        "PURL=",
        "-metadata",
        "Encoded_by=",
        "-metadata",
        "Description=",
        "-metadata",
        "description=",
        "-metadata",
        "SUMMARY=",
        "-metadata",
        "WEBSITE=",
        "-metadata:s:a",
        f"title={metadata}",
        "-metadata:s:s",
        f"title={metadata}",
        "-map",
        "0:v:0?",
        "-map",
        "0:a:?",
        "-map",
        "0:s:?",
    ])
    
    # Add softsub subtitle mapping if exists
    if srt_file and intro_settings.get("mode") == "softsub":
        cmd.extend(["-map", "1:0"])
        # Use proper subtitle codec based on output format
        ext = outfile.rsplit(".", 1)[-1].lower() if "." in outfile else ""
        if ext == "mkv":
            cmd.extend(["-c:s", "srt"])
        else:
            cmd.extend(["-c:s", "mov_text"])
        # Set the intro subtitle as the default subtitle track
        cmd.extend(["-disposition:s:0", "default"])
        LOGGER.info(f"Set intro subtitle as default track")
    
    # Add hardsub video filter if needed
    if wants_intro and intro_settings.get("mode") == "hardsub":
        try:
            subtitle_filter = get_intro_subtitle_filter(intro_settings)
            if subtitle_filter:
                cmd.extend(["-vf", subtitle_filter])
                cmd.extend(["-c:v", "libx264", "-crf", "23", "-preset", "fast"])
                LOGGER.info(f"Added hardsub intro subtitle filter")
        except Exception as e:
            LOGGER.error(f"Error adding hardsub filter: {e}")
            cmd.extend(["-c:v", "copy"])
    else:
        cmd.extend(["-c:v", "copy"])
    
    cmd.extend([
        "-c:a",
        "copy",
        "-c:s",
        "copy",
        outfile,
        "-y",
    ])

    listener.suproc = await create_subprocess_exec(*cmd, stderr=PIPE)
    code = await listener.suproc.wait()

    if code == 0:
        listener.seed = False
        await clean_target(media_file)
        # Clean up SRT file if created
        if srt_file and await aiopath.exists(srt_file):
            await aioremove(srt_file)
        await move(outfile, base_dir)
    else:
        await clean_target(outfile)
        # Clean up SRT file on error
        if srt_file and await aiopath.exists(srt_file):
            await aioremove(srt_file)
        LOGGER.error(
            "%s. Changing metadata failed, Path %s",
            (await listener.suproc.stderr.read()).decode(),
            media_file,
        )
