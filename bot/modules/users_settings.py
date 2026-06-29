
#!/usr/bin/env python3
from datetime import datetime
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex, create, text, photo, document
from aiofiles import open as aiopen
from aiofiles.os import remove as aioremove, path as aiopath, mkdir
from langcodes import Language
from os import path as ospath, getcwd
from PIL import Image
from time import time
from functools import partial
from html import escape
from io import BytesIO
from asyncio import sleep
from cryptography.fernet import Fernet

import asyncio
from bot import (
    OWNER_ID,
    LOGGER,
    bot,
    user_data,
    config_dict,
    categories_dict,
    DATABASE_URL,
    IS_PREMIUM_USER,
    MAX_SPLIT_SIZE,
)
from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    sendCustomMsg,
    editMessage,
    deleteMessage,
    sendFile,
    chat_info,
    user_info,
)
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.bot_utils import (
    update_user_ldata,
    sync_to_async,
    new_task,
    is_url,
    is_gdrive_link,
    is_rclone_path,
    get_readable_file_size,
)
from bot.helper.ext_utils.subtitle_utils import (
    COLOR_OPTIONS,
    BG_COLOR_OPTIONS,
    validate_and_escape_subtitle_text,
)
from bot.helper.mirror_utils.upload_utils.ddlserver.gofile import Gofile
from bot.helper.themes import BotTheme
from bot.helper.ext_utils.personal_bot_manager import PersonalBotManager, verify_personal_bot, verify_personal_dump

handler_dict = {}
desp_dict = {
    "rcc": [
        "RClone is a command-line program to sync files and directories to and from different cloud storage providers like GDrive, OneDrive...",
        "Send rclone.conf. \n<b>Timeout:</b> 60 sec",
    ],
    "lprefix": [
        "Leech Filename Prefix is the Front Part attacted with the Filename of the Leech Files.",
        'Send Leech Filename Prefix. Documentation Here : <a href="https://t.me/CANON_BOTS/4">Click Me</a> \n<b>Timeout:</b> 60 sec',
    ],
    "lsuffix": [
        "Leech Filename Suffix is the End Part attached with the Filename of the Leech Files",
        'Send Leech Filename Suffix. Documentation Here : <a href="https://t.me/CANON_BOTS/4">Click Me</a> \n<b>Timeout:</b> 60 sec',
    ],
    "lremname_auto": [
        "<b><i>AutoRename Template uses tags to automatically rename files based on metadata like title, season, episode, quality</i></b>",
        '<b>Send AutoRename Template. Documentation Here :</b> <a href="https://t.me/CANON_BOTS/3">Click Me</a>\n<b>Example:</b> <code>{title} S{season}E{episode} {quality}</code> \n<b>Timeout:</b> 60 sec',
    ],
    "lremname_regex": [
        "<b><i>Regex Remname uses regex patterns to remove or manipulate filenames</i></b>",
        '<b>Send Regex Remname. Documentation Here :</b> <a href="https://t.me/CANON_BOTS/4">Click Me</a>\n<b>Example:</b> <code>|pattern:replacement|pattern2:replacement2</code> \n<b>Timeout:</b> 60 sec',
    ],
    "intro_text": [
        "<b><i>Intro Subtitle Text will appear at the start of your video</i></b>",
        '<b>Send Intro Text</b>\n<b>Example:</b> <code>Enjoy the Movie!</code>\n<b>Max Length:</b> 200 characters\n<b>Timeout:</b> 60 sec',
    ],
    "intro_duration": [
        "<b><i>Duration (in seconds) for how long the intro subtitle will display</i></b>",
        '<b>Send Duration in seconds</b>\n<b>Example:</b> <code>10</code>\n<b>Max:</b> 30 seconds\n<b>Timeout:</b> 60 sec',
    ],
    "intro_fontsize": [
        "<b><i>Font size for the intro subtitle text</i></b>",
        '<b>Send Font Size</b>\n<b>Example:</b> <code>28</code>\n<b>Range:</b> 12-72\n<b>Timeout:</b> 60 sec',
    ],
    "lcaption": [
        "Leech Caption is the Custom Caption on the Leech Files Uploaded by the bot",
        'Send Leech Caption. You can add HTML tags. Documentation Here : <a href="https://t.me/CANON_BOTS/4">Click Me</a> \n<b>Timeout:</b> 60 sec',
    ],
    "ldump": [
        "Leech Files User Dump for Personal Use as a Storage.",
        "Send Leech Dump Channel ID\n➲ <b>Format:</b> \ntitle chat_id/@username\ntitle2 chat_id2/@username2. \n\n<b>NOTE:</b>Make Bot Admin in the Channel else it will not accept\n<b>Timeout:</b> 60 sec",
    ],
    "mprefix": [
        "Mirror Filename Prefix is the Front Part attacted with the Filename of the Mirrored/Cloned Files.",
        "Send Mirror Filename Prefix. \n<b>Timeout:</b> 60 sec",
    ],
    "msuffix": [
        "Mirror Filename Suffix is the End Part attached with the Filename of the Mirrored/Cloned Files",
        "Send Mirror Filename Suffix. \n<b>Timeout:</b> 60 sec",
    ],
    "mremname": [
        "Mirror Filename Remname is combination of Regex(s) used for removing or manipulating Filename of the Mirrored/Cloned Files",
        "Send Mirror Filename Remname. \n<b>Timeout:</b> 60 sec",
    ],
    "thumb": [
        "Custom Thumbnail to appear on the Leeched files uploaded by the bot",
        "Send a photo to save it as custom thumbnail. \n<b>Alternatively: </b><code>/cmd [photo] -s thumb</code> \n<b>Timeout:</b> 60 sec",
    ],
    "yt_opt": [
        "YT-DLP Options is the Custom Quality for the extraction of videos from the yt-dlp supported sites.",
        'Send YT-DLP Options. Timeout: 60 sec\nFormat: key:value|key:value|key:value.\nExample: format:bv*+mergeall[vcodec=none]|nocheckcertificate:True\nCheck all yt-dlp api options from this <a href="https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L184">FILE</a> to convert cli arguments to api options.',
    ],
    "usess": [
        f'User Session is Telegram Session used to Download Private Contents from Private Channels with no compromise in Privacy, Build with Encryption.\n{"<b>Warning:</b> This Bot is not secured. We recommend asking the group owner to set the Upstream repo to the Official repo. If it is not the official repo, then WZML-X is not responsible for any issues that may occur in your account." if config_dict["UPSTREAM_REPO"] != "https://github.com/weebzone/WZML-X" else "Bot is Secure. You can use the session securely."}',
        "Send your Session String.\n<b>Timeout:</b> 60 sec",
    ],
    "split_size": [
        "Leech Splits Size is the size to split the Leeched File before uploading",
        f"Send Leech split size in any comfortable size, like 2Gb, 500MB or 1.46gB. \n<b>PREMIUM ACTIVE:</b> {IS_PREMIUM_USER}. \n<b>Timeout:</b> 60 sec",
    ],
    "ddl_servers": [
        "DDL Servers which uploads your File to their Specific Hosting",
        "",
    ],
    "user_tds": [
        f'UserTD helps to Upload files via Bot to your Custom Drive Destination via Global SA mail\n\n➲ <b>SA Mail :</b> {"Not Specified" if "USER_TD_SA" not in config_dict else config_dict["USER_TD_SA"]}',
        "Send User TD details for Use while Mirror/Clone\n➲ <b>Format:</b>\nname id/link index(optional)\nname2 link2/id2 index(optional)\n\n<b>NOTE:</b>\n<i>1. Drive ID must be valid, then only it will accept\n2. Names can have spaces\n3. All UserTDs are updated on every change\n4. To delete specific UserTD, give Name(s) separated by each line</i>\n\n<b>Timeout:</b> 60 sec",
    ],
    "gofile": [
        "Gofile is a free file sharing and storage platform. You can store and share your content without any limit.",
        "Send GoFile's API Key. Get it on https://gofile.io/myProfile, It will not be Accepted if the API Key is Invalid !!\n<b>Timeout:</b> 60 sec",
    ],
    "streamtape": [
        "Streamtape is free Video Streaming & sharing Hoster",
        "Send StreamTape's Login and Key\n<b>Format:</b> <code>user_login:pass_key</code>\n<b>Timeout:</b> 60 sec",
    ],
    "lmeta": [
        "Your Channel Name that will be used while editing metadata of the Video File",
        "Send Metadata Text for Leeching Files.\n<b>Timeout:</b> 60 Sec.",
    ],
    "ffmpeg_cmds": [
        "Custom FFmpeg Commands to process files before upload. Dict of list values for different profiles.",
        'Send FFmpeg Commands as JSON Dict.\n<b>Example:</b>\n<code>{"keep_japanese": ["-i mltb.video -map 0:v:0 -map 0:a:m:language:jpn -map 0:s:m:language:eng? -c copy mltb.mkv -del"]}</code>\n\n<b>Notes:</b>\n- <code>mltb.video</code> = all video files, <code>mltb.mkv</code> = output as mkv\n- <code>-del</code> = delete original after processing\n- Use <code>-ff key_name</code> in commands to execute\n<b>Timeout:</b> 60 sec',
    ],
    "pbot_token": [
        "Personal Upload Bot Token to perform uploads on behalf of you.",
        "Send your Bot Token (from @BotFather).\n<b>Timeout:</b> 60 sec"
    ],
    "pdump_chat": [
        "Personal Upload Dump Chat/Channel ID or Username.",
        "Send Channel/Chat ID (e.g., -100123456789) or public channel username (e.g., @my_channel).\n<b>Timeout:</b> 60 sec"
    ],
}
fname_dict = {
    "rcc": "RClone",
    "lprefix": "Prefix",
    "lsuffix": "Suffix",
    "lremname_auto": "AutoRename Template",
    "lremname_regex": "Regex Remname",
    "intro_text": "Intro Text",
    "intro_duration": "Intro Duration",
    "intro_fontsize": "Intro Font Size",
    "lmeta": "Metadata",
    "mprefix": "Prefix",
    "msuffix": "Suffix",
    "mremname": "Remname",
    "ldump": "User Dump",
    "lcaption": "Caption",
    "thumb": "Thumbnail",
    "yt_opt": "YT-DLP Options",
    "usess": "User Session",
    "split_size": "Leech Splits",
    "ddl_servers": "DDL Servers",
    "user_tds": "User Custom TDs",
    "gofile": "GoFile",
    "streamtape": "StreamTape",
    "ffmpeg_cmds": "FFmpeg Cmds",
    "pbot_token": "Bot Token",
    "pdump_chat": "Dump Channel",
}


async def get_user_settings(from_user, key=None, edit_type=None, edit_mode=None):
    user_id = from_user.id
    name = from_user.mention(style="html")
    buttons = ButtonMaker()
    thumbpath = f"Thumbnails/{user_id}.jpg"
    rclone_path = f"rclone/{user_id}.conf"
    user_dict = user_data.get(user_id, {})
    if key is None:
        buttons.ibutton("Universal Settings", f"userset {user_id} universal")
        buttons.ibutton("Mirror Settings", f"userset {user_id} mirror")
        buttons.ibutton("Leech Settings", f"userset {user_id} leech")
        buttons.ibutton("Personal Upload Bot", f"userset {user_id} personal_bot")
        if user_dict and any(key in user_dict for key in list(fname_dict.keys())):
            buttons.ibutton("Reset Setting", f"userset {user_id} reset_all")
        buttons.ibutton("Close", f"userset {user_id} close")

        text = BotTheme(
            "USER_SETTING",
            NAME=name,
            ID=user_id,
            USERNAME=f"@{from_user.username}",
            LANG=(
                Language.get(lc).display_name()
                if (lc := from_user.language_code)
                else "N/A"
            ),
            DC=from_user.dc_id,
        )

        button = buttons.build_menu(1)
    elif key == "universal":
        ytopt = (
            "Not Exists"
            if (val := user_dict.get("yt_opt", config_dict.get("YT_DLP_OPTIONS", "")))
            == ""
            else val
        )
        buttons.ibutton(
            f"{'✅️' if ytopt != 'Not Exists' else ''} YT-DLP Options",
            f"userset {user_id} yt_opt",
        )
        u_sess = "Exists" if user_dict.get("usess", False) else "Not Exists"
        buttons.ibutton(
            f"{'✅️' if u_sess != 'Not Exists' else ''} User Session",
            f"userset {user_id} usess",
        )
        bot_pm = (
            "Enabled" if user_dict.get("bot_pm", config_dict["BOT_PM"]) else "Disabled"
        )
        buttons.ibutton(
            "Disable Bot PM" if bot_pm == "Enabled" else "Enable Bot PM",
            f"userset {user_id} bot_pm",
        )
        if config_dict["BOT_PM"]:
            bot_pm = "Force Enabled"
        mediainfo = (
            "Enabled"
            if user_dict.get("mediainfo", config_dict["SHOW_MEDIAINFO"])
            else "Disabled"
        )
        buttons.ibutton(
            "Disable MediaInfo" if mediainfo == "Enabled" else "Enable MediaInfo",
            f"userset {user_id} mediainfo",
        )
        if config_dict["SHOW_MEDIAINFO"]:
            mediainfo = "Force Enabled"
        save_mode = "Save As Dump" if user_dict.get("save_mode") else "Save As BotPM"
        buttons.ibutton(
            "Save As BotPM" if save_mode == "Save As Dump" else "Save As Dump",
            f"userset {user_id} save_mode",
        )
        dailytl = config_dict["DAILY_TASK_LIMIT"] or "∞"
        dailytas = (
            user_dict.get("dly_tasks")[1]
            if user_dict
            and user_dict.get("dly_tasks")
            and user_id != OWNER_ID
            and config_dict["DAILY_TASK_LIMIT"]
            else config_dict["DAILY_TASK_LIMIT"] or "️∞" if user_id != OWNER_ID else "∞"
        )
        if user_dict.get("dly_tasks", False):
            t = str(datetime.now() - user_dict["dly_tasks"][0]).split(":")
            lastused = f"{t[0]}h {t[1]}m {t[2].split('.')[0]}s ago"
        else:
            lastused = "Bot Not Used yet.."

        text = BotTheme(
            "UNIVERSAL",
            NAME=name,
            YT=escape(ytopt),
            DT=f"{dailytas} / {dailytl}",
            LAST_USED=lastused,
            BOT_PM=bot_pm,
            MEDIAINFO=mediainfo,
            SAVE_MODE=save_mode,
            USESS=u_sess,
        )
        buttons.ibutton("Back", f"userset {user_id} back", "footer")
        buttons.ibutton("Close", f"userset {user_id} close", "footer")
        button = buttons.build_menu(2)
    elif key == "mirror":
        buttons.ibutton("RClone", f"userset {user_id} rcc")
        rccmsg = "Exists" if await aiopath.exists(rclone_path) else "Not Exists"
        dailytlup = (
            get_readable_file_size(config_dict["DAILY_MIRROR_LIMIT"] * 1024**3)
            if config_dict["DAILY_MIRROR_LIMIT"]
            else "∞"
        )
        dailyup = (
            get_readable_file_size(await getdailytasks(user_id, check_mirror=True))
            if config_dict["DAILY_MIRROR_LIMIT"] and user_id != OWNER_ID
            else "️∞"
        )
        buttons.ibutton("Mirror Prefix", f"userset {user_id} mprefix")
        mprefix = (
            "Not Exists"
            if (
                val := user_dict.get(
                    "mprefix", config_dict.get("MIRROR_FILENAME_PREFIX", "")
                )
            )
            == ""
            else val
        )

        buttons.ibutton("Mirror Suffix", f"userset {user_id} msuffix")
        msuffix = (
            "Not Exists"
            if (
                val := user_dict.get(
                    "msuffix", config_dict.get("MIRROR_FILENAME_SUFFIX", "")
                )
            )
            == ""
            else val
        )

        buttons.ibutton("Mirror Remname", f"userset {user_id} mremname")
        mremname = (
            "Not Exists"
            if (
                val := user_dict.get(
                    "mremname", config_dict.get("MIRROR_FILENAME_REMNAME", "")
                )
            )
            == ""
            else val
        )

        ddl_serv = len(val) if (val := user_dict.get("ddl_servers", False)) else 0
        buttons.ibutton("DDL Servers", f"userset {user_id} ddl_servers")

        tds_mode = "Enabled" if user_dict.get("td_mode", False) else "Disabled"
        if not config_dict["USER_TD_MODE"]:
            tds_mode = "Force Disabled"

        user_tds = len(val) if (val := user_dict.get("user_tds", False)) else 0
        buttons.ibutton("User TDs", f"userset {user_id} user_tds")

        text = BotTheme(
            "MIRROR",
            NAME=name,
            RCLONE=rccmsg,
            DDL_SERVER=ddl_serv,
            DM=f"{dailyup} / {dailytlup}",
            MREMNAME=escape(mremname),
            MPREFIX=escape(mprefix),
            MSUFFIX=escape(msuffix),
            TMODE=tds_mode,
            USERTD=user_tds,
        )

        buttons.ibutton("Back", f"userset {user_id} back", "footer")
        buttons.ibutton("Close", f"userset {user_id} close", "footer")
        button = buttons.build_menu(2)
    elif key == "leech":
        if (
            user_dict.get("as_doc", False)
            or "as_doc" not in user_dict
            and config_dict["AS_DOCUMENT"]
        ):
            ltype = "DOCUMENT"
            buttons.ibutton("Send As Media", f"userset {user_id} doc")
        else:
            ltype = "MEDIA"
            buttons.ibutton("Send As Document", f"userset {user_id} doc")

        dailytlle = (
            get_readable_file_size(config_dict["DAILY_LEECH_LIMIT"] * 1024**3)
            if config_dict["DAILY_LEECH_LIMIT"]
            else "️∞"
        )
        dailyll = (
            get_readable_file_size(await getdailytasks(user_id, check_leech=True))
            if config_dict["DAILY_LEECH_LIMIT"] and user_id != OWNER_ID
            else "∞"
        )

        thumbmsg = "Exists" if await aiopath.exists(thumbpath) else "Not Exists"
        buttons.ibutton(
            f"{'✅️' if thumbmsg == 'Exists' else ''} Thumbnail",
            f"userset {user_id} thumb",
        )

        split_size = (
            get_readable_file_size(config_dict["LEECH_SPLIT_SIZE"]) + " (Default)"
            if user_dict.get("split_size", "") == ""
            else get_readable_file_size(user_dict["split_size"])
        )
        equal_splits = (
            "Enabled"
            if user_dict.get("equal_splits", config_dict.get("EQUAL_SPLITS"))
            else "Disabled"
        )
        media_group = (
            "Enabled"
            if user_dict.get("media_group", config_dict.get("MEDIA_GROUP"))
            else "Disabled"
        )
        buttons.ibutton(
            f"{'✅️' if user_dict.get('split_size') else ''} Leech Splits",
            f"userset {user_id} split_size",
        )

        lcaption = (
            "Not Exists"
            if (
                val := user_dict.get(
                    "lcaption", config_dict.get("LEECH_FILENAME_CAPTION", "")
                )
            )
            == ""
            else val
        )
        buttons.ibutton(
            f"{'✅️' if lcaption != 'Not Exists' else ''} Leech Caption",
            f"userset {user_id} lcaption",
        )

        lprefix = (
            "Not Exists"
            if (
                val := user_dict.get(
                    "lprefix", config_dict.get("LEECH_FILENAME_PREFIX", "")
                )
            )
            == ""
            else val
        )
        buttons.ibutton(
            f"{'✅️' if lprefix != 'Not Exists' else ''} Leech Prefix",
            f"userset {user_id} lprefix",
        )

        lsuffix = (
            "Not Exists"
            if (
                val := user_dict.get(
                    "lsuffix", config_dict.get("LEECH_FILENAME_SUFFIX", "")
                )
            )
            == ""
            else val
        )
        buttons.ibutton(
            f"{'✅️' if lsuffix != 'Not Exists' else ''} Leech Suffix",
            f"userset {user_id} lsuffix",
        )

        # AutoRename Template (template-based)
        lremname_auto = (
            "Not Exists"
            if (
                val := user_dict.get(
                    "lremname_auto", config_dict.get("LEECH_FILENAME_REMNAME_AUTO", "")
                )
            )
            == ""
            else val
        )
        buttons.ibutton(
            f"{'✅️' if lremname_auto != 'Not Exists' else ''} AutoRename Template",
            f"userset {user_id} lremname_auto",
        )

        # Regex Remname (regex-based)
        lremname_regex = (
            "Not Exists"
            if (
                val := user_dict.get(
                    "lremname_regex", config_dict.get("LEECH_FILENAME_REMNAME_REGEX", "")
                )
            )
            == ""
            else val
        )
        buttons.ibutton(
            f"{'✅️' if lremname_regex != 'Not Exists' else ''} Regex Remname",
            f"userset {user_id} lremname_regex",
        )

        # Rename Method toggle (only show if both exist)
        if lremname_auto != "Not Exists" and lremname_regex != "Not Exists":
            rename_method = user_dict.get("rename_method", "auto")
            buttons.ibutton(
                f"Method: {'Auto Rename' if rename_method == 'auto' else 'Regex'}",
                f"userset {user_id} rename_method",
            )

        # AutoRename toggle
        autorename_enabled = user_dict.get("autorename", True)  # Default: enabled
        buttons.ibutton(
            "Disable AutoRename" if autorename_enabled else "Enable AutoRename",
            f"userset {user_id} autorename",
        )

        # Auto Thumbnail toggle
        auto_thumb = user_dict.get("auto_thumb", config_dict.get("AUTO_THUMBNAIL", False))
        buttons.ibutton(
            "Disable Auto Thumbnail" if auto_thumb else "Enable Auto Thumbnail",
            f"userset {user_id} auto_thumb",
        )

        buttons.ibutton("Leech Dump", f"userset {user_id} ldump")
        ldump = "Not Exists" if (val := user_dict.get("ldump", "")) == "" else len(val)

        lmeta = (
            "Not Exists"
            if (val := user_dict.get("lmeta", config_dict.get("METADATA", ""))) == ""
            else val
        )
        buttons.ibutton(
            f"{'✅️' if lmeta != 'Not Exists' else ''} Metadata",
            f"userset {user_id} lmeta",
        )
        
        # Intro Subtitle button
        intro_subtitle = user_dict.get("intro_subtitle", {})
        has_intro = intro_subtitle.get("text", "") != ""
        intro_enabled = intro_subtitle.get("enabled", True) if has_intro else False
        buttons.ibutton(
            f"{'✅️' if has_intro and intro_enabled else '❌' if has_intro else ''} 📝 Intro Subtitle",
            f"userset {user_id} intro_subtitle",
        )

        # FFmpeg Commands button
        ffmpeg_cmds = user_dict.get("ffmpeg_cmds", {})
        ffmpeg_status = "Not Set"
        if ffmpeg_cmds:
            ffmpeg_status = ", ".join(ffmpeg_cmds.keys())
        buttons.ibutton(
            f"{'✅️' if ffmpeg_cmds else ''} 🎬 FFmpeg Cmds",
            f"userset {user_id} ffmpeg_cmds",
        )

        text = BotTheme(
            "LEECH",
            NAME=name,
            DL=f"{dailyll} / {dailytlle}",
            LTYPE=ltype,
            THUMB=thumbmsg,
            SPLIT_SIZE=split_size,
            EQUAL_SPLIT=equal_splits,
            MEDIA_GROUP=media_group,
            LCAPTION=escape(lcaption),
            LPREFIX=escape(lprefix),
            LSUFFIX=escape(lsuffix),
            LDUMP=ldump,
            LREMNAME_AUTO=escape(lremname_auto),
            LREMNAME_REGEX=escape(lremname_regex),
            RENAME_METHOD="Auto Rename" if user_dict.get("rename_method", "auto") == "auto" else "Regex",
            LMETA=escape(lmeta),
            AUTORENAME="Enabled" if autorename_enabled else "Disabled",
            AUTO_THUMB="Enabled" if auto_thumb else "Disabled",
        )

        buttons.ibutton("Back", f"userset {user_id} back", "footer")
        buttons.ibutton("Close", f"userset {user_id} close", "footer")
        button = buttons.build_menu(2)
    elif key == "personal_bot":
        pbot_token = user_dict.get("personal_bot_token", "")
        pbot_username = user_dict.get("personal_bot_username", "None")
        pbot_enabled = "Enabled" if user_dict.get("personal_bot_enabled", False) else "Disabled"
        
        pdump_chat = user_dict.get("personal_dump_chat_id", "")
        pdump_enabled = "Enabled" if user_dict.get("personal_dump_enabled", False) else "Disabled"
        pdump_verified = "Verified" if user_dict.get("personal_dump_verified", False) else "Not Verified"

        text = (
            f"㊂ <b><u>Personal Upload Bot Settings :</u></b>\n\n"
            f"┎ <b>Bot Token:</b> <code>{'Connected' if pbot_token else 'Not Connected'}</code>\n"
            f"┠ <b>Bot Username:</b> {'@' + pbot_username if pbot_username != 'None' else 'None'}\n"
            f"┠ <b>Bot Status:</b> <code>{pbot_enabled}</code>\n"
            f"┠ <b>Dump Channel:</b> <code>{pdump_chat or 'Not Configured'}</code>\n"
            f"┠ <b>Dump Status:</b> <code>{pdump_enabled}</code>\n"
            f"┖ <b>Dump Permissions:</b> <code>{pdump_verified}</code>\n\n"
            f"➲ <b>Description:</b> <i>Use your own Telegram bot for uploading leech files to offload the main bot and avoid FloodWaits.</i>"
        )
        
        if pbot_token:
            buttons.ibutton("Disable Bot" if user_dict.get("personal_bot_enabled", False) else "Enable Bot", f"userset {user_id} toggle_pbot")
            buttons.ibutton("Change Bot Token", f"userset {user_id} pbot_token edit")
            buttons.ibutton("Remove Bot Token", f"userset {user_id} rm_pbot")
        else:
            buttons.ibutton("Connect Bot Token", f"userset {user_id} pbot_token edit")
            
        if pdump_chat:
            buttons.ibutton("Disable Dump" if user_dict.get("personal_dump_enabled", False) else "Enable Dump", f"userset {user_id} toggle_pdump")
            buttons.ibutton("Change Dump Channel", f"userset {user_id} pdump_chat edit")
            buttons.ibutton("Remove Dump Channel", f"userset {user_id} rm_pdump")
        else:
            buttons.ibutton("Configure Dump Channel", f"userset {user_id} pdump_chat edit")

        if pbot_token and pdump_chat:
            buttons.ibutton("Verify Permissions", f"userset {user_id} verify_pbot")

        buttons.ibutton("Back", f"userset {user_id} back", "footer")
        buttons.ibutton("Close", f"userset {user_id} close", "footer")
        button = buttons.build_menu(2)
    elif key == "ddl_servers":
        ddl_serv, serv_list = 0, []
        if ddl_dict := user_dict.get("ddl_servers", False):
            for serv, (enabled, _) in ddl_dict.items():
                if enabled:
                    serv_list.append(serv)
                    ddl_serv += 1
        text = (
            f"㊂ <b><u>{fname_dict[key]} Settings :</u></b>\n\n"
            f"➲ <b>Enabled DDL Server(s) :</b> <i>{ddl_serv}</i>\n\n"
            f"➲ <b>Description :</b> <i>{desp_dict[key][0]}</i>"
        )
        for btn in ["gofile", "streamtape"]:
            buttons.ibutton(
                f"{'✅️' if btn in serv_list else ''} {fname_dict[btn]}",
                f"userset {user_id} {btn}",
            )
        buttons.ibutton("Back", f"userset {user_id} back mirror", "footer")
        buttons.ibutton("Close", f"userset {user_id} close", "footer")
        button = buttons.build_menu(2)
    elif edit_type:
        text = f"㊂ <b><u>{fname_dict[key]} Settings :</u></b>\n\n"
        if key == "rcc":
            set_exist = await aiopath.exists(rclone_path)
            text += f"➲ <b>RClone.Conf File :</b> <i>{'' if set_exist else 'Not'} Exists</i>\n\n"
        elif key == "thumb":
            set_exist = await aiopath.exists(thumbpath)
            text += f"➲ <b>Custom Thumbnail :</b> <i>{'' if set_exist else 'Not'} Exists</i>\n\n"
        elif key == "yt_opt":
            set_exist = (
                "Not Exists"
                if (
                    val := user_dict.get(
                        "yt_opt", config_dict.get("YT_DLP_OPTIONS", "")
                    )
                )
                == ""
                else val
            )
            text += f"➲ <b>YT-DLP Options :</b> <code>{escape(set_exist)}</code>\n\n"
        elif key == "usess":
            set_exist = "Exists" if user_dict.get("usess") else "Not Exists"
            text += f"➲ <b>{fname_dict[key]} :</b> <code>{set_exist}</code>\n➲ <b>Encryption :</b> {'🔐' if set_exist else '🔓'}\n\n"
        elif key == "split_size":
            set_exist = (
                get_readable_file_size(config_dict["LEECH_SPLIT_SIZE"]) + " (Default)"
                if user_dict.get("split_size", "") == ""
                else get_readable_file_size(user_dict["split_size"])
            )
            text += f"➲ <b>Leech Split Size :</b> <i>{set_exist}</i>\n\n"
            if user_dict.get("equal_splits", False) or (
                "equal_splits" not in user_dict and config_dict["EQUAL_SPLITS"]
            ):
                buttons.ibutton(
                    "Disable Equal Splits", f"userset {user_id} esplits", "header"
                )
            else:
                buttons.ibutton(
                    "Enable Equal Splits", f"userset {user_id} esplits", "header"
                )
            if user_dict.get("media_group", False) or (
                "media_group" not in user_dict and config_dict["MEDIA_GROUP"]
            ):
                buttons.ibutton(
                    "Disable Media Group", f"userset {user_id} mgroup", "header"
                )
            else:
                buttons.ibutton(
                    "Enable Media Group", f"userset {user_id} mgroup", "header"
                )
        elif key in ["pbot_token", "pdump_chat"]:
            if key == "pbot_token":
                val = user_dict.get("personal_bot_token", "")
                set_exist = "Connected" if val else "Not Connected"
            else:
                val = user_dict.get("personal_dump_chat_id", "")
                set_exist = str(val) if val else "Not Configured"
            text += f"➲ <b>Personal Bot {fname_dict[key]} :</b> {set_exist}\n\n"
        elif key in ["lprefix", "lremname_auto", "lremname_regex", "lsuffix", "lcaption", "ldump", "lmeta"]:
            set_exist = (
                "Not Exists"
                if (
                    val := user_dict.get(
                        key, config_dict.get(f"LEECH_FILENAME_{key[1:].upper()}", "")
                    )
                )
                == ""
                else val
            )
            if set_exist != "Not Exists" and key == "ldump":
                set_exist = "\n\n" + "\n".join(
                    [
                        f"{index}. <b>{dump}</b> : <code>{ids}</code>"
                        for index, (dump, ids) in enumerate(val.items(), start=1)
                    ]
                )
            text += f"➲ <b>Leech Filename {fname_dict[key]} :</b> {set_exist}\n\n"
        elif key in ["mprefix", "mremname", "msuffix"]:
            set_exist = (
                "Not Exists"
                if (
                    val := user_dict.get(
                        key, config_dict.get(f"MIRROR_FILENAME_{key[1:].upper()}", "")
                    )
                )
                == ""
                else val
            )
            text += f"➲ <b>Mirror Filename {fname_dict[key]} :</b> {set_exist}\n\n"
        elif key in ["gofile", "streamtape"]:
            set_exist = (
                "Exists"
                if key in (ddl_dict := user_dict.get("ddl_servers", {}))
                and ddl_dict[key][1]
                and ddl_dict[key][1] != ""
                else "Not Exists"
            )
            ddl_mode = (
                "Enabled"
                if key in (ddl_dict := user_dict.get("ddl_servers", {}))
                and ddl_dict[key][0]
                else "Disabled"
            )
            text = (
                f"➲ <b>Upload {fname_dict[key]} :</b> {ddl_mode}\n"
                f"➲ <b>{fname_dict[key]}'s API Key :</b> {set_exist}\n\n"
            )
            buttons.ibutton(
                "Disable DDL" if ddl_mode == "Enabled" else "Enable DDL",
                f"userset {user_id} s{key}",
                "header",
            )
        elif key == "user_tds":
            set_exist = len(val) if (val := user_dict.get(key, False)) else "Not Exists"
            tds_mode = "Enabled" if user_dict.get("td_mode", False) else "Disabled"
            buttons.ibutton(
                "Disable UserTDs" if tds_mode == "Enabled" else "Enable UserTDs",
                f"userset {user_id} td_mode",
                "header",
            )
            if not config_dict["USER_TD_MODE"]:
                tds_mode = "Force Disabled"
            text += f"➲ <b>User TD Mode :</b> {tds_mode}\n"
            text += f"➲ <b>{fname_dict[key]} :</b> {set_exist}\n\n"
        
        # Handle intro subtitle fields
        elif key in ["intro_text", "intro_duration", "intro_fontsize"]:
            intro_settings = user_dict.get("intro_subtitle", {})
            if key == "intro_text":
                set_exist = intro_settings.get("text", "")
            elif key == "intro_duration":
                set_exist = str(intro_settings.get("duration", "")) if intro_settings.get("duration") else ""
            else:  # intro_fontsize
                set_exist = str(intro_settings.get("font_size", "")) if intro_settings.get("font_size") else ""
            
            set_exist = "Not Exists" if set_exist == "" else set_exist
            text = f"➲ <b>{fname_dict[key]} :</b> {set_exist}\n\n"
        
        elif key == "ffmpeg_cmds":
            ffc = user_dict.get("ffmpeg_cmds", {})
            if ffc:
                set_exist = "\n" + "\n".join(
                    [
                        f"{no}. <b>{k}</b>: <code>{escape(str(v[0][:60]))}{'...' if len(str(v[0])) > 60 else ''}</code>"
                        for no, (k, v) in enumerate(ffc.items(), start=1)
                    ]
                )
            else:
                set_exist = "Not Exists"
            text += f"➲ <b>{fname_dict[key]} :</b> {set_exist}\n\n"
        
        else:
            return
        text += f"➲ <b>Description :</b> <i>{desp_dict[key][0]}</i>"
        if not edit_mode:
            buttons.ibutton(
                (
                    f"Change {fname_dict[key]}"
                    if set_exist
                    and set_exist != "Not Exists"
                    and (
                        set_exist
                        != get_readable_file_size(config_dict["LEECH_SPLIT_SIZE"])
                        + " (Default)"
                    )
                    else f"Set {fname_dict[key]}"
                ),
                f"userset {user_id} {key} edit",
            )
        else:
            text += "\n\n" + desp_dict[key][1]
            buttons.ibutton("Stop Change", f"userset {user_id} {key}")
        if (
            set_exist
            and set_exist != "Not Exists"
            and (
                set_exist
                != get_readable_file_size(config_dict["LEECH_SPLIT_SIZE"])
                + " (Default)"
            )
        ):
            if key == "thumb":
                buttons.ibutton("View Thumbnail", f"userset {user_id} vthumb", "header")
            elif key == "user_tds":
                buttons.ibutton("Show UserTDs", f"userset {user_id} show_tds", "header")
            buttons.ibutton("↻ Delete", f"userset {user_id} d{key}")
        buttons.ibutton("Back", f"userset {user_id} back {edit_type}", "footer")
        buttons.ibutton("Close", f"userset {user_id} close", "footer")
        button = buttons.build_menu(2)
    
    return text, button


async def update_user_settings(
    query, key=None, edit_type=None, edit_mode=None, msg=None, sdirect=False
):
    msg, button = await get_user_settings(
        msg.from_user if sdirect else query.from_user, key, edit_type, edit_mode
    )
    await editMessage(query if sdirect else query.message, msg, button)


# ============ INTRO SUBTITLE INPUT HANDLERS ============
async def set_intro_text(client, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    text = message.text
    
    # Validate and escape text
    success, escaped_text, error = validate_and_escape_subtitle_text(text)
    
    if not success:
        await sendMessage(message, f"❌ {error}")
        await update_user_settings(pre_event, "intro_text", "leech")
        return
    
    # Get or create intro_subtitle dict
    intro_settings = user_data.get(user_id, {}).get("intro_subtitle", {})
    intro_settings["text"] = text
    
    # Set defaults if not already set
    if "color" not in intro_settings:
        intro_settings["color"] = "white"
    if "bg_color" not in intro_settings:
        intro_settings["bg_color"] = "none"
    if "duration" not in intro_settings:
        intro_settings["duration"] = 5
    if "mode" not in intro_settings:
        intro_settings["mode"] = "softsub"
    if "font_size" not in intro_settings:
        intro_settings["font_size"] = 24
    if "enabled" not in intro_settings:
        intro_settings["enabled"] = True
    
    update_user_ldata(user_id, "intro_subtitle", intro_settings)
    
    if DATABASE_URL:
        await DbManger().update_user_data(user_id)
    
    await deleteMessage(message)
    await update_user_settings(pre_event, "intro_text", "leech")


async def set_intro_duration(client, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    duration_text = message.text.strip()
    
    # Validate duration
    if not duration_text.isdigit():
        await sendMessage(message, "❌ Duration must be a number!")
        await update_user_settings(pre_event, "intro_duration", "leech")
        return
    
    duration = int(duration_text)
    
    if duration < 1 or duration > 30:
        await sendMessage(message, "❌ Duration must be between 1-30 seconds!")
        await update_user_settings(pre_event, "intro_duration", "leech")
        return
    
    # Update intro settings
    intro_settings = user_data.get(user_id, {}).get("intro_subtitle", {})
    intro_settings["duration"] = duration
    update_user_ldata(user_id, "intro_subtitle", intro_settings)
    
    if DATABASE_URL:
        await DbManger().update_user_data(user_id)
    
    await deleteMessage(message)
    await update_user_settings(pre_event, "intro_duration", "leech")


async def set_intro_fontsize(client, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    size_text = message.text.strip()
    
    # Validate font size
    if not size_text.isdigit():
        await sendMessage(message, "❌ Font size must be a number!")
        await update_user_settings(pre_event, "intro_fontsize", "leech")
        return
    
    font_size = int(size_text)
    
    if font_size < 12 or font_size > 72:
        await sendMessage(message, "❌ Font size must be between 12-72!")
        await update_user_settings(pre_event, "intro_fontsize", "leech")
        return
    
    # Update intro settings
    intro_settings = user_data.get(user_id, {}).get("intro_subtitle", {})
    intro_settings["font_size"] = font_size
    update_user_ldata(user_id, "intro_subtitle", intro_settings)
    
    if DATABASE_URL:
        await DbManger().update_user_data(user_id)
    
    await deleteMessage(message)
    await update_user_settings(pre_event, "intro_fontsize", "leech")


async def user_settings(client, message):
    if len(message.command) > 1 and (
        message.command[1] == "-s" or message.command[1] == "-set"
    ):
        set_arg = message.command[2].strip() if len(message.command) > 2 else None
        msg = await sendMessage(message, "<i>Fetching Settings...</i>", photo="IMAGES")
        if set_arg and (reply_to := message.reply_to_message):
            if message.from_user.id != reply_to.from_user.id:
                return await editMessage(
                    msg,
                    "<i>Reply to Your Own Message for Setting via Args Directly</i>",
                )
            if (
                set_arg
                in [
                    "lprefix",
                    "lsuffix",
                    "lremname",
                    "lcaption",
                    "ldump",
                    "yt_opt",
                    "lmeta",
                    "intro_text",
                    "intro_duration",
                    "intro_fontsize",
                ]
                and reply_to.text
            ):
                return await set_custom(client, reply_to, msg, set_arg, True)
            elif set_arg == "thumb" and reply_to.media:
                return await set_thumb(client, reply_to, msg, set_arg, True)
        await editMessage(
            msg,
            """㊂ <b><u>Available Flags :</u></b>
>> Reply to the Value with appropriate arg respectively to set directly without opening USet.

➲ <b>Custom Thumbnail :</b>
    /cmd -s thumb
➲ <b>Leech Filename Prefix :</b>
    /cmd -s lprefix
➲ <b>Leech Filename Suffix :</b>
    /cmd -s lsuffix
➲ <b>Leech Filename Remname :</b>
    /cmd -s lremname
➲ <b>Leech Filename Caption :</b>
    /cmd -s lcaption
➲ <b>Leech Metadata Text :</b>
    /cmd -s lmeta
➲ <b>YT-DLP Options :</b>
    /cmd -s yt_opt
➲ <b>Leech User Dump :</b>
    /cmd -s ldump""",
        )
    else:
        from_user = message.from_user
        handler_dict[from_user.id] = False
        msg, button = await get_user_settings(from_user)
        await sendMessage(message, msg, button, "IMAGES")


async def set_personal_setting(client, message, pre_event, key):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    value = message.text.strip()
    
    if key == "pbot_token":
        verifying_msg = await sendMessage(message, "⏳ <i>Verifying bot token, please wait...</i>")
        success, res = await verify_personal_bot(value)
        await deleteMessage(verifying_msg)
        
        if success:
            update_user_ldata(user_id, "personal_bot_token", value)
            update_user_ldata(user_id, "personal_bot_username", res)
            await PersonalBotManager.get_instance().stop_client(user_id)
            await sendMessage(message, f"✅ <b>Success!</b> Bot token verified.\nConnected to: @{res}")
        else:
            await sendMessage(message, f"❌ <b>Failed!</b> Invalid bot token:\n<code>{escape(res)}</code>")
            
    elif key == "pdump_chat":
        if value.startswith("-100"):
            try:
                chat_id = int(value)
            except ValueError:
                chat_id = value
        elif value.startswith("-") or value.isdigit():
            try:
                chat_id = int(value)
            except ValueError:
                chat_id = value
        else:
            chat_id = value
            
        update_user_ldata(user_id, "personal_dump_chat_id", chat_id)
        update_user_ldata(user_id, "personal_dump_verified", False)
        await sendMessage(message, f"✅ <b>Dump Channel saved!</b>\nTarget: <code>{chat_id}</code>\n\n<i>Note: Remember to run 'Verify Permissions' to ensure your Personal Bot can write to this channel!</i>")
        
    if DATABASE_URL:
        await DbManger().update_user_data(user_id)
        
    await deleteMessage(message)
    await update_user_settings(pre_event, "personal_bot")


async def set_custom(client, message, pre_event, key, direct=False):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    value = message.text
    LOGGER.info(f"[SET_CUSTOM] Called for user {user_id}, key={key}, value={value[:50] if value else 'None'}")
    return_key = "leech"
    n_key = key
    user_dict = user_data.get(user_id, {})
    if key in ["gofile", "streamtape"]:
        ddl_dict = user_dict.get("ddl_servers", {})
        mode, api = ddl_dict.get(key, [False, ""])
        if key == "gofile" and not await Gofile.is_goapi(value):
            value = ""
        ddl_dict[key] = [mode, value]
        value = ddl_dict
        n_key = "ddl_servers"
        return_key = "ddl_servers"
    elif key == "user_tds":
        user_tds = user_dict.get(key, {})
        for td_item in value.split("\n"):
            if td_item == "":
                continue
            split_ck = td_item.split()
            td_details = td_item.rsplit(
                maxsplit=(
                    2
                    if split_ck[-1].startswith("http")
                    and not is_gdrive_link(split_ck[-1])
                    else 1 if len(split_ck[-1]) > 15 else 0
                )
            )
            if td_details[0] in list(categories_dict.keys()):
                continue
            for title in list(user_tds.keys()):
                if td_details[0].casefold() == title.casefold():
                    del user_tds[title]
            if len(td_details) > 1:
                if is_gdrive_link(td_details[1].strip()):
                    td_details[1] = GoogleDriveHelper.getIdFromUrl(td_details[1])
                if await sync_to_async(
                    GoogleDriveHelper().getFolderData, td_details[1]
                ):
                    user_tds[td_details[0]] = {
                        "drive_id": td_details[1],
                        "index_link": (
                            td_details[2].rstrip("/") if len(td_details) > 2 else ""
                        ),
                    }
        value = user_tds
        return_key = "mirror"
    elif key == "ldump":
        ldumps = user_dict.get(key, {})
        for dump_item in value.split("\n"):
            if dump_item == "":
                continue
            dump_info = dump_item.rsplit(
                maxsplit=(1 if dump_item.split()[-1].startswith(("-100", "@")) else 0)
            )
            if dump_info[0] in list(ldumps.keys()):
                continue
            for title in list(ldumps.keys()):
                if dump_info[0].casefold() == title.casefold():
                    del ldumps[title]
            if len(dump_info) > 1 and (dump_chat := await chat_info(dump_info[1])):
                ldumps[dump_info[0]] = dump_chat.id
        value = ldumps
    elif key in ["yt_opt", "usess"]:
        if key == "usess":
            password = Fernet.generate_key()
            try:
                await deleteMessage(
                    await (
                        await sendCustomMsg(
                            message.from_user.id,
                            f"<u><b>Decryption Key:</b></u> \n┃\n┃ <code>{password.decode()}</code>\n┃\n┖ <b>Note:</b> <i>Keep this Key Securely, this is not Stored in Bot and Access Key to use your Session...</i>",
                        )
                    ).pin(both_sides=True)
                )
                encrypt_sess = Fernet(password).encrypt(value.encode())
                value = encrypt_sess.decode()
            except Exception:
                value = ""
        return_key = "universal"
    elif key == "ffmpeg_cmds":
        import json
        try:
            parsed = json.loads(value)
            if not isinstance(parsed, dict):
                await sendMessage(message, "❌ <b>FFMPEG_CMDS must be a JSON dict!</b>\nExample: <code>{\"keep_japanese\": [\"-i mltb.video -map 0:v:0 -c copy mltb.mkv\"]}</code>")
                await update_user_settings(pre_event, key, "leech", msg=message, sdirect=direct)
                return
            for k, v in parsed.items():
                if not isinstance(v, list):
                    parsed[k] = [v]
            value = parsed
        except json.JSONDecodeError:
            await sendMessage(message, "❌ <b>Invalid JSON format!</b>\nSend a valid JSON dict.\nExample: <code>{\"keep_japanese\": [\"-i mltb.video -map 0:v:0 -c copy mltb.mkv\"]}</code>")
            await update_user_settings(pre_event, key, "leech", msg=message, sdirect=direct)
            return
    elif key in ["intro_text", "intro_duration", "intro_fontsize"]:
        # Handle intro subtitle fields inline
        intro_settings = user_dict.get("intro_subtitle", {})
        
        if key == "intro_text":
            # Validate text
            success, escaped_text, error = validate_and_escape_subtitle_text(value)
            if not success:
                await sendMessage(message, f"❌ {error}")
                await update_user_settings(pre_event, key, "leech", msg=message, sdirect=direct)
                return
            intro_settings["text"] = value
            # Set defaults
            if "color" not in intro_settings:
                intro_settings["color"] = "white"
            if "bg_color" not in intro_settings:
                intro_settings["bg_color"] = "none"
            if "duration" not in intro_settings:
                intro_settings["duration"] = 5
            if "mode" not in intro_settings:
                intro_settings["mode"] = "softsub"
            if "font_size" not in intro_settings:
                intro_settings["font_size"] = 24
        
        elif key == "intro_duration":
            # Validate duration
            if not value.isdigit():
                await sendMessage(message, "❌ Duration must be a number!")
                await update_user_settings(pre_event, key, "leech", msg=message, sdirect=direct)
                return
            duration = int(value)
            if duration < 1 or duration > 30:
                await sendMessage(message, "❌ Duration must be between 1-30 seconds!")
                await update_user_settings(pre_event, key, "leech", msg=message, sdirect=direct)
                return
            intro_settings["duration"] = duration
        
        elif key == "intro_fontsize":
            # Validate font size
            if not value.isdigit():
                await sendMessage(message, "❌ Font size must be a number!")
                await update_user_settings(pre_event, key, "leech", msg=message, sdirect=direct)
                return
            font_size = int(value)
            if font_size < 12 or font_size > 72:
                await sendMessage(message, "❌ Font size must be between 12-72!")
                await update_user_settings(pre_event, key, "leech", msg=message, sdirect=direct)
                return
            intro_settings["font_size"] = font_size
        
        value = intro_settings
        n_key = "intro_subtitle"
        return_key = "leech"
    
    update_user_ldata(user_id, n_key, value)
    await deleteMessage(message)
    await update_user_settings(pre_event, key, return_key, msg=message, sdirect=direct)
    if DATABASE_URL:
        await DbManger().update_user_data(user_id)


async def set_thumb(client, message, pre_event, key, direct=False):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    path = "Thumbnails/"
    if not await aiopath.isdir(path):
        await mkdir(path)
    photo_dir = await message.download()
    des_dir = ospath.join(path, f"{user_id}.jpg")
    await sync_to_async(Image.open(photo_dir).convert("RGB").save, des_dir, "JPEG")
    await aioremove(photo_dir)
    update_user_ldata(user_id, "thumb", des_dir)
    await deleteMessage(message)
    await update_user_settings(pre_event, key, "leech", msg=message, sdirect=direct)
    if DATABASE_URL:
        await DbManger().update_user_doc(user_id, "thumb", des_dir)


async def add_rclone(client, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    path = f"{getcwd()}/rclone/"
    if not await aiopath.isdir(path):
        await mkdir(path)
    des_dir = ospath.join(path, f"{user_id}.conf")
    await message.download(file_name=des_dir)
    update_user_ldata(user_id, "rclone", f"rclone/{user_id}.conf")
    await deleteMessage(message)
    await update_user_settings(pre_event, "rcc", "mirror")
    if DATABASE_URL:
        await DbManger().update_user_doc(user_id, "rclone", des_dir)


async def leech_split_size(client, message, pre_event):
    user_id = message.from_user.id
    handler_dict[user_id] = False
    sdic = ["b", "kb", "mb", "gb"]
    value = message.text.strip()
    slice = -2 if value[-2].lower() in ["k", "m", "g"] else -1
    out = value[slice:].strip().lower()
    if out in sdic:
        value = min(
            (float(value[:slice].strip()) * 1024 ** sdic.index(out)), MAX_SPLIT_SIZE
        )
    update_user_ldata(user_id, "split_size", int(round(value)))
    await deleteMessage(message)
    await update_user_settings(pre_event, "split_size", "leech")
    if DATABASE_URL:
        await DbManger().update_user_data(user_id)


async def event_handler(client, query, pfunc, rfunc, photo=False, document=False):
    user_id = query.from_user.id
    handler_dict[user_id] = True
    start_time = time()

    async def event_filter(_, __, event):
        if photo:
            mtype = event.photo
        elif document:
            mtype = event.document
        else:
            mtype = event.text
        user = event.from_user or event.sender_chat
        return bool(
            user.id == user_id and event.chat.id == query.message.chat.id and mtype
        )

    handler = client.add_handler(
        MessageHandler(pfunc, filters=create(event_filter)), group=-1
    )
    while handler_dict[user_id]:
        await sleep(0.5)
        if time() - start_time > 60:
            handler_dict[user_id] = False
            await rfunc()
    client.remove_handler(*handler)




# Simplified approach - store callback info in handler_dict instead of dynamic handlers
async def wait_for_input(query, pfunc, rfunc, photo=False, document=False):
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    
    # Store callback info in handler_dict
    handler_dict[user_id] = {
        "active": True,
        "chat_id": chat_id,
        "pfunc": pfunc,
        "rfunc": rfunc,
        "photo": photo,
        "document": document,
        "start_time": time()
    }
    
    LOGGER.info(f"[WAIT_INPUT] Registered input handler for user {user_id} in chat {chat_id}")


# Global message handler - processes messages for users waiting for input
async def global_settings_input_handler(client, message):
    user_id = message.from_user.id if message.from_user else None
    chat_id = message.chat.id
    
    if not user_id or user_id not in handler_dict:
        return
    
    user_handler = handler_dict[user_id]
    
    # Check if it's a dict (new system) or bool (old system - ignore)
    if not isinstance(user_handler, dict) or not user_handler.get("active"):
        return
    
    # Check if message is in the right chat
    if user_handler["chat_id"] != chat_id:
        return
    
    # Check for timeout (5 minutes)
    if time() - user_handler["start_time"] > 300:
        LOGGER.info(f"[GLOBAL_HANDLER] Timeout for user {user_id}")
        handler_dict[user_id] = False
        await user_handler["rfunc"]()
        return
    
    # Check message type matches what we're waiting for
    if user_handler["photo"] and not message.photo:
        return
    if user_handler["document"] and not message.document:
        return
    if not user_handler["photo"] and not user_handler["document"] and not message.text:
        return
    
    LOGGER.info(f"[GLOBAL_HANDLER] Processing input for user {user_id}: {message.text if message.text else 'media'}")
    
    # Clear handler before processing to prevent re-entrance
    handler_dict[user_id] = False
    
    # Call the processing function
    try:
        await user_handler["pfunc"](client, message)
        LOGGER.info(f"[GLOBAL_HANDLER] Successfully processed input for user {user_id}")
    except Exception as e:
        LOGGER.error(f"[GLOBAL_HANDLER] Error processing input for user {user_id}: {e}", exc_info=True)



async def edit_user_settings(client, query):
    from_user = query.from_user
    user_id = from_user.id
    message = query.message
    data = query.data.split()
    thumb_path = f"Thumbnails/{user_id}.jpg"
    rclone_path = f"rclone/{user_id}.conf"
    user_dict = user_data.get(user_id, {})
    if user_id != int(data[1]):
        await query.answer("Not Yours!", show_alert=True)
    elif data[2] in ["universal", "mirror", "leech", "personal_bot"]:
        await query.answer()
        await update_user_settings(query, data[2])
    elif data[2] == "toggle_pbot":
        handler_dict[user_id] = False
        if not user_dict.get("personal_bot_token"):
            return await query.answer("Please connect a bot token first!", show_alert=True)
        await query.answer()
        current = user_dict.get("personal_bot_enabled", False)
        update_user_ldata(user_id, "personal_bot_enabled", not current)
        await update_user_settings(query, "personal_bot")
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
    elif data[2] == "toggle_pdump":
        handler_dict[user_id] = False
        if not user_dict.get("personal_dump_chat_id"):
            return await query.answer("Please configure a dump channel first!", show_alert=True)
        await query.answer()
        current = user_dict.get("personal_dump_enabled", False)
        update_user_ldata(user_id, "personal_dump_enabled", not current)
        await update_user_settings(query, "personal_bot")
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
    elif data[2] in ["rm_pbot", "dpbot_token"]:
        handler_dict[user_id] = False
        await query.answer("Bot Token removed!")
        update_user_ldata(user_id, "personal_bot_token", "")
        update_user_ldata(user_id, "personal_bot_username", "None")
        update_user_ldata(user_id, "personal_bot_enabled", False)
        await PersonalBotManager.get_instance().stop_client(user_id)
        await update_user_settings(query, "personal_bot" if data[2] == "rm_pbot" else "pbot_token", "personal_bot")
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
    elif data[2] in ["rm_pdump", "dpdump_chat"]:
        handler_dict[user_id] = False
        await query.answer("Dump channel removed!")
        update_user_ldata(user_id, "personal_dump_chat_id", "")
        update_user_ldata(user_id, "personal_dump_enabled", False)
        update_user_ldata(user_id, "personal_dump_verified", False)
        await update_user_settings(query, "personal_bot" if data[2] == "rm_pdump" else "pdump_chat", "personal_bot")
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
    elif data[2] == "verify_pbot":
        handler_dict[user_id] = False
        token = user_dict.get("personal_bot_token", "")
        dump = user_dict.get("personal_dump_chat_id", "")
        if not token or not dump:
            return await query.answer("Configure both Bot Token and Dump Chat first!", show_alert=True)
        await query.answer("Verifying write access to dump channel...", show_alert=False)
        success, msg = await verify_personal_dump(token, dump)
        if success:
            update_user_ldata(user_id, "personal_dump_verified", True)
            btn = ButtonMaker()
            btn.ibutton("OK", f"userset {user_id} personal_bot")
            await query.message.edit_text(
                f"✅ <b>Verification Successful!</b>\n\n{msg}",
                reply_markup=btn.build_menu(1)
            )
        else:
            update_user_ldata(user_id, "personal_dump_verified", False)
            btn = ButtonMaker()
            btn.ibutton("Try Again", f"userset {user_id} personal_bot")
            await query.message.edit_text(
                f"❌ <b>Verification Failed!</b>\n\n<b>Error:</b> <code>{escape(msg)}</code>",
                reply_markup=btn.build_menu(1)
            )
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
    elif data[2] in ["pbot_token", "pdump_chat"]:
        await query.answer()
        edit_mode = len(data) == 4
        await update_user_settings(query, data[2], "personal_bot", edit_mode)
        if not edit_mode:
            return
        pfunc = partial(set_personal_setting, pre_event=query, key=data[2])
        rfunc = partial(update_user_settings, query, data[2], "personal_bot")
        await wait_for_input(query, pfunc, rfunc)
    elif data[2] == "doc":
        update_user_ldata(user_id, "as_doc", not user_dict.get("as_doc", False))
        await query.answer()
        await update_user_settings(query, "leech")
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
    elif data[2] == "vthumb":
        handler_dict[user_id] = False
        await query.answer()
        buttons = ButtonMaker()
        buttons.ibutton("Cʟᴏsᴇ", f"wzmlx {user_id} close")
        await sendMessage(message, from_user.mention, buttons.build_menu(1), thumb_path)
        await update_user_settings(query, "thumb", "leech")
    elif data[2] == "show_tds":
        handler_dict[user_id] = False
        user_tds = user_dict.get("user_tds", {})
        msg = f"➲ <b><u>User TD(s) Details</u></b>\n\n<b>Total UserTD(s) :</b> {len(user_tds)}\n\n"
        for index_no, (drive_name, drive_dict) in enumerate(user_tds.items(), start=1):
            msg += f"{index_no}: <b>Name:</b> <code>{drive_name}</code>\n"
            msg += f"  <b>Drive ID:</b> <code>{drive_dict['drive_id']}</code>\n"
            msg += f"  <b>Index Link:</b> <code>{ind_url if (ind_url := drive_dict['index_link']) else 'Not Provided'}</code>\n\n"
        try:
            await sendCustomMsg(user_id, msg)
            await query.answer("User TDs Successfully Send in your PM", show_alert=True)
        except Exception:
            await query.answer(
                "Start the Bot in PM (Private) and Try Again", show_alert=True
            )
        await update_user_settings(query, "user_tds", "mirror")
    elif data[2] == "dthumb":
        handler_dict[user_id] = False
        if await aiopath.exists(thumb_path):
            await query.answer()
            await aioremove(thumb_path)
            update_user_ldata(user_id, "thumb", "")
            await update_user_settings(query, "thumb", "leech")
            if DATABASE_URL:
                await DbManger().update_user_doc(user_id, "thumb")
        else:
            await query.answer("Old Settings", show_alert=True)
            await update_user_settings(query, "leech")
    elif data[2] == "thumb":
        await query.answer()
        edit_mode = len(data) == 4
        await update_user_settings(query, data[2], "leech", edit_mode)
        if not edit_mode:
            return
        pfunc = partial(set_thumb, pre_event=query, key=data[2])
        rfunc = partial(update_user_settings, query, data[2], "leech")
        await wait_for_input(query, pfunc, rfunc, True)
    elif data[2] in ["yt_opt", "usess"]:
        await query.answer()
        edit_mode = len(data) == 4
        await update_user_settings(query, data[2], "universal", edit_mode)
        if not edit_mode:
            return
        pfunc = partial(set_custom, pre_event=query, key=data[2])
        rfunc = partial(update_user_settings, query, data[2], "universal")
        await wait_for_input(query, pfunc, rfunc)
    elif data[2] in ["dyt_opt", "dusess"]:
        handler_dict[user_id] = False
        await query.answer()
        update_user_ldata(user_id, data[2][1:], "")
        await update_user_settings(query, data[2][1:], "universal")
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
    elif data[2] in ["bot_pm", "mediainfo", "save_mode", "td_mode"]:
        handler_dict[user_id] = False
        if (
            data[2] == "save_mode"
            and not user_dict.get(data[2], False)
            and not user_dict.get("ldump")
        ):
            return await query.answer(
                "Set User Dump first to Change Save Msg Mode !", show_alert=True
            )
        elif (
            data[2] == "bot_pm"
            and (config_dict["BOT_PM"] or config_dict["SAFE_MODE"])
            or data[2] == "mediainfo"
            and config_dict["SHOW_MEDIAINFO"]
            or data[2] == "td_mode"
            and not config_dict["USER_TD_MODE"]
        ):
            mode_up = "Disabled" if data[2] == "td_mode" else "Enabled"
            return await query.answer(
                f"Force {mode_up}! Can't Alter Settings", show_alert=True
            )
        if data[2] == "td_mode" and not user_dict.get("user_tds", False):
            return await query.answer(
                "Set UserTD first to Enable User TD Mode !", show_alert=True
            )
        await query.answer()
        update_user_ldata(user_id, data[2], not user_dict.get(data[2], False))
        if data[2] in ["td_mode"]:
            await update_user_settings(query, "user_tds", "mirror")
        else:
            await update_user_settings(query, "universal")
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
    elif data[2] == "split_size":
        await query.answer()
        edit_mode = len(data) == 4
        await update_user_settings(query, data[2], "leech", edit_mode)
        if not edit_mode:
            return
        pfunc = partial(leech_split_size, pre_event=query)
        rfunc = partial(update_user_settings, query, data[2], "leech")
        await wait_for_input(query, pfunc, rfunc)
    elif data[2] == "dsplit_size":
        handler_dict[user_id] = False
        await query.answer()
        update_user_ldata(user_id, "split_size", "")
        await update_user_settings(query, "split_size", "leech")
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
    elif data[2] == "esplits":
        handler_dict[user_id] = False
        await query.answer()
        update_user_ldata(
            user_id, "equal_splits", not user_dict.get("equal_splits", False)
        )
        await update_user_settings(query, "leech")
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
    elif data[2] == "mgroup":
        handler_dict[user_id] = False
        await query.answer()
        update_user_ldata(
            user_id, "media_group", not user_dict.get("media_group", False)
        )
        await update_user_settings(query, "leech")
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
    elif data[2] == "autorename":
        handler_dict[user_id] = False
        await query.answer()
        update_user_ldata(
            user_id, "autorename", not user_dict.get("autorename", True)
        )
        await update_user_settings(query, "leech")
    elif data[2] == "auto_thumb":
        handler_dict[user_id] = False
        await query.answer()
        update_user_ldata(
            user_id, "auto_thumb", not user_dict.get("auto_thumb", config_dict.get("AUTO_THUMBNAIL", False))
        )
        await update_user_settings(query, "leech")
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
    
    # ============ INTRO SUBTITLE HANDLERS ============
    elif data[2] == "intro_subtitle":
        # Show intro subtitle settings menu
        handler_dict[user_id] = False
        await query.answer()
        
        intro_settings = user_dict.get("intro_subtitle", {})
        # Force softsub mode for all users
        intro_settings["mode"] = "softsub"
        text = intro_settings.get("text", "Not Set")
        color = intro_settings.get("color", "white")
        bg_color = intro_settings.get("bg_color", "none")
        duration = intro_settings.get("duration", 5)
        font_size = intro_settings.get("font_size", 24)
        is_enabled = intro_settings.get("enabled", True)
        
        buttons = ButtonMaker()
        msg = f"📝 <b>Intro Subtitle Settings</b>\n\n"
        msg += f"<b>Status:</b> {'✅ Enabled' if is_enabled else '❌ Disabled'}\n"
        msg += f"<b>Text:</b> <code>{escape(text[:50])}...</code>" if len(text) > 50 else f"<b>Text:</b> <code>{escape(text)}</code>"
        msg += f"\n<b>Color:</b> {COLOR_OPTIONS.get(color, color)}"
        msg += f"\n<b>Background:</b> {BG_COLOR_OPTIONS.get(bg_color, bg_color)}"
        msg += f"\n<b>Duration:</b> {duration} seconds"
        msg += f"\n<b>Font Size:</b> {font_size}px"
        msg += f"\n<b>Mode:</b> Softsub (Default Track)"
        
        # Enable/Disable toggle button (only show if text is set)
        if text != "Not Set":
            buttons.ibutton(
                "❌ Disable" if is_enabled else "✅ Enable",
                f"userset {user_id} intro_toggle",
            )
        
        buttons.ibutton("Set Text", f"userset {user_id} intro_text")
        buttons.ibutton("Set Color", f"userset {user_id} intro_color")
        buttons.ibutton("Set Background", f"userset {user_id} intro_bgcolor")
        buttons.ibutton("Set Duration", f"userset {user_id} intro_duration")
        buttons.ibutton("Set Font Size", f"userset {user_id} intro_fontsize")
        
        if text != "Not Set":
            buttons.ibutton("🗑️ Reset All", f"userset {user_id} intro_reset", "footer")
        
        buttons.ibutton("Back", f"userset {user_id} leech", "footer")
        buttons.ibutton("Close", f"userset {user_id} close", "footer")
        
        await editMessage(query.message, msg, buttons.build_menu(2))
    
    
    elif data[2] == "intro_text":
        await query.answer()
        edit_mode = len(data) == 4
        await update_user_settings(query, "intro_text", "leech", edit_mode)
        if not edit_mode:
            return
        pfunc = partial(set_custom, pre_event=query, key="intro_text")
        rfunc = partial(update_user_settings, query, "intro_text", "leech")
        await wait_for_input(query, pfunc, rfunc)
    
    elif data[2] == "intro_color":
        # Show color options
        handler_dict[user_id] = False
        await query.answer()
        
        buttons = ButtonMaker()
        msg = "<b>Select Text Color:</b>"
        
        for color_key, color_name in COLOR_OPTIONS.items():
            buttons.ibutton(color_name, f"userset {user_id} intro_setcolor^{color_key}")
        
        buttons.ibutton("Back", f"userset {user_id} intro_subtitle", "footer")
        await editMessage(query.message, msg, buttons.build_menu(2))
    
    elif data[2].startswith("intro_setcolor"):
        # Set specific color
        handler_dict[user_id] = False
        await query.answer()
        
        color = data[2].split("^")[1]
        intro_settings = user_dict.get("intro_subtitle", {})
        intro_settings["color"] = color
        update_user_ldata(user_id, "intro_subtitle", intro_settings)
        
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
        
        await asyncio.sleep(0.5)
        # Go back to intro subtitle menu
        await query.message.edit_reply_markup(None)
        fake_data = ["userset", str(user_id), "intro_subtitle"]
        query.data = " ".join(fake_data)
        await edit_user_settings(client, query)
    
    elif data[2] == "intro_bgcolor":
        # Show background color options
        handler_dict[user_id] = False
        await query.answer()
        
        buttons = ButtonMaker()
        msg = "<b>Select Background Color:</b>"
        
        for color_key, color_name in BG_COLOR_OPTIONS.items():
            buttons.ibutton(color_name, f"userset {user_id} intro_setbgcolor^{color_key}")
        
        buttons.ibutton("Back", f"userset {user_id} intro_subtitle", "footer")
        await editMessage(query.message, msg, buttons.build_menu(2))
    
    elif data[2].startswith("intro_setbgcolor"):
        # Set specific background color
        handler_dict[user_id] = False
        await query.answer()
        
        bg_color = data[2].split("^")[1]
        intro_settings = user_dict.get("intro_subtitle", {})
        intro_settings["bg_color"] = bg_color
        update_user_ldata(user_id, "intro_subtitle", intro_settings)
        
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
        
        await asyncio.sleep(0.5)
        # Go back to intro subtitle menu
        await query.message.edit_reply_markup(None)
        fake_data = ["userset", str(user_id), "intro_subtitle"]
        query.data = " ".join(fake_data)
        await edit_user_settings(client, query)
    
    elif data[2] == "intro_duration":
        await query.answer()
        edit_mode = len(data) == 4
        await update_user_settings(query, "intro_duration", "leech", edit_mode)
        if not edit_mode:
            return
        pfunc = partial(set_custom, pre_event=query, key="intro_duration")
        rfunc = partial(update_user_settings, query, "intro_duration", "leech")
        await wait_for_input(query, pfunc, rfunc)

    elif data[2] == "intro_fontsize":
        await query.answer()
        edit_mode = len(data) == 4
        await update_user_settings(query, "intro_fontsize", "leech", edit_mode)
        if not edit_mode:
            return
        pfunc = partial(set_custom, pre_event=query, key="intro_fontsize")
        rfunc = partial(update_user_settings, query, "intro_fontsize", "leech")
        await wait_for_input(query, pfunc, rfunc)
    
    elif data[2] == "intro_toggle":
        # Toggle intro subtitle enabled/disabled without deleting settings
        handler_dict[user_id] = False
        intro_settings = user_dict.get("intro_subtitle", {})
        current = intro_settings.get("enabled", True)
        intro_settings["enabled"] = not current
        update_user_ldata(user_id, "intro_subtitle", intro_settings)
        
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
        
        status = "enabled ✅" if not current else "disabled ❌"
        await query.answer(f"Intro subtitle {status}")
        
        # Refresh the intro subtitle menu
        await asyncio.sleep(0.3)
        await query.message.edit_reply_markup(None)
        fake_data = ["userset", str(user_id), "intro_subtitle"]
        query.data = " ".join(fake_data)
        await edit_user_settings(client, query)
    
    elif data[2] == "intro_reset":
        # Reset all intro subtitle settings
        handler_dict[user_id] = False
        await query.answer("Intro subtitle settings reset!")
        update_user_ldata(user_id, "intro_subtitle", {})
        
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
        
        await update_user_settings(query, "leech")
    
    elif data[2] in ["sgofile", "sstreamtape", "dgofile", "dstreamtape"]:
        handler_dict[user_id] = False
        ddl_dict = user_dict.get("ddl_servers", {})
        key = data[2][1:]
        mode, api = ddl_dict.get(key, [False, ""])
        if data[2][0] == "s":
            if not mode and api == "":
                return await query.answer(
                    "Set API to Enable DDL Server", show_alert=True
                )
            ddl_dict[key] = [not mode, api]
        elif data[2][0] == "d":
            ddl_dict[key] = [mode, ""]
        await query.answer()
        update_user_ldata(user_id, "ddl_servers", ddl_dict)
        await update_user_settings(query, key, "ddl_servers")
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
    elif data[2] == "rcc":
        await query.answer()
        edit_mode = len(data) == 4
        await update_user_settings(query, data[2], "mirror", edit_mode)
        if not edit_mode:
            return
        pfunc = partial(add_rclone, pre_event=query)
        rfunc = partial(update_user_settings, query, data[2], "mirror")
        await wait_for_input(query, pfunc, rfunc, document=True)
    elif data[2] == "drcc":
        handler_dict[user_id] = False
        if await aiopath.exists(rclone_path):
            await query.answer()
            await aioremove(rclone_path)
            update_user_ldata(user_id, "rclone", "")
            await update_user_settings(query, "rcc", "mirror")
            if DATABASE_URL:
                await DbManger().update_user_doc(user_id, "rclone")
        else:
            await query.answer("Old Settings", show_alert=True)
            await update_user_settings(query)
    elif data[2] in ["ddl_servers", "user_tds", "gofile", "streamtape"]:
        handler_dict[user_id] = False
        await query.answer()
        edit_mode = len(data) == 4
        await update_user_settings(
            query,
            data[2],
            "mirror" if data[2] in ["ddl_servers", "user_tds"] else "ddl_servers",
            edit_mode,
        )
        if not edit_mode:
            return
        pfunc = partial(set_custom, pre_event=query, key=data[2])
        rfunc = partial(
            update_user_settings,
            query,
            data[2],
            "mirror" if data[2] in ["ddl_servers", "user_tds"] else "ddl_servers",
        )
        await wait_for_input(query, pfunc, rfunc)
    elif data[2] in [
        "lprefix",
        "lsuffix",
        "lremname_auto",
        "lremname_regex",
        "lcaption",
        "ldump",
        "mprefix",
        "msuffix",
        "mremname",
        "lmeta",
        "ffmpeg_cmds",
    ]:
        handler_dict[user_id] = False
        await query.answer()
        edit_mode = len(data) == 4
        return_key = "leech" if data[2][0] == "l" or data[2] == "ffmpeg_cmds" else "mirror"
        await update_user_settings(query, data[2], return_key, edit_mode)
        if not edit_mode:
            return
        pfunc = partial(set_custom, pre_event=query, key=data[2])
        rfunc = partial(update_user_settings, query, data[2], return_key)
        await wait_for_input(query, pfunc, rfunc)
    elif data[2] == "rename_method":
        handler_dict[user_id] = False
        await query.answer()
        current_method = user_dict.get("rename_method", "auto")
        new_method = "regex" if current_method == "auto" else "auto"
        update_user_ldata(user_id, "rename_method", new_method)
        await update_user_settings(query, "leech")
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
    elif data[2] in [
        "dlprefix",
        "dlsuffix",
        "dlremname_auto",
        "dlremname_regex",
        "dlcaption",
        "dldump",
        "dlmeta",
        "dffmpeg_cmds",
    ]:
        handler_dict[user_id] = False
        await query.answer()
        update_user_ldata(user_id, data[2][1:], {} if data[2] in ["dldump", "dffmpeg_cmds"] else "")
        await update_user_settings(query, data[2][1:], "leech")
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
    elif data[2] in ["dmprefix", "dmsuffix", "dmremname", "duser_tds"]:
        handler_dict[user_id] = False
        await query.answer()
        update_user_ldata(user_id, data[2][1:], {} if data[2] == "duser_tds" else "")
        if data[2] == "duser_tds":
            update_user_ldata(user_id, "td_mode", False)
        await update_user_settings(query, data[2][1:], "mirror")
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
    elif data[2] == "back":
        handler_dict[user_id] = False
        await query.answer()
        setting = data[3] if len(data) == 4 else None
        await update_user_settings(query, setting)
    elif data[2] == "reset_all":
        handler_dict[user_id] = False
        await query.answer()
        buttons = ButtonMaker()
        buttons.ibutton("Yes", f"userset {user_id} reset_now y")
        buttons.ibutton("No", f"userset {user_id} reset_now n")
        buttons.ibutton("Close", f"userset {user_id} close", "footer")
        await editMessage(
            message, "Do you want to Reset Settings ?", buttons.build_menu(2)
        )
    elif data[2] == "reset_now":
        handler_dict[user_id] = False
        if data[3] == "n":
            return await update_user_settings(query)
        if await aiopath.exists(thumb_path):
            await aioremove(thumb_path)
        if await aiopath.exists(rclone_path):
            await aioremove(rclone_path)
        await query.answer()
        update_user_ldata(user_id, None, None)
        await update_user_settings(query)
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
            await DbManger().update_user_doc(user_id, "thumb")
            await DbManger().update_user_doc(user_id, "rclone")
    elif data[2] == "user_del":
        user_id = int(data[3])
        await query.answer()
        thumb_path = f"Thumbnails/{user_id}.jpg"
        rclone_path = f"rclone/{user_id}.conf"
        if await aiopath.exists(thumb_path):
            await aioremove(thumb_path)
        if await aiopath.exists(rclone_path):
            await aioremove(rclone_path)
        update_user_ldata(user_id, None, None)
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
            await DbManger().update_user_doc(user_id, "thumb")
            await DbManger().update_user_doc(user_id, "rclone")
        await editMessage(message, f"Data Reset for {user_id}")
    else:
        handler_dict[user_id] = False
        await query.answer()
        await deleteMessage(message.reply_to_message)
        await deleteMessage(message)


# Add this function HERE (around line 2448)
async def set_thumbnail_by_reply(client, message):
    user_id = message.from_user.id
    reply_to = message.reply_to_message
    
    if reply_to is None:
        await sendMessage(message, "❌ Reply to a photo to set it as thumbnail!")
        return
        
    if not reply_to.photo:
        await sendMessage(message, "❌ Please reply to a photo!")
        return
    
    try:
        thumb_path = f"Thumbnails/{user_id}.jpg"
        
        # Download and save the thumbnail
        await reply_to.download(file_name=thumb_path)
        
        # Update user data
        update_user_ldata(user_id, "thumb", thumb_path)
        
        # Update database if enabled
        if DATABASE_URL:
            await DbManger().update_user_doc(user_id, "thumb")
        
        await sendMessage(message, "✅ Thumbnail set successfully!")
        
    except Exception as e:
        LOGGER.error(f"Error setting thumbnail: {e}")
        await sendMessage(message, f"❌ Error setting thumbnail: {str(e)}")

async def send_users_settings(client, message):
    text = message.text.split(maxsplit=1)
    userid = text[1] if len(text) > 1 else None
    if userid and not userid.isdigit():
        userid = None
    elif (
        (reply_to := message.reply_to_message)
        and reply_to.from_user
        and not reply_to.from_user.is_bot
    ):
        userid = reply_to.from_user.id
    if not userid:
        msg = f"<u><b>Total Users / Chats Data Saved :</b> {len(user_data)}</u>"
        buttons = ButtonMaker()
        buttons.ibutton("Close", f"userset {message.from_user.id} close")
        button = buttons.build_menu(1)
        for user, data in user_data.items():
            msg += f"\n\n<code>{user}</code>:"
            if data:
                for key, value in data.items():
                    if key in ["token", "time", "ddl_servers", "usess", "personal_bot_token"]:
                        continue
                    msg += f"\n<b>{key}</b>: <code>{escape(str(value))}</code>"
            else:
                msg += "\nUser's Data is Empty!"
        if len(msg.encode()) > 4000:
            with BytesIO(str.encode(msg)) as ofile:
                ofile.name = "users_settings.txt"
                await sendFile(message, ofile)
        else:
            await sendMessage(message, msg, button)
    elif int(userid) in user_data:
        msg = f'{(await user_info(userid)).mention(style="html")} ( <code>{userid}</code> ):'
        if data := user_data[int(userid)]:
            buttons = ButtonMaker()
            buttons.ibutton(
                "Delete Data", f"userset {message.from_user.id} user_del {userid}"
            )
            buttons.ibutton("Close", f"userset {message.from_user.id} close")
            button = buttons.build_menu(1)
            for key, value in data.items():
                if key in ["token", "time", "ddl_servers", "usess", "personal_bot_token"]:
                    continue
                msg += f"\n<b>{key}</b>: <code>{escape(str(value))}</code>"
        else:
            msg += "\nThis User has not Saved anything."
            button = None
        await sendMessage(message, msg, button)
    else:
        await sendMessage(message, f"{userid} have not saved anything..")


# ============ /aux AUTORENAME COMMAND ============
@new_task
async def autorename_cmd(client, message):
    """
    /aux [template] — Set AutoRename template directly.
    /aux            — Show current template.
    /aux off        — Clear the saved template.

    Example: /aux [animeshrine.xyz] S0{season}E{episode} Dr. Stone {quality}.mkv
    """
    user_id = message.from_user.id
    user_dict = user_data.get(user_id, {})
    args = message.text.split(maxsplit=1)

    # --- No argument: show current template ---
    if len(args) == 1:
        current = user_dict.get(
            "lremname_auto",
            config_dict.get("LEECH_FILENAME_REMNAME_AUTO", ""),
        )
        if current:
            await sendMessage(
                message,
                f"📝 <b>Current AutoRename Template:</b>\n"
                f"<code>{escape(current)}</code>\n\n"
                f"<b>Usage:</b> <code>/aux [template]</code>\n"
                f"<b>Clear:</b> <code>/aux off</code>",
            )
        else:
            await sendMessage(
                message,
                "📝 <b>No AutoRename template set.</b>\n\n"
                "<b>Usage:</b> <code>/aux [animeshrine.xyz] S0{{season}}E{{episode}} Dr. Stone {{quality}}.mkv</code>\n\n"
                "<b>Available tags:</b>\n"
                "  <code>{title}</code> — parsed title\n"
                "  <code>{season}</code> — season number\n"
                "  <code>{episode}</code> — episode number\n"
                "  <code>{quality}</code> — video quality (e.g. 1080p)\n"
                "  <code>{codec}</code> — video codec\n"
                "  <code>{audio}</code> — audio codec\n"
                "  <code>{chapter}</code> — chapter number\n"
                "  <code>{episode:+N}</code> — episode with offset",
            )
        return

    template = args[1].strip()

    # --- Clear template ---
    if template.lower() in ("off", "clear", "reset", "del", "none"):
        update_user_ldata(user_id, "lremname_auto", "")
        if DATABASE_URL:
            await DbManger().update_user_data(user_id)
        await sendMessage(message, "✅ <b>AutoRename template cleared!</b>")
        return

    # --- Save new template ---
    update_user_ldata(user_id, "lremname_auto", template)
    if DATABASE_URL:
        await DbManger().update_user_data(user_id)

    await sendMessage(
        message,
        f"✅ <b>AutoRename template saved!</b>\n\n"
        f"<code>{escape(template)}</code>",
    )


bot.add_handler(
    MessageHandler(
        send_users_settings,
        filters=command(BotCommands.UsersCommand) & CustomFilters.sudo,
    )
)
bot.add_handler(
    MessageHandler(
        user_settings,
        filters=command(BotCommands.UserSetCommand) & CustomFilters.authorized_uset,
    )
)
bot.add_handler(
    MessageHandler(
        set_thumbnail_by_reply,
        filters=command(BotCommands.ThumbnailCommand) & CustomFilters.authorized,
    )
)
bot.add_handler(
    MessageHandler(
        autorename_cmd,
        filters=command(BotCommands.AutoRenameCommand) & CustomFilters.authorized,
    )
)
bot.add_handler(CallbackQueryHandler(edit_user_settings, filters=regex("^userset")))

# Register global message handler for user settings input
bot.add_handler(
    MessageHandler(
        global_settings_input_handler,
        filters=text | photo | document  # Catches text, photos, and documents
    ),
    group=-2  # Lower than default to let other handlers run first
)
LOGGER.info("[USER_SETTINGS] Global settings input handler registered at group=-2")
