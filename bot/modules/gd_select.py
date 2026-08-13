#!/usr/bin/env python3
"""
Google Drive Folder File Selection — Web selection UI.
"""
from pyrogram.handlers import CallbackQueryHandler
from pyrogram.filters import regex

from bot import bot, LOGGER, config_dict
from bot.helper.telegram_helper.message_utils import deleteMessage
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.bot_utils import get_readable_file_size, new_task
from web.gdrive_selection_store import GDriveSelectionStore


def gd_selection_buttons(uid: int):
    gid = str(uid)
    pincode = "".join([n for n in gid if n.isdigit()][:4])
    buttons = ButtonMaker()
    BASE_URL = config_dict["BASE_URL"]
    buttons.ubutton("Select Files", f"{BASE_URL}/app/files/{gid}")
    buttons.ibutton("Pincode", f"gdsel pin {gid} {pincode}")
    buttons.ibutton("Cancel", f"gdsel cancel {gid}")
    buttons.ibutton("Done Selecting", f"gdsel done {gid}")
    return buttons.build_menu(2)


@new_task
async def gd_select_cb(client, query):
    """Handle all gdsel callback queries."""
    from bot.helper.mirror_utils.download_utils.gd_download import gd_select_cache

    parts = query.data.split()
    action = parts[1]
    uid = int(parts[2])
    user_id = query.from_user.id

    cache = gd_select_cache.get(uid)
    if cache is None:
        await query.answer("⚠️ Session expired or download already started!", show_alert=True)
        try:
            await deleteMessage(query.message)
        except Exception:
            pass
        return

    if user_id != cache.get("user_id"):
        await query.answer("❌ This selection is not for you!", show_alert=True)
        return

    if action == "pin":
        await query.answer(parts[3], show_alert=True)

    elif action == "done":
        selected_ids = GDriveSelectionStore().read_selection(str(uid))
        for idx, f in enumerate(cache["files"]):
            f["selected"] = str(idx) in selected_ids

        selected = [f for f in cache["files"] if f["selected"]]
        if not selected:
            await query.answer("⚠️ Select at least one file first!", show_alert=True)
            return
        total_sel_size = sum(f["size"] for f in selected)
        await query.answer(
            f"🚀 Starting download of {len(selected)} file(s) "
            f"({get_readable_file_size(total_sel_size)})!"
        )
        LOGGER.info(
            f"[GDRIVE SELECT] uid={uid} user={user_id} "
            f"selected {len(selected)}/{len(cache['files'])} files "
            f"({get_readable_file_size(total_sel_size)})"
        )
        await deleteMessage(query.message)
        GDriveSelectionStore().delete_data(str(uid))
        cache["event"].set()

    elif action == "cancel":
        await query.answer("❌ Download cancelled!")
        LOGGER.info(f"[GDRIVE SELECT] uid={uid} user={user_id} cancelled selection")
        cache["is_cancelled"] = True
        await deleteMessage(query.message)
        GDriveSelectionStore().delete_data(str(uid))
        cache["event"].set()


bot.add_handler(CallbackQueryHandler(gd_select_cb, filters=regex(r"^gdsel")))
