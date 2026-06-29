#!/usr/bin/env python3
from time import time
from aiofiles.os import remove as aioremove, path as aiopath

from bot import (
    download_dict,
    download_dict_lock,
    get_client,
    LOGGER,
    config_dict,
    non_queued_dl,
    queue_dict_lock,
)
from bot.helper.mirror_utils.status_utils.qbit_status import QbittorrentStatus
from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    deleteMessage,
    sendStatusMessage,
)
from bot.helper.ext_utils.bot_utils import bt_selection_buttons, sync_to_async
from bot.helper.listeners.qbit_listener import onDownloadStart
from bot.helper.ext_utils.task_manager import is_queued


"""
Only v1 torrents
#from hashlib import sha1
#from base64 import b16encode, b32decode
#from bencoding import bencode, bdecode
#from re import search as re_search
def __get_hash_magnet(mgt: str):
    hash_ = re_search(r'(?<=xt=urn:btih:)[a-zA-Z0-9]+', mgt).group(0)
    if len(hash_) == 32:
        hash_ = b16encode(b32decode(hash_.upper())).decode()
    return str(hash_)

def __get_hash_file(path):
    with open(path, "rb") as f:
        decodedDict = bdecode(f.read())
        hash_ = sha1(bencode(decodedDict[b'info'])).hexdigest()
    return str(hash_)
"""


async def add_qb_torrent(link, path, listener, ratio, seed_time, name=""):
    client = await sync_to_async(get_client)
    ADD_TIME = time()
    try:
        url = link
        tpath = None
        if await aiopath.exists(link):
            url = None
            tpath = link
        added_to_queue, event = await is_queued(listener.uid)
        op = await sync_to_async(
            client.torrents_add,
            url,
            tpath,
            path,
            is_paused=added_to_queue,
            tags=f"{listener.uid}",
            ratio_limit=ratio,
            seeding_time_limit=seed_time,
            headers={"user-agent": "Wget/1.12"},
        )
        if op.lower() == "ok.":
            tor_info = await sync_to_async(client.torrents_info, tag=f"{listener.uid}")
            if len(tor_info) == 0:
                while True:
                    tor_info = await sync_to_async(
                        client.torrents_info, tag=f"{listener.uid}"
                    )
                    if len(tor_info) > 0:
                        break
                    elif time() - ADD_TIME >= 120:
                        msg = "Not added! Check if the link is valid or not. If it's torrent file then report, this happens if torrent file size above 10mb."
                        await sendMessage(listener.message, msg)
                        return
            tor_info = tor_info[0]
            ext_hash = tor_info.hash
            
            # Rename torrent content if custom name provided
            if name:
                try:
                    # Get the torrent files
                    files = await sync_to_async(client.torrents_files, torrent_hash=ext_hash)
                    if files:
                        # Get the base name and extension from first file
                        old_name = files[0].name
                        if "/" in old_name:  # Multi-file torrent
                            # Rename the folder
                            folder_name = old_name.split("/")[0]
                            await sync_to_async(client.torrents_rename_folder, 
                                              torrent_hash=ext_hash, 
                                              old_path=folder_name, 
                                              new_path=name)
                            LOGGER.info(f"Renamed torrent folder: {folder_name} → {name}")
                        else:  # Single file torrent
                            # Add extension from original file
                            from os.path import splitext
                            ext = splitext(old_name)[1]
                            new_name = name if ext in name else f"{name}{ext}"
                            await sync_to_async(client.torrents_rename_file, 
                                              torrent_hash=ext_hash, 
                                              old_path=old_name, 
                                              new_path=new_name)
                            LOGGER.info(f"Renamed torrent file: {old_name} → {new_name}")
                except Exception as e:
                    LOGGER.error(f"Error renaming torrent: {e}")
        else:
            await sendMessage(
                listener.message,
                "This Torrent already added or unsupported/invalid link/file.",
            )
            return

        async with download_dict_lock:
            download_dict[listener.uid] = QbittorrentStatus(
                listener, queued=added_to_queue
            )
        await onDownloadStart(f"{listener.uid}")

        if added_to_queue:
            LOGGER.info(f"Added to Queue/Download: {tor_info.name} - Hash: {ext_hash}")
        else:
            async with queue_dict_lock:
                non_queued_dl.add(listener.uid)
            LOGGER.info(f"QbitDownload started: {tor_info.name} - Hash: {ext_hash}")

        await listener.onDownloadStart()

        if config_dict["BASE_URL"] and listener.select:
            if link.startswith("magnet:"):
                metamsg = "Downloading Metadata, wait then you can select files. Use torrent file to avoid this wait."
                meta = await sendMessage(listener.message, metamsg)
                while True:
                    tor_info = await sync_to_async(
                        client.torrents_info, tag=f"{listener.uid}"
                    )
                    if len(tor_info) == 0:
                        await deleteMessage(meta)
                        return
                    try:
                        tor_info = tor_info[0]
                        if tor_info.state not in [
                            "metaDL",
                            "checkingResumeData",
                            "pausedDL",
                        ]:
                            await deleteMessage(meta)
                            break
                    except Exception:
                        await deleteMessage(meta)
                        return

            ext_hash = tor_info.hash
            if not added_to_queue:
                await sync_to_async(client.torrents_pause, torrent_hashes=ext_hash)
            SBUTTONS = bt_selection_buttons(ext_hash)
            msg = "Your download paused. Choose files then press Done Selecting button to start downloading."
            await sendMessage(listener.message, msg, SBUTTONS)
        else:
            await sendStatusMessage(listener.message)

        if added_to_queue:
            await event.wait()

            async with download_dict_lock:
                if listener.uid not in download_dict:
                    return
                download_dict[listener.uid].queued = False

            await sync_to_async(client.torrents_resume, torrent_hashes=ext_hash)
            LOGGER.info(
                f"Start Queued Download from Qbittorrent: {tor_info.name} - Hash: {ext_hash}"
            )

            async with queue_dict_lock:
                non_queued_dl.add(listener.uid)
    except Exception as e:
        await sendMessage(listener.message, str(e))
    finally:
        if await aiopath.exists(link):
            await aioremove(link)
