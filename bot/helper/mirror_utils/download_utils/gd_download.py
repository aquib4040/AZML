#!/usr/bin/env python3
from asyncio import Event
from json import dumps as jdumps
from secrets import token_hex
from cloudscraper import create_scraper as cget

from bot import (
    download_dict,
    download_dict_lock,
    LOGGER,
    non_queued_dl,
    queue_dict_lock,
)
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.mirror_utils.status_utils.gdrive_status import GdriveStatus
from bot.helper.mirror_utils.status_utils.queue_status import QueueStatus
from bot.helper.telegram_helper.message_utils import sendMessage, sendStatusMessage
from bot.helper.ext_utils.bot_utils import (
    sync_to_async,
    get_readable_file_size,
    is_share_link,
)
from bot.helper.ext_utils.task_manager import (
    is_queued,
    limit_checker,
    stop_duplicate_check,
)

# Populated by add_gd_download, consumed by gd_select.py callbacks.
gd_select_cache: dict = {}


def prepare_gdrive_file_list(files):
    file_list = []
    seen_dirs = set()
    for idx, f in enumerate(files):
        rel_path = f["rel_path"]
        parts = [p for p in rel_path.split("/") if p]
        for i in range(len(parts)):
            dir_path = "/".join(parts[:i])
            if dir_path:
                dir_path += "/"
            dir_name = parts[i]
            full_dir_path = f"{dir_path}{dir_name}"
            if full_dir_path not in seen_dirs:
                seen_dirs.add(full_dir_path)
                file_list.append(
                    {
                        "name": dir_name,
                        "path": dir_path,
                        "size": 0,
                        "id": f"dir_{full_dir_path}",
                        "is_dir": True,
                        "selected": True,
                    }
                )

        file_list.append(
            {
                "name": f["name"],
                "path": rel_path,
                "size": f["size"],
                "id": str(idx),
                "is_dir": False,
                "selected": f.get("selected", True),
            }
        )
    return file_list


async def add_gd_download(link, path, listener, newname, org_link):
    drive = GoogleDriveHelper()
    name, mime_type, size, _, _ = await sync_to_async(drive.count, link)
    if is_share_link(org_link):
        cget().request(
            "POST",
            "https://wzmlcontribute.vercel.app/contribute",
            headers={"Content-Type": "application/json"},
            data=jdumps(
                {"name": name, "link": org_link, "size": get_readable_file_size(size)}
            ),
        )
    if mime_type is None:
        await sendMessage(listener.message, name)
        return

    name = newname or name

    # ════════════════════════════════════════════════════════════════════════
    # GDRIVE FOLDER FILE SELECTION FLOW
    # Triggered when: -s flag is set AND the link is a folder
    # ════════════════════════════════════════════════════════════════════════
    if listener.select and mime_type == "Folder":
        file_id = GoogleDriveHelper.getIdFromUrl(link)
        files = await sync_to_async(drive.get_folder_tree, file_id)

        if not files:
            await sendMessage(listener.message, "❌ No files found in this Google Drive folder.")
            return

        sel_event = Event()
        gd_select_cache[listener.uid] = {
            "files": files,
            "event": sel_event,
            "is_cancelled": False,
            "folder_name": name,
            "user_id": listener.message.from_user.id,
        }

        from web.gdrive_selection_store import GDriveSelectionStore

        file_list = prepare_gdrive_file_list(files)
        GDriveSelectionStore().save_data(listener.uid, file_list)
        all_ids = [str(idx) for idx, _ in enumerate(files)]
        GDriveSelectionStore().save_selection(listener.uid, all_ids)

        from bot.modules.gd_select import gd_selection_buttons

        msg_text = (
            "Your Google Drive download paused. Choose files from selection web link then press Done Selecting button."
        )
        buttons = gd_selection_buttons(listener.uid)
        await sendMessage(listener.message, msg_text, buttons)

        # ── Wait for user action (Done / Cancel) ──
        await sel_event.wait()

        cache = gd_select_cache.pop(listener.uid, {})
        if cache.get("is_cancelled"):
            await listener.onDownloadError("Google Drive file selection cancelled by user")
            return

        selected_files = [f for f in cache.get("files", []) if f["selected"]]
        if not selected_files:
            await sendMessage(listener.message, "❌ No files selected. Download cancelled.")
            return

        # ── Size limit check on selected total ──
        size = sum(f["size"] for f in selected_files)
        msg, button = await stop_duplicate_check(name, listener)
        if msg:
            await sendMessage(listener.message, msg, button)
            return
        if limit_exceeded := await limit_checker(size, listener, isDriveLink=True):
            await sendMessage(listener.message, limit_exceeded)
            return

        # ── Queue check ──
        gid = token_hex(5)
        added_to_queue, event = await is_queued(listener.uid)
        if added_to_queue:
            LOGGER.info(f"[GDRIVE SELECT] Added to Queue/Download: {name}")
            async with download_dict_lock:
                download_dict[listener.uid] = QueueStatus(name, size, gid, listener, "dl")
            await listener.onDownloadStart()
            await sendStatusMessage(listener.message)
            await event.wait()
            async with download_dict_lock:
                if listener.uid not in download_dict:
                    return
            from_queue = True
        else:
            from_queue = False

        drive = GoogleDriveHelper(name, path, listener)
        async with download_dict_lock:
            download_dict[listener.uid] = GdriveStatus(
                drive, size, listener.message, gid, "dl", listener.upload_details
            )

        async with queue_dict_lock:
            non_queued_dl.add(listener.uid)

        if from_queue:
            LOGGER.info(f"Start Queued Download from GDrive: {name}")
        else:
            LOGGER.info(f"Download from GDrive: {name}")
            await listener.onDownloadStart()
            await sendStatusMessage(listener.message)

        await sync_to_async(drive.download_selected, selected_files)
        return

    # Normal Download Flow
    gid = token_hex(5)
    msg, button = await stop_duplicate_check(name, listener)
    if msg:
        await sendMessage(listener.message, msg, button)
        return
    if limit_exceeded := await limit_checker(size, listener, isDriveLink=True):
        await sendMessage(listener.message, limit_exceeded)
        return
    added_to_queue, event = await is_queued(listener.uid)
    if added_to_queue:
        LOGGER.info(f"Added to Queue/Download: {name}")
        async with download_dict_lock:
            download_dict[listener.uid] = QueueStatus(name, size, gid, listener, "dl")
        await listener.onDownloadStart()
        await sendStatusMessage(listener.message)
        await event.wait()
        async with download_dict_lock:
            if listener.uid not in download_dict:
                return
        from_queue = True
    else:
        from_queue = False

    drive = GoogleDriveHelper(name, path, listener)
    async with download_dict_lock:
        download_dict[listener.uid] = GdriveStatus(
            drive, size, listener.message, gid, "dl", listener.upload_details
        )

    async with queue_dict_lock:
        non_queued_dl.add(listener.uid)

    if from_queue:
        LOGGER.info(f"Start Queued Download from GDrive: {name}")
    else:
        LOGGER.info(f"Download from GDrive: {name}")
        await listener.onDownloadStart()
        await sendStatusMessage(listener.message)

    await sync_to_async(drive.download, link)
