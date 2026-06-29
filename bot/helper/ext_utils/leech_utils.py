
from hashlib import md5
from time import strftime, gmtime, time
from re import sub as re_sub, search as re_search
import re

from shlex import split as ssplit
from natsort import natsorted
from os import path as ospath
from aiofiles.os import remove as aioremove, path as aiopath, mkdir, makedirs, listdir
from aioshutil import rmtree as aiormtree
from contextlib import suppress
from asyncio import create_subprocess_exec, create_task, gather, Semaphore
from asyncio.subprocess import PIPE
from telegraph import upload_file
from langcodes import Language
from pathlib import Path
from bot import LOGGER, MAX_SPLIT_SIZE, config_dict, user_data
from bot.modules.mediainfo import parseinfo
from bot.helper.ext_utils.bot_utils import (
    cmd_exec,
    sync_to_async,
    get_readable_file_size,
    get_readable_time,
)
from bot.helper.ext_utils.fs_utils import ARCH_EXT, get_mime_type
from bot.helper.ext_utils.telegraph_helper import telegraph
import re

async def extract_metadata_from_filename(filename, filepath=None):
    metadata = {
        'title': 'Unknown',
        'season': '1',
        'episode': '01',
        'quality': '1080p',
        'chapter': '001'
    }

    # List of known uploader/group tags to remove
    uploader_tags = [
        'Toonworld4all', 'SubsPlease', 'EMBER', 'Erai-raws',
        'HorribleSubs', 'AnimeRG', 'Judas', 'ASW', 'Anime Time',
        'Virtuality', 'SmallSizedAnime', 'DKB', 'Cleo', 'Reaktor',
        'Commie', 'GJM', 'Underwater', 'FFF', 'Doki', 'gg', 'Chihiro',
        'Coalgirls', 'UTW', 'Mazui', 'Hadena', 'Horrible', 'Mezashite',
        'Asenshi', 'Vivid', 'Soldado', 'Anime4Life', 'Ohys-Raws',
        'CR', 'NanDesuKa', 'Plex', 'Anime-Koi', 'AnimeKaizoku',
        'ReinForce', 'BlurayDesuYo', 'Beatrice-Raws', 'SCY', 'Nep_Blanc',
        'Anime-Supreme', 'HiSub', 'NC-Raws', 'nekomoe kissaten',
        # Add more uploader tags as you encounter them
    ]

    # Remove only specific uploader tags from the beginning
    pattern = r'^\[(?:' + '|'.join(re.escape(tag) for tag in uploader_tags) + r')\]\s*'
    clean_filename = re.sub(pattern, '', filename, flags=re.IGNORECASE)
    clean_filename = clean_filename.strip()

    # Title patterns
    title_patterns = [
        # Bracketed episode prefix: "[E392] Naruto Shippuden [1080p] ..." -> "Naruto Shippuden"
        r'^\[[Ee]p?(?:isode)?[\s\.\-]*0*\d+\][\s\.\-]*(.+?)[\s\.\-]*(?:\[|@|$)',
        r'^(.+?)[\s\.\-]*[Ss]0*(\d+)[\s\.\-]*[Ee]0*(\d+)',
        r'^(.+?)[\s\.\-]*[Ss]eason[\s\.\-]*0*(\d+)[\s\.\-]*[Ee]pisode[\s\.\-]*0*(\d+)',
        r'^\[CH[-\s]?\d+\][\s\.\-]*(.+?)[\s\.\-]*-',
        r'^\[\d+\][\s\.\-]*(.+?)[\s\.\-]*(?:@|$)',
        r'^(.+?)[\s\.\-]*(?:Ch(?:apter)?|#)[\s\.\-]*\d+',
        r'^(.+?)[\s\.\-]*\[',
        r'^0*(\d{1,4})[\s\.\-_]+(.+?)(?:[\s\.\-_]+|@|$)',
    ]

    title_found = False
    episode_found = False

    for pattern in title_patterns:
        title_match = re.search(pattern, clean_filename, re.IGNORECASE)
        if title_match:
            if len(title_match.groups()) >= 3:
                title = title_match.group(1).replace('.', ' ').replace('-', ' ').strip()
                metadata['season'] = title_match.group(2)
                ep_num = int(title_match.group(3))
                metadata['episode'] = str(ep_num).zfill(4 if ep_num >= 1000 else 3 if ep_num >= 100 else 2)
                episode_found = True
            elif len(title_match.groups()) == 2 and pattern == r'^0*(\d{1,4})[\s\.\-_]+(.+?)(?:[\s\.\-_]+|@|$)':
                ep_num = int(title_match.group(1))
                if 1 <= ep_num <= 9999 and ep_num < 1920:
                    metadata['episode'] = str(ep_num).zfill(4 if ep_num >= 1000 else 3 if ep_num >= 100 else 2)
                    episode_found = True
                title = title_match.group(2).replace('.', ' ').replace('-', ' ').replace('_', ' ').strip()
            else:
                title = title_match.group(1).replace('.', ' ').replace('-', ' ').strip()
            title = re.sub(r'\s*[\(\[]?\s*(199[0-9]|20[0-2][0-9]|2030)\s*[\)\]]?\s*', ' ', title).strip()
            metadata['title'] = title
            title_found = True
            break

    if not title_found and clean_filename:
        base_title = re.split(r'[\.\-\s]+(?:199[0-9]|20[0-2][0-9]|2030)|[\.\-\s]+\d{3,4}p', clean_filename)[0]
        if base_title:
            base_title = base_title.replace('.', ' ').replace('-', ' ').strip()
            base_title = re.sub(r'\s*[\(\[]?\s*(199[0-9]|20[0-2][0-9]|2030)\s*[\)\]]?\s*', ' ', base_title).strip()
            metadata['title'] = base_title

    # Season detection
    season_match = re.search(r'[Ss](?:eason[\s\.\-]*)?0*(\d+)', filename)
    if season_match:
        metadata['season'] = season_match.group(1)

    # ENHANCED EPISODE DETECTION
    if not episode_found:
        # ── Pre-clean: strip hex hashes like [BE8EB16E] to prevent false E+digit matches ──
        filename_for_ep = re.sub(r'\[[0-9A-Fa-f]{6,8}\]', '', filename).strip()

        # ── Also strip known non-episode bracketed tags ──
        filename_for_ep = re.sub(
            r'\[(?:'
            r'(?:1080|720|480|360|2160|4320)[pP]|'  # resolution: [1080p]
            r'(?:BD|BluRay|Blu-Ray|BDRip|BDRemux)|'  # source
            r'(?:WEB|WEBRip|WEB-DL|WEBDL|HDTV|DVDRip|DVD)|'
            r'(?:HEVC|H\.?264|H\.?265|x264|x265|AVC|XVID|DIVX)|'  # codec
            r'(?:AAC|AC3|DTS|FLAC|MP3|OPUS|TRUEHD|ATMOS)|'         # audio
            r'(?:HDR|HDR10|SDR|DV|DoVi)|'                          # color
            r'(?:10bit|8bit|Hi10P)|'                                # bit depth
            r'(?:Dual|Multi|Sub|Dub|Eng|Jpn|Hindi|Tamil|Tel)'       # lang
            r')\]',
            '', filename_for_ep, flags=re.IGNORECASE
        ).strip()

        episode_patterns = [
            # ── HIGHEST PRIORITY: Versioned episode formats ──
            # "- 02v2", "- 13v3", "- 1001v2" — the vN suffix was blocking old lookahead
            r'[\s\.\-]+-[\s\.\-]*0*(\d{1,4})v\d+(?=[\s\.\-\[]|\.(?:mkv|mp4|avi|mov|wmv)|$)',

            # ── Bracketed E-prefixed episode: [E392], [Ep392], [Episode 392] ──
            r'\[[Ee]p?(?:isode)?[\s\.\-]*0*(\d{1,4})\]',

            # ── Standard S/E formats ──
            r'[Ss]0*(\d+)[Ee]0*(\d+)',              # S01E01  (capture group 2 = ep)
            r'[Ee]p(?:isode)?[\s\.\-]*0*(\d{1,4})', # Episode 01, Ep01, ep-1001
            r'[Ee][\s\.\-]*0*(\d{1,4})(?=[\s\.\-\[]|\.(?:mkv|mp4|avi)|$)',  # E01, E 01

            # ── Episode number at the very beginning (e.g. "99 Slam Dunk") ──
            r'^0*(\d{1,4})[\s\.\-_]+(?![xX]\d)',

            # ── Common anime dash separator ──
            # "Title - 45", "Title - 1001" with optional vN suffix in lookahead
            r'[\s\.\-]+-[\s\.\-]*0*(\d{1,4})(?=v\d+|[\s\.\-]|\.(?:mkv|mp4|avi|mov)|$)',

            # ── Anime-style bracketed episode ──
            r'[\s\.\-]+0*(\d{1,4})[\s\.\-]+\[',     # " 01 [", " 1001 ["
            r'[\s\.\-]+-[\s\.\-]+0*(\d{1,4})[\s\.\-]+\[',  # " - 01 ["

            # ── Episode before quality tag ──
            r'[\s\.\-]+0*(\d{1,4})[\s\.\-]+\d{3,4}[pP]',   # " 01 1080p"
            r'[\s\.\-]+0*(\d{1,4})[\s\.\-]*\[(?!CH)',        # " 01[" but not [CH

            # ── Bracketed episode number ──
            r'\[0*(\d{1,4})\](?!\s*[pP])',            # [01], [1001] but not [1080p]
            r'\(0*(\d{1,4})\)(?!\s*[pP])',            # (01), (1001)

            # ── Before version/source/special tags ──
            r'[\s\._\-]0*(\d{1,4})(?=[\s\._\-](?:END|Final|Fin|v\d|BD|WEB|BluRay|HEVC|x264|x265))',

            # ── Japanese/Chinese format ──
            r'第\s*0*(\d{1,4})\s*[話话回集]',          # 第01話, 第1001話
            r'第\s*0*(\d{1,4})\s*(?:期|季)',           # season kanji (use for season if needed)

            # ── With surrounding IDs/hashes ──
            r'[\s\.\-]+0*(\d{1,4})[\s\.\-]+\[\d{5,}\]',  # " 45 [4681281]"

            # ── Hyphen/underscore separated ──
            r'(?<![A-Za-z0-9])-[\s]*0*(\d{1,4})(?=[\s\.\-\[]|v\d+|$)',  # "- 01", "-1001"
            r'(?<![A-Za-z0-9])_0*(\d{1,4})(?=[\s\._\-]|$)',              # "_01", "_1001"

            # ── x / tilde / hash / ordinal formats ──
            r'[\s\.\-]x0*(\d{1,4})(?=[\s\.\-]|$)',             # " x01"
            r'[\s\.\-]~[\s]*0*(\d{1,4})(?=[\s\.\-]|$)',        # " ~ 01"
            r'#0*(\d{1,4})(?=[\s\.\-]|$)',                      # "#01", "#1001"
            r'[\s\.\-]0*(\d{1,4})(?:st|nd|rd|th)[\s\.\-]',     # 1st, 2nd …

            # ── Part/Vol/Book formats ──
            r'[Pp]art[\s\.\-]*0*(\d{1,4})(?=[\s\.\-]|$)',      # Part 01
            r'[Vv]ol(?:ume)?[\s\.\-]*0*(\d{1,4})(?=[\s\.\-]|$)',  # Vol 01
            r'[Bb]ook[\s\.\-]*0*(\d{1,4})(?=[\s\.\-]|$)',      # Book 01

            # ── Roman numerals (I to L = 1 to 50) ──
            r'[\s\.\-]+(X{0,3}(?:IX|IV|V?I{0,3})|L(?:X{0,3})(?:IX|IV|V?I{0,3})?)(?=[\s\.\-]|$)',
        ]

        roman_to_int = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
            'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
            'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15,
            'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20,
            'XXI': 21, 'XXII': 22, 'XXIII': 23, 'XXIV': 24, 'XXV': 25,
            'XXVI': 26, 'XXVII': 27, 'XXVIII': 28, 'XXIX': 29, 'XXX': 30,
            'XXXI': 31, 'XXXII': 32, 'XXXIII': 33, 'XXXIV': 34, 'XXXV': 35,
            'XXXVI': 36, 'XXXVII': 37, 'XXXVIII': 38, 'XXXIX': 39, 'XL': 40,
            'XLI': 41, 'XLII': 42, 'XLIII': 43, 'XLIV': 44, 'XLV': 45,
            'XLVI': 46, 'XLVII': 47, 'XLVIII': 48, 'XLIX': 49, 'L': 50
        }

        for pattern in episode_patterns:
            episode_match = re.search(pattern, filename_for_ep, re.IGNORECASE)
            if episode_match:
                # S01E01 pattern has 2 groups; use group 2 for episode
                if episode_match.lastindex and episode_match.lastindex >= 2:
                    ep_value = episode_match.group(2).upper()
                else:
                    ep_value = episode_match.group(1).upper()

                # Roman numeral check
                if ep_value in roman_to_int:
                    metadata['episode'] = str(roman_to_int[ep_value]).zfill(2)
                    episode_found = True
                    break

                try:
                    ep_num = int(ep_value)

                    # Beginning-of-filename pattern: reject years & resolutions
                    if pattern == r'^0*(\d{1,4})[\s\.\-_]+(?![xX]\d)':
                        if ep_num >= 1920 or ep_num == 0:
                            continue

                    if 1 <= ep_num <= 9999:
                        # For 1000+ episodes require explicit context
                        if ep_num > 999:
                            context_check = re.search(
                                rf'(?:episode|ep|e|第|-)\s*0*{ep_num}',
                                filename_for_ep,
                                re.IGNORECASE
                            )
                            if not context_check:
                                continue

                        metadata['episode'] = str(ep_num).zfill(
                            4 if ep_num >= 1000 else 3 if ep_num >= 100 else 2
                        )
                        episode_found = True
                        break
                except ValueError:
                    continue

        # Fallback: any standalone 1-4 digit number after stripping noise
        if not episode_found:
            title_part = re.split(r'[\.\-\s]+\d{3,4}[pP]', filename_for_ep)[0]
            title_part = re.sub(r'\[.*?\]|\(.*?\)', '', title_part).strip()
            fallback_match = re.search(
                r'[\s\.\-]+0*(\d{1,4})(?=[\s\.\-]|v\d+|$)', title_part
            )
            if fallback_match:
                ep_num = int(fallback_match.group(1))
                if 1 <= ep_num <= 9999 and ep_num < 1920:
                    metadata['episode'] = str(ep_num).zfill(
                        4 if ep_num >= 1000 else 3 if ep_num >= 100 else 2
                    )

    # Quality detection
    quality_match = re.search(r'(\d{3,4}[pP]|4K|2160[pP])', filename, re.IGNORECASE)
    if quality_match:
        metadata['quality'] = quality_match.group(1)
    elif filepath and await aiopath.exists(filepath):
        file_size = await aiopath.getsize(filepath)
        if file_size > 500 * 1024 * 1024:
            metadata['quality'] = 'HDRip'

    # Chapter patterns
    chapter_patterns = [
        r'\[CH[-\s]?(\d+)\]',
        r'\[(?:CH|Ch|ch)[-\s]?(\d+)\]',
        r'\[(\d{2,4})\]',
        r'Ch(?:apter)?[-_\s]?(\d+)',
        r'\b[Cc][-\s]?(\d+)\b',
        r'#(\d+)',
        r'\bEp(?:isode)?[-_\s]?(\d+)\b',
        r'\bVol(?:ume)?[-_\s]?(\d+)\b',
        r'\bPart[-_\s]?(\d+)\b',
        r'\b第\s?(\d+)\s?[話话]\b',
        r'\bChap[-_\s]?(\d+)\b',
        r'\bBook[-_\s]?(\d+)\b',
        r'\bE(\d{2,4})\b',
        r'\bS\d+E(\d+)\b',
        r'\[(?:C|c)(\d+)\]',
        r'\b\d{1,4}(?=\s?(?:END|Final|Fin)\b)',
    ]

    for pattern in chapter_patterns:
        chapter_match = re.search(pattern, filename, re.IGNORECASE)
        if chapter_match:
            metadata['chapter'] = chapter_match.group(1).zfill(3)
            break

    return metadata
    
async def apply_template_rename(filename, template, filepath=None):
    if not template or '{' not in template:
        return filename
    metadata = await extract_metadata_from_filename(filename, filepath)
    
    # Handle math offsets in episode/season tags like {episode:+12} or {episode:-3}
    # Supports both episode and season tags with +/- arithmetic
    def _apply_math_offset(tmpl, meta):
        """Replace {tag:+N} / {tag:-N} patterns with the computed value."""
        def replacer(m):
            tag = m.group(1)       # e.g. "episode" or "season"
            sign = m.group(2)      # "+" or "-"
            offset = int(m.group(3))  # the numeric offset
            
            raw = meta.get(tag, "")
            if not raw:
                return m.group(0)  # keep original if tag not in metadata
            
            try:
                original_num = int(raw)
                pad_width = len(raw)  # preserve original zero-padding width
                
                offset_val = offset if sign == "+" else -offset
                result = original_num + offset_val
                
                # Safety: if result is non-positive, fall back to original value
                if result <= 0:
                    result = original_num
                
                # Apply smart padding matching original width or auto-pad rules
                new_str = str(result).zfill(pad_width)
                
                # Replace the matched pattern with plain {tag} and update metadata
                meta[tag] = new_str
                return f"{{{tag}}}"
            except ValueError:
                return m.group(0)  # keep original on error
        
        # Pattern matches {episode:+12}, {episode:-3}, {season:+2}, etc.
        patched = re.sub(r'\{(episode|season):([+\-])(\d+)\}', replacer, tmpl)
        return patched
    
    template = _apply_math_offset(template, metadata)

    
    try:
        renamed = template.format(**metadata)
        original_ext = Path(filename).suffix
        if not renamed.endswith(original_ext):
            renamed += original_ext
        return renamed
    except (KeyError, ValueError):
        return filename
        
async def is_multi_streams(path):
    try:
        result = await cmd_exec([
            "ffprobe",
            "-hide_banner",
            "-loglevel",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            path,
        ])
        if res := result[1]:
            LOGGER.warning(f"Get Video Streams: {res}")
    except Exception as e:
        LOGGER.error(f"Get Video Streams: {e}. Mostly File not found!")
        return False
    fields = eval(result[0]).get("streams")
    if fields is None:
        LOGGER.error(f"get_video_streams: {result}")
        return False
    videos = 0
    audios = 0
    for stream in fields:
        if stream.get("codec_type") == "video":
            videos += 1
        elif stream.get("codec_type") == "audio":
            audios += 1
    return videos > 1 or audios > 1

async def get_media_info(path, metadata=False):
    try:
        result = await cmd_exec([
            "ffprobe",
            "-hide_banner",
            "-loglevel",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            path,
        ])
        if res := result[1]:
            LOGGER.warning(f"Media Info FF: {res}")
    except Exception as e:
        LOGGER.error(f"Media Info: {e}. Mostly File not found!")
        return (0, "", "", "") if metadata else (0, None, None)
    ffresult = eval(result[0])
    fields = ffresult.get("format")
    if fields is None:
        LOGGER.error(f"Media Info Sections: {result}")
        return (0, "", "", "") if metadata else (0, None, None)
    duration = round(float(fields.get("duration", 0)))
    if metadata:
        lang, qual, stitles = "", "", ""
        if (streams := ffresult.get("streams")) and streams[0].get("codec_type") == "video":
            qual = int(streams[0].get("height"))
            qual = f"{480 if qual <= 480 else 540 if qual <= 540 else 720 if qual <= 720 else 1080 if qual <= 1080 else 2160 if qual <= 2160 else 4320 if qual <= 4320 else 8640}p"
        for stream in streams:
            if stream.get("codec_type") == "audio" and (
                lc := stream.get("tags", {}).get("language")
            ):
                with suppress(Exception):
                    lc = Language.get(lc).display_name()
                if lc not in lang:
                    lang += f"{lc}, "
            if stream.get("codec_type") == "subtitle" and (
                st := stream.get("tags", {}).get("language")
            ):
                with suppress(Exception):
                    st = Language.get(st).display_name()
                if st not in stitles:
                    stitles += f"{st}, "
        return duration, qual, lang[:-2], stitles[:-2]
    tags = fields.get("tags", {})
    artist = tags.get("artist") or tags.get("ARTIST") or tags.get("Artist")
    title = tags.get("title") or tags.get("TITLE") or tags.get("Title")
    return duration, artist, title

async def get_document_type(path):
    is_video, is_audio, is_image = False, False, False
    if path.endswith((".aria2", ".!qB")):
        return is_video, is_audio, is_image
    if path.endswith(tuple(ARCH_EXT)) or re_search(
        r".+(\.|_)(rar|7z|zip|bin)(\.0*\d+)?$", path
    ):
        return is_video, is_audio, is_image
    mime_type = await sync_to_async(get_mime_type, path)
    if mime_type.startswith("audio"):
        return False, True, False
    if mime_type.startswith("image"):
        return False, False, True
    if not mime_type.startswith("video") and not mime_type.endswith("octet-stream"):
        return is_video, is_audio, is_image
    try:
        result = await cmd_exec([
            "ffprobe",
            "-hide_banner",
            "-loglevel",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            path,
        ])
        if res := result[1]:
            LOGGER.warning(f"Get Document Type: {res}")
    except Exception as e:
        LOGGER.error(f"Get Document Type: {e}. Mostly File not found!")
        return is_video, is_audio, is_image
    fields = eval(result[0]).get("streams")
    if fields is None:
        LOGGER.error(f"get_document_type: {result}")
        return is_video, is_audio, is_image
    for stream in fields:
        if stream.get("codec_type") == "video":
            is_video = True
        elif stream.get("codec_type") == "audio":
            is_audio = True
    return is_video, is_audio, is_image

async def get_audio_thumb(audio_file):
    des_dir = "Thumbnails"
    if not await aiopath.exists(des_dir):
        await mkdir(des_dir)
    des_dir = ospath.join(des_dir, f"{time()}.jpg")
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        audio_file,
        "-an",
        "-vcodec",
        "copy",
        des_dir,
    ]
    status = await create_subprocess_exec(*cmd, stderr=PIPE)
    if await status.wait() != 0 or not await aiopath.exists(des_dir):
        err = (await status.stderr.read()).decode().strip()
        LOGGER.error(
            f"Error while extracting thumbnail from audio. Name: {audio_file} stderr: {err}"
        )
        return None
    return des_dir

async def take_ss(video_file, duration=None, total=1, gen_ss=False):
    des_dir = ospath.join("Thumbnails", f"{time()}")
    await makedirs(des_dir, exist_ok=True)
    if duration is None:
        duration = (await get_media_info(video_file))[0]
    if duration == 0:
        duration = 3
    duration = duration - (duration * 2 / 100)
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        "",
        "-i",
        video_file,
        "-vf",
        "thumbnail",
        "-frames:v",
        "1",
        des_dir,
    ]
    tstamps = {}
    thumb_sem = Semaphore(3)

    async def extract_ss(eq_thumb):
        async with thumb_sem:
            cmd[5] = str((duration // total) * eq_thumb)
            tstamps[f"wz_thumb_{eq_thumb}.jpg"] = strftime(
                "%H:%M:%S", gmtime(float(cmd[5]))
            )
            cmd[-1] = ospath.join(des_dir, f"wz_thumb_{eq_thumb}.jpg")
            task = await create_subprocess_exec(*cmd, stderr=PIPE)
            return (task, await task.wait(), eq_thumb)

    tasks = [extract_ss(eq_thumb) for eq_thumb in range(1, total + 1)]
    status = await gather(*tasks)
    for task, rtype, eq_thumb in status:
        if rtype != 0 or not await aiopath.exists(
            ospath.join(des_dir, f"wz_thumb_{eq_thumb}.jpg")
        ):
            err = (await task.stderr.read()).decode().strip()
            LOGGER.error(
                f"Error while extracting thumbnail no. {eq_thumb} from video. Name: {video_file} stderr: {err}"
            )
            await aiormtree(des_dir)
            return None
    return (des_dir, tstamps) if gen_ss else ospath.join(des_dir, "wz_thumb_1.jpg")

async def split_file(
    path,
    size,
    file_,
    dirpath,
    split_size,
    listener,
    start_time=0,
    i=1,
    inLoop=False,
    multi_streams=True,
):
    if (
        listener.suproc == "cancelled"
        or listener.suproc is not None
        and listener.suproc.returncode == -9
    ):
        return False
    if listener.seed and not listener.newDir:
        dirpath = f"{dirpath}/splited_files_mltb"
    if not await aiopath.exists(dirpath):
        await mkdir(dirpath)
    user_id = listener.message.from_user.id
    user_dict = user_data.get(user_id, {})
    leech_split_size = user_dict.get("split_size") or config_dict["LEECH_SPLIT_SIZE"]
    parts = -(-size // leech_split_size)
    if (
        user_dict.get("equal_splits")
        or config_dict["EQUAL_SPLITS"]
        and "equal_splits" not in user_dict
    ) and not inLoop:
        split_size = ((size + parts - 1) // parts) + 1000
    if (await get_document_type(path))[0]:
        if multi_streams:
            multi_streams = await is_multi_streams(path)
        duration = (await get_media_info(path))[0]
        base_name, extension = ospath.splitext(file_)
        split_size -= 5000000
        while i <= parts or start_time < duration - 4:
            parted_name = f"{base_name}.part{i:03}{extension}"
            out_path = ospath.join(dirpath, parted_name)
            cmd = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                str(start_time),
                "-i",
                path,
                "-fs",
                str(split_size),
                "-map",
                "0",
                "-map_chapters",
                "-1",
                "-async",
                "1",
                "-strict",
                "-2",
                "-c",
                "copy",
                out_path,
            ]
            if not multi_streams:
                del cmd[10]
                del cmd[10]
            if (
                listener.suproc == "cancelled"
                or listener.suproc is not None
                and listener.suproc.returncode == -9
            ):
                return False
            listener.suproc = await create_subprocess_exec(*cmd, stderr=PIPE)
            code = await listener.suproc.wait()
            if code == -9:
                return False
            elif code != 0:
                err = (await listener.suproc.stderr.read()).decode().strip()
                try:
                    await aioremove(out_path)
                except Exception:
                    pass
                if multi_streams:
                    LOGGER.warning(
                        f"{err}. Retrying without map, -map 0 not working in all situations. Path: {path}"
                    )
                    return await split_file(
                        path,
                        size,
                        file_,
                        dirpath,
                        split_size,
                        listener,
                        start_time,
                        i,
                        True,
                        False,
                    )
                else:
                    LOGGER.warning(
                        f"{err}. Unable to split this video, if it's size less than {MAX_SPLIT_SIZE} will be uploaded as it is. Path: {path}"
                    )
                    return "errored"
            out_size = await aiopath.getsize(out_path)
            if out_size > MAX_SPLIT_SIZE:
                dif = out_size - MAX_SPLIT_SIZE
                split_size -= dif + 5000000
                await aioremove(out_path)
                return await split_file(
                    path,
                    size,
                    file_,
                    dirpath,
                    split_size,
                    listener,
                    start_time,
                    i,
                    True,
                )
            lpd = (await get_media_info(out_path))[0]
            if lpd == 0:
                LOGGER.error(
                    f"Something went wrong while splitting, mostly file is corrupted. Path: {path}"
                )
                break
            elif duration == lpd:
                LOGGER.warning(
                    f"This file has been splitted with default stream and audio, so you will only see one part with less size from orginal one because it doesn't have all streams and audios. This happens mostly with MKV videos. Path: {path}"
                )
                break
            elif lpd <= 3:
                await aioremove(out_path)
                break
            start_time += lpd - 3
            i += 1
    else:
        out_path = ospath.join(dirpath, f"{file_}.")
        listener.suproc = await create_subprocess_exec(
            "split",
            "--numeric-suffixes=1",
            "--suffix-length=3",
            f"--bytes={split_size}",
            path,
            out_path,
            stderr=PIPE,
        )
        code = await listener.suproc.wait()
        if code == -9:
            return False
        elif code != 0:
            err = (await listener.suproc.stderr.read()).decode().strip()
            LOGGER.error(err)
    return True

def get_md5_hash(file_path):
    hash_md5 = md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

async def format_filename(file_, user_id, dirpath=None, isMirror=False, custom_name=False):
    """
    Format filename with prefix, suffix, and optionally apply remname (template/regex).
    
    Args:
        file_: The filename to format
        user_id: User ID for getting user-specific settings
        dirpath: Directory path for template metadata extraction
        isMirror: True if this is a mirror operation (uses mremname instead of lremname)
        custom_name: If string, use as exact filename (from -n flag); if False, apply normal formatting
    
    Returns:
        Tuple of (formatted_filename, caption)
    """
    user_dict = user_data.get(user_id, {})
    
    LOGGER.info(f"[FORMAT_FILENAME] Called with: file_={file_}, custom_name={custom_name}")
    
    # If custom_name is a string (user provided -n with value), use it as exact filename
    if custom_name:
        # Extract extension from original file
        ext = ospath.splitext(file_)[1]
        # If custom_name already has extension, use as-is; otherwise add original extension
        if not ospath.splitext(custom_name)[1]:
            custom_name = f"{custom_name}{ext}"
        LOGGER.info(f"[FORMAT_FILENAME] Using custom name: {custom_name}")
        
        # Get caption template
        lcaption = (
            config_dict["LEECH_FILENAME_CAPTION"]
            if (val := user_dict.get("lcaption", "")) == ""
            else val
        )
        
        # Format caption with custom filename if template exists
        cap_mono = (
            f"<{config_dict['CAP_FONT']}>{custom_name}</{config_dict['CAP_FONT']}>"
            if config_dict["CAP_FONT"]
            else custom_name
        )
        
        if lcaption and dirpath and not isMirror:
            def lowerVars(match):
                return f"{{{match.group(1).lower()}}}"
            
            lcaption = (
                lcaption.replace("\\|", "%%")
                .replace("\\{", "&%&")
                .replace("\\}", "$%$")
                .replace("\\s", " ")
            )
            slit = lcaption.split("|")
            slit[0] = re_sub(r"\\{([^}]+)\\}", lowerVars, slit[0])
            up_path = ospath.join(dirpath, file_)  # Use original file for media info
            dur, qual, lang, subs = await get_media_info(up_path, True)
            cap_mono = slit[0].format(
                filename=custom_name,  # Use custom name in caption
                size=get_readable_file_size(await aiopath.getsize(up_path)),
                duration=get_readable_time(dur),
                quality=qual,
                languages=lang,
                subtitles=subs,
            )
            if len(slit) > 1:
                for rep in range(1, len(slit)):
                    args = slit[rep].split(":")
                    if len(args) == 3:
                        cap_mono = cap_mono.replace(args[0], args[1], int(args[2]))
                    elif len(args) == 2:
                        cap_mono = cap_mono.replace(args[0], args[1])
                    elif len(args) == 1:
                        cap_mono = cap_mono.replace(args[0], "")
            cap_mono = cap_mono.replace("%%", "|").replace("&%&", "{").replace("$%$", "}")
        
        return custom_name, cap_mono
    
    ftag, ctag = ("m", "MIRROR") if isMirror else ("l", "LEECH")
    prefix = (
        config_dict[f"{ctag}_FILENAME_PREFIX"]
        if (val := user_dict.get(f"{ftag}prefix", "")) == ""
        else val
    )
    
    # If custom_name is True (user provided -n), skip all remname logic
    if custom_name:
        remname = ""
    elif isMirror:
        # For mirror, use old remname field
        remname = (
            config_dict[f"{ctag}_FILENAME_REMNAME"]
            if (val := user_dict.get(f"{ftag}remname", "")) == ""
            else val
        )
    else:
        # Get both rename methods for leech
        remname_auto = (
            config_dict.get("LEECH_FILENAME_REMNAME_AUTO", "")
            if (val := user_dict.get("lremname_auto", "")) == ""
            else val
        )
        
        remname_regex = (
            config_dict.get("LEECH_FILENAME_REMNAME_REGEX", "")
            if (val := user_dict.get("lremname_regex", "")) == ""
            else val
        )
        
        # Determine which method to use
        rename_method = user_dict.get("rename_method", "auto")
        autorename_enabled = user_dict.get("autorename", True)
        
        if not autorename_enabled:
            remname = ""
        elif rename_method == "auto" and remname_auto:
            remname = remname_auto
        elif rename_method == "regex" and remname_regex:
            remname = remname_regex
        else:
            # Fallback: if only one exists, use it
            remname = remname_auto if remname_auto else remname_regex
    
    suffix = (
        config_dict[f"{ctag}_FILENAME_SUFFIX"]
        if (val := user_dict.get(f"{ftag}suffix", "")) == ""
        else val
    )
    lcaption = (
        config_dict["LEECH_FILENAME_CAPTION"]
        if (val := user_dict.get("lcaption", "")) == ""
        else val
    )
    prefile_ = file_
    file_ = re_sub(r"www\S+", "", file_)
    
    # Apply remname if it exists
    if remname:
        if "{" in remname and "}" in remname:
            filepath = ospath.join(dirpath, prefile_) if dirpath else None
            file_ = await apply_template_rename(file_, remname, filepath)
            LOGGER.info(f"Template Rename: {file_}")
        else:
            if not remname.startswith("|"):
                remname = f"|{remname}"
            remname = remname.replace("\\s", " ")
            slit = remname.split("|")
            __newFileName = ospath.splitext(file_)[0]
            for rep in range(1, len(slit)):
                args = slit[rep].split(":")
                if len(args) == 3:
                    __newFileName = re_sub(
                        args[0], args[1], __newFileName, int(args[2])
                    )
                elif len(args) == 2:
                    __newFileName = re_sub(args[0], args[1], __newFileName)
                elif len(args) == 1:
                    __newFileName = re_sub(args[0], "", __newFileName)
            file_ = __newFileName + ospath.splitext(file_)[1]
            LOGGER.info(f"Old Remname: {file_}")
            for rep in range(1, len(slit)):
                args = slit[rep].split(":")
                if len(args) == 3:
                    __newFileName = re_sub(
                        args[0], args[1], __newFileName, int(args[2])
                    )
                elif len(args) == 2:
                    __newFileName = re_sub(args[0], args[1], __newFileName)
                elif len(args) == 1:
                    __newFileName = re_sub(args[0], "", __newFileName)
            file_ = __newFileName + ospath.splitext(file_)[1]
            LOGGER.info(f"New Remname : {file_}")
    nfile_ = file_
    if prefix:
        nfile_ = prefix.replace("\\s", " ") + file_
        prefix = re_sub(r"<.*?>", "", prefix).replace("\\s", " ")
        if not file_.startswith(prefix):
            file_ = f"{prefix}{file_}"
    if suffix and not isMirror:
        suffix = suffix.replace("\\s", " ")
        sufLen = len(suffix)
        fileDict = file_.split(".")
        _extIn = 1 + len(fileDict[-1])
        _extOutName = ".".join(fileDict[:-1]).replace(".", " ").replace("-", " ")
        _newExtFileName = f"{_extOutName}{suffix}.{fileDict[-1]}"
        if len(_extOutName) > (64 - (sufLen + _extIn)):
            _newExtFileName = (
                _extOutName[: 64 - (sufLen + _extIn)] + f"{suffix}.{fileDict[-1]}"
            )
        file_ = _newExtFileName
    elif suffix:
        suffix = suffix.replace("\\s", " ")
        file_ = (
            f"{ospath.splitext(file_)[0]}{suffix}{ospath.splitext(file_)[1]}"
            if "." in file_
            else f"{file_}{suffix}"
        )
    cap_mono = (
        f"<{config_dict['CAP_FONT']}>{nfile_}</{config_dict['CAP_FONT']}>"
        if config_dict["CAP_FONT"]
        else nfile_
    )
    if lcaption and dirpath and not isMirror:

        def lowerVars(match):
            return f"{{{match.group(1).lower()}}}"

        lcaption = (
            lcaption.replace("\\|", "%%")
            .replace("\\{", "&%&")
            .replace("\\}", "$%$")
            .replace("\\s", " ")
        )
        slit = lcaption.split("|")
        slit[0] = re_sub(r"\\{([^}]+)\\}", lowerVars, slit[0])
        up_path = ospath.join(dirpath, prefile_)
        dur, qual, lang, subs = await get_media_info(up_path, True)
        cap_mono = slit[0].format(
            filename=nfile_,
            size=get_readable_file_size(await aiopath.getsize(up_path)),
            duration=get_readable_time(dur),
            quality=qual,
            languages=lang,
            subtitles=subs,
            md5_hash=get_md5_hash(up_path),
        )
        if len(slit) > 1:
            for rep in range(1, len(slit)):
                args = slit[rep].split(":")
                if len(args) == 3:
                    cap_mono = cap_mono.replace(args[0], args[1], int(args[2]))
                elif len(args) == 2:
                    cap_mono = cap_mono.replace(args[0], args[1])
                elif len(args) == 1:
                    cap_mono = cap_mono.replace(args[0], "")
        cap_mono = cap_mono.replace("%%", "|").replace("&%&", "{").replace("$%$", "}")
    return file_, cap_mono

async def get_ss(up_path, ss_no):
    try:
        thumbs_path, tstamps = await take_ss(up_path, total=min(ss_no, 250), gen_ss=True)
        if not thumbs_path:
            return None
        th_html = f"📌\n"
        results = []
        for tele_id, stamp in tstamps.items():
            img_path = ospath.join(thumbs_path, tele_id)
            if await aiopath.exists(img_path):
                try:
                    img_url = upload_file(img_path)
                    results.append((img_url, stamp))
                except Exception as e:
                    LOGGER.error(f"Error uploading screenshot: {e}")
                    continue
        th_html += "".join(f'<img src="{img_url}"><br>Screenshot at {stamp}\n' for img_url, stamp in results)
        await aiormtree(thumbs_path)
        if not results:
            return None
        link_id = (await telegraph.create_page(title="ScreenShots X", content=th_html))["path"]
        return f"https://graph.org/{link_id}"
    except Exception as e:
        LOGGER.error(f"Error processing screenshots: {e}")
        return None

def get_md5_hash(file_path):
    hash_md5 = md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

async def get_mediainfo_link(up_path):
    try:
        stdout, __, _ = await cmd_exec(ssplit(f'mediainfo "{up_path}"'))
        tc = f"📌\n<pre>{stdout}</pre>"
        link_id = (await telegraph.create_page(title="MediaInfo", content=tc))["path"]
        return f"https://graph.org/{link_id}"
    except Exception as e:
        LOGGER.error(f"Error creating mediainfo link: {e}")
        return None


async def extract_streams(listener, dl_path, stream_options):
    import json
    from asyncio.subprocess import PIPE
    out_dir = f"{dl_path}_streams"
    await makedirs(out_dir, exist_ok=True)
    outputs = []

    probe = await create_subprocess_exec(
        "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", dl_path,
        stdout=PIPE, stderr=PIPE,
    )
    stdout, _ = await probe.communicate()
    all_streams = json.loads(stdout).get("streams", [])

    def get_lang(s, si):
        tags = s.get("tags", {})
        lang = tags.get("language", "").strip()
        if lang and lang.lower() not in ("und", ""):
            return lang
        return f"track_{si}"

    def unique_name(used, name):
        count = used.get(name, 0)
        used[name] = count + 1
        return name if count == 0 else f"{name}_{count + 1}"

    if "video" in stream_options:
        used = {}
        for s in all_streams:
            if s.get("codec_type") != "video":
                continue
            si = s["index"]
            fname = unique_name(used, get_lang(s, si))
            out = ospath.join(out_dir, f"{fname}.mkv")
            cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", dl_path,
                   "-map", f"0:{si}", "-c:v", "copy", out]
            proc = await create_subprocess_exec(*cmd)
            if await proc.wait() == 0:
                outputs.append(out)
            else:
                LOGGER.error(f"extract_streams: video stream {si} failed")

    if "audio" in stream_options:
        used = {}
        for s in all_streams:
            if s.get("codec_type") != "audio":
                continue
            si = s["index"]
            fname = unique_name(used, get_lang(s, si))
            codec = s.get("codec_name", "")
            ext_map = {"aac": "aac", "mp3": "mp3", "flac": "flac", "ac3": "ac3", "eac3": "eac3", "dts": "dts"}
            ext = ext_map.get(codec, "mka")
            out = ospath.join(out_dir, f"{fname}.{ext}")
            cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", dl_path,
                   "-map", f"0:{si}", "-c:a", "copy", out]
            proc = await create_subprocess_exec(*cmd)
            if await proc.wait() == 0:
                outputs.append(out)
            else:
                LOGGER.error(f"extract_streams: audio stream {si} failed")

    if "subtitle" in stream_options:
        used = {}
        for s in all_streams:
            if s.get("codec_type") != "subtitle":
                continue
            si = s["index"]
            fname = unique_name(used, get_lang(s, si))
            codec = s.get("codec_name", "")
            if codec in ("subrip", "srt", "text", "utf_8", "utf8"):
                ext, enc = "srt", "srt"
            elif codec == "webvtt":
                ext, enc = "vtt", "webvtt"
            elif codec == "mov_text":
                ext, enc = "srt", "srt"
            else:
                ext, enc = "ass", "ass"
            out = ospath.join(out_dir, f"{fname}.{ext}")
            cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", dl_path,
                   "-map", f"0:{si}", "-c:s", enc, out]
            proc = await create_subprocess_exec(*cmd)
            if await proc.wait() == 0:
                outputs.append(out)
            else:
                LOGGER.error(f"extract_streams: subtitle stream {si} failed")

    return out_dir, outputs
