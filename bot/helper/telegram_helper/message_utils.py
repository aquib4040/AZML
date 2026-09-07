#!/usr/bin/env python3
from traceback import format_exc
from asyncio import sleep
from aiofiles.os import remove as aioremove
from random import choice as rchoice
from time import time
from re import match as re_match, search as re_search, sub as re_sub
from cryptography.fernet import InvalidToken

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import InputMediaPhoto
from pyrogram.errors import (
    ReplyMarkupInvalid,
    FloodWait,
    PeerIdInvalid,
    ChannelInvalid,
    RPCError,
    UserNotParticipant,
    MessageNotModified,
    MessageEmpty,
    PhotoInvalidDimensions,
    WebpageCurlFailed,
    MediaEmpty,
)

from bot import (
    config_dict,
    user_data,
    categories_dict,
    bot_cache,
    LOGGER,
    bot_name,
    status_reply_dict,
    status_reply_dict_lock,
    Interval,
    bot,
    user,
    download_dict_lock,
)
from bot.helper.ext_utils.bot_utils import (
    get_readable_message,
    setInterval,
    sync_to_async,
    download_image_url,
    fetch_user_tds,
    fetch_user_dumps,
    new_thread,
)
import aiohttp
import json

from bot.helper.telegram_helper.button_build import ButtonMaker, to_bot_api_keyboard
from bot.helper.ext_utils.exceptions import TgLinkException

_http_session = None


async def get_http_session():
    global _http_session
    if _http_session is None or _http_session.closed:
        connector = aiohttp.TCPConnector(limit=100, keepalive_timeout=75)
        _http_session = aiohttp.ClientSession(connector=connector)
    return _http_session


def sanitize_telegram_html(text: str) -> str:
    if not text:
        return text
    # Convert Pyrogram pseudo-tags to Bot API valid HTML tags
    text = str(text).replace("<spoiler>", "<tg-spoiler>").replace("</spoiler>", "</tg-spoiler>")
    text = text.replace("<SPOILER>", "<tg-spoiler>").replace("</SPOILER>", "</tg-spoiler>")
    return text


async def send_styled_http_message(chat_id, text, keyboard_dict, photo=None, reply_to_message_id=None):
    bot_token = config_dict.get("BOT_TOKEN", "")
    if not bot_token:
        return None
    text = sanitize_telegram_html(text)
    if photo:
        if photo == "IMAGES":
            try:
                images_list = config_dict.get("IMAGES", [])
                photo = rchoice(images_list) if images_list else None
            except Exception:
                photo = None
        if photo:
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            payload = {
                "chat_id": chat_id,
                "photo": photo,
                "caption": text,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(keyboard_dict),
                "disable_notification": True,
            }
        else:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(keyboard_dict),
                "disable_web_page_preview": True,
                "disable_notification": True,
            }
    else:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": json.dumps(keyboard_dict),
            "disable_web_page_preview": True,
            "disable_notification": True,
        }
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    try:
        session = await get_http_session()
        async with session.post(url, data=payload, timeout=8) as resp:
            data = await resp.json()
            if data.get("ok"):
                msg_id = data["result"]["message_id"]
                return await bot.get_messages(chat_id, msg_id)
            else:
                LOGGER.error(f"HTTP Styled Message API Error: {data}")
    except Exception as e:
        LOGGER.error(f"HTTP Styled Message Error: {e}")
    return None


async def edit_styled_http_message(chat_id, message_id, text, keyboard_dict, is_media=False):
    bot_token = config_dict.get("BOT_TOKEN", "")
    if not bot_token:
        return None
    text = sanitize_telegram_html(text)
    url = f"https://api.telegram.org/bot{bot_token}/editMessageCaption" if is_media else f"https://api.telegram.org/bot{bot_token}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "caption" if is_media else "text": text,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(keyboard_dict),
    }
    if not is_media:
        payload["disable_web_page_preview"] = True
    try:
        session = await get_http_session()
        async with session.post(url, data=payload, timeout=8) as resp:
            data = await resp.json()
            if data.get("ok"):
                return True
            if is_media and not data.get("ok"):
                url2 = f"https://api.telegram.org/bot{bot_token}/editMessageText"
                payload2 = {
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps(keyboard_dict),
                    "disable_web_page_preview": True,
                }
                async with session.post(url2, data=payload2, timeout=8) as resp2:
                    d2 = await resp2.json()
                    return d2.get("ok", False)
    except Exception as e:
        LOGGER.error(f"HTTP Styled Edit Error: {e}")
    return None


async def edit_styled_http_reply_markup(chat_id, message_id, keyboard_dict):
    bot_token = config_dict.get("BOT_TOKEN", "")
    if not bot_token:
        return None
    url = f"https://api.telegram.org/bot{bot_token}/editMessageReplyMarkup"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reply_markup": json.dumps(keyboard_dict),
    }
    try:
        session = await get_http_session()
        async with session.post(url, data=payload, timeout=8) as resp:
            data = await resp.json()
            if data.get("ok"):
                return True
    except Exception as e:
        LOGGER.error(f"HTTP Styled ReplyMarkup Error: {e}")
    return None


async def sendMessage(message, text, buttons=None, photo=None, **kwargs):
    try:
        if kb_dict := to_bot_api_keyboard(buttons):
            chat_id = message.chat.id
            reply_to_id = (
                rply.id
                if (rply := message.reply_to_message)
                and not rply.text
                and not rply.caption
                else None
            )
            http_msg = await send_styled_http_message(chat_id, text, kb_dict, photo, reply_to_id)
            if http_msg:
                return http_msg
        if photo:
            try:
                if photo == "IMAGES":
                    photo = rchoice(config_dict["IMAGES"])
                return await message.reply_photo(
                    photo=photo,
                    reply_to_message_id=message.id,
                    caption=text,
                    reply_markup=buttons,
                    disable_notification=True,
                    **kwargs,
                )
            except IndexError:
                pass
            except (PhotoInvalidDimensions, WebpageCurlFailed, MediaEmpty):
                des_dir = await download_image_url(photo)
                await sendMessage(message, text, buttons, des_dir)
                await aioremove(des_dir)
                return
            except Exception:
                LOGGER.error(format_exc())
        return await message.reply(
            text=text,
            quote=True,
            disable_web_page_preview=True,
            disable_notification=True,
            reply_markup=buttons,
            reply_to_message_id=(
                rply.id
                if (rply := message.reply_to_message)
                and not rply.text
                and not rply.caption
                else None
            ),
            **kwargs,
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await sendMessage(message, text, buttons, photo)
    except ReplyMarkupInvalid:
        return await sendMessage(message, text, None, photo)
    except MessageEmpty:
        return await sendMessage(message, text, parse_mode=ParseMode.DISABLED)
    except Exception as e:
        LOGGER.error(format_exc())
        return str(e)


async def sendCustomMsg(chat_id, text, buttons=None, photo=None, debug=False):
    try:
        if kb_dict := to_bot_api_keyboard(buttons):
            http_msg = await send_styled_http_message(chat_id, text, kb_dict, photo)
            if http_msg:
                return http_msg
        if photo:
            try:
                if photo == "IMAGES":
                    photo = rchoice(config_dict["IMAGES"])
                return await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=text,
                    reply_markup=buttons,
                    disable_notification=True,
                )
            except IndexError:
                pass
            except (PhotoInvalidDimensions, WebpageCurlFailed, MediaEmpty):
                des_dir = await download_image_url(photo)
                await sendCustomMsg(chat_id, text, buttons, des_dir)
                await aioremove(des_dir)
                return
            except Exception:
                LOGGER.error(format_exc())
        return await bot.send_message(
            chat_id=chat_id,
            text=text,
            disable_web_page_preview=True,
            disable_notification=True,
            reply_markup=buttons,
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await sendCustomMsg(chat_id, text, buttons, photo)
    except ReplyMarkupInvalid:
        return await sendCustomMsg(chat_id, text, None, photo)
    except Exception as e:
        LOGGER.error(format_exc())
        return str(e)


async def chat_info(channel_id):
    channel_id = str(channel_id).strip()
    if channel_id.startswith("-100"):
        channel_id = int(channel_id)
    elif channel_id.startswith("@"):
        channel_id = channel_id.replace("@", "")
    else:
        return None
    try:
        return await bot.get_chat(channel_id)
    except (PeerIdInvalid, ChannelInvalid) as e:
        LOGGER.error(f"{e.NAME}: {e.MESSAGE} for {channel_id}")
        return None


async def sendMultiMessage(chat_ids, text, buttons=None, photo=None):
    msg_dict = {}
    for channel_id in chat_ids.split():
        channel_id, *topic_id = channel_id.split(":")
        topic_id = int(topic_id[0]) if len(topic_id) else None
        chat = await chat_info(channel_id)
        try:
            if photo:
                try:
                    if photo == "IMAGES":
                        photo = rchoice(config_dict["IMAGES"])
                    sent = await bot.send_photo(
                        chat_id=chat.id,
                        photo=photo,
                        caption=text,
                        reply_markup=buttons,
                        reply_to_message_id=topic_id,
                        disable_notification=True,
                    )
                    msg_dict[f"{chat.id}:{topic_id}"] = sent
                except IndexError:
                    pass
                except (PhotoInvalidDimensions, WebpageCurlFailed, MediaEmpty):
                    des_dir = await download_image_url(photo)
                    await sendMultiMessage(chat_ids, text, buttons, des_dir)
                    await aioremove(des_dir)
                    break
                except Exception as e:
                    LOGGER.error(str(e))
                continue
            LOGGER.info("DEBUG CP 2")
            if not photo and (kb_dict := to_bot_api_keyboard(buttons)):
                sent = await send_styled_http_message(chat.id, text, kb_dict, reply_to_message_id=topic_id)
                if sent:
                    msg_dict[f"{chat.id}:{topic_id}"] = sent
                    continue
            sent = await bot.send_message(
                chat_id=chat.id,
                text=text,
                disable_web_page_preview=True,
                disable_notification=True,
                reply_to_message_id=topic_id,
                reply_markup=buttons,
            )
            msg_dict[f"{chat.id}:{topic_id}"] = sent
        except FloodWait as f:
            LOGGER.warning(str(f))
            await sleep(f.value * 1.2)
            return await sendMultiMessage(chat_ids, text, buttons, photo)
        except Exception as e:
            LOGGER.error(str(e))
    return msg_dict


async def editMessage(message, text, buttons=None, photo=None):
    try:
        if kb_dict := to_bot_api_keyboard(buttons):
            chat_id = message.chat.id
            is_media = bool(message.media or getattr(message, "photo", None))
            http_msg = await edit_styled_http_message(chat_id, message.id, text, kb_dict, is_media)
            if http_msg:
                return http_msg
        if message.media:
            if photo:
                photo = rchoice(config_dict["IMAGES"]) if photo == "IMAGES" else photo
                return await message.edit_media(
                    InputMediaPhoto(photo, text), reply_markup=buttons
                )
            return await message.edit_caption(caption=text, reply_markup=buttons)
        await message.edit(
            text=text, disable_web_page_preview=True, reply_markup=buttons
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await editMessage(message, text, buttons, photo)
    except (MessageNotModified, MessageEmpty):
        pass
    except ReplyMarkupInvalid:
        return await editMessage(message, text, None, photo)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)


async def editReplyMarkup(message, reply_markup):
    try:
        if kb_dict := to_bot_api_keyboard(reply_markup):
            chat_id = message.chat.id
            http_msg = await edit_styled_http_reply_markup(chat_id, message.id, kb_dict)
            if http_msg:
                return http_msg
        return await message.edit_reply_markup(reply_markup=reply_markup)
    except MessageNotModified:
        pass
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)


async def sendFile(message, file, caption=None, buttons=None):
    try:
        return await message.reply_document(
            document=file,
            quote=True,
            caption=caption,
            disable_notification=True,
            reply_markup=buttons,
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await sendFile(message, file, caption)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)


async def sendRss(text):
    try:
        if user:
            return await user.send_message(
                chat_id=config_dict["RSS_CHAT"],
                text=text,
                disable_web_page_preview=True,
                disable_notification=True,
            )
        else:
            return await bot.send_message(
                chat_id=config_dict["RSS_CHAT"],
                text=text,
                disable_web_page_preview=True,
                disable_notification=True,
            )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await sendRss(text)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)


async def deleteMessage(message):
    try:
        await message.delete()
    except Exception as e:
        LOGGER.error(str(e))


async def auto_delete_message(cmd_message=None, bot_message=None):
    if config_dict["AUTO_DELETE_MESSAGE_DURATION"] != -1:
        await sleep(config_dict["AUTO_DELETE_MESSAGE_DURATION"])
        if cmd_message is not None:
            await deleteMessage(cmd_message)
        if bot_message is not None:
            await deleteMessage(bot_message)


async def delete_links(message):
    if config_dict["DELETE_LINKS"]:
        if reply_to := message.reply_to_message:
            await deleteMessage(reply_to)
        await deleteMessage(message)


async def delete_all_messages():
    async with status_reply_dict_lock:
        for key, data in list(status_reply_dict.items()):
            try:
                del status_reply_dict[key]
                await deleteMessage(data[0])
            except Exception as e:
                LOGGER.error(str(e))


async def get_tg_link_content(link, user_id, decrypter=None):
    message = None
    user_sess = user_data.get(user_id, {}).get("usess", "")
    if link.startswith(
        (
            "https://t.me/",
            "https://telegram.me/",
            "https://telegram.dog/",
            "https://telegram.space/",
        )
    ):
        private = False
        msg = re_match(
            r"https:\/\/(t\.me|telegram\.me|telegram\.dog|telegram\.space)\/(?:c\/)?([^\/]+)(?:\/[^\/]+)?\/([0-9]+)",
            link,
        )
    else:
        private = True
        msg = re_match(
            r"tg:\/\/(openmessage)\?user_id=([0-9]+)&message_id=([0-9]+)", link
        )
        if not (user or user_sess):
            raise TgLinkException(
                "USER_SESSION_STRING or Private User Session required for this private link!"
            )

    chat = msg.group(2)
    msg_id = int(msg.group(3))
    if chat.isdigit():
        chat = int(chat) if private else int(f"-100{chat}")

    if not private:
        try:
            message = await bot.get_messages(chat_id=chat, message_ids=msg_id)
            if message.empty:
                private = True
        except Exception as e:
            private = True
            if not (user or user_sess):
                raise e

    if private and user:
        try:
            user_message = await user.get_messages(chat_id=chat, message_ids=msg_id)
            if not user_message.empty:
                return user_message, "user"
        except Exception as e:
            if not user_sess:
                raise TgLinkException(
                    f"Bot User Session  don't have access to this chat!. ERROR: {e}"
                ) from e

    if private and user_sess:
        if decrypter is None:
            return None, ""
        try:
            async with Client(
                user_id,
                session_string=decrypter.decrypt(user_sess).decode(),
                in_memory=True,
                no_updates=True,
            ) as usession:
                user_message = await usession.get_messages(
                    chat_id=chat, message_ids=msg_id
                )
        except InvalidToken:
            raise TgLinkException("Provided Decryption Key is Invalid, Recheck & Retry")
        except Exception as e:
            raise TgLinkException(
                f"User Session don't have access to this chat!. ERROR: {e}"
            ) from e
        if not user_message.empty:
            return user_message, "user_sess"
        else:
            raise TgLinkException("Privatly Deleted or Not Accessible!")
    elif not private:
        return message, "bot"
    else:
        raise TgLinkException(
            "Bot can't download from GROUPS without joining!, Set your Own Session to get access !"
        )


async def update_all_messages(force=False):
    async with status_reply_dict_lock:
        if (
            not status_reply_dict
            or not Interval
            or (not force and time() - list(status_reply_dict.values())[0][1] < 3)
        ):
            return
        for chat_id in list(status_reply_dict.keys()):
            status_reply_dict[chat_id][1] = time()
    async with download_dict_lock:
        msg, buttons = await sync_to_async(get_readable_message)
    if msg is None:
        return
    async with status_reply_dict_lock:
        for chat_id in list(status_reply_dict.keys()):
            if status_reply_dict[chat_id] and msg != status_reply_dict[chat_id][0].text:
                rmsg = await editMessage(
                    status_reply_dict[chat_id][0], msg, buttons, "IMAGES"
                )
                if isinstance(rmsg, str) and rmsg.startswith("Telegram says: [400"):
                    del status_reply_dict[chat_id]
                    continue
                status_reply_dict[chat_id][0].text = msg
                status_reply_dict[chat_id][1] = time()


async def sendStatusMessage(msg):
    async with download_dict_lock:
        progress, buttons = await sync_to_async(get_readable_message)
    if progress is None:
        return
    async with status_reply_dict_lock:
        chat_id = msg.chat.id
        if chat_id in list(status_reply_dict.keys()):
            message = status_reply_dict[chat_id][0]
            await deleteMessage(message)
            del status_reply_dict[chat_id]
        if message := await sendMessage(msg, progress, buttons, photo="IMAGES"):
            if hasattr(message, "caption"):
                message.caption = progress
            else:
                message.text = progress
        status_reply_dict[chat_id] = [message, time()]
        if not Interval:
            Interval.append(
                setInterval(config_dict["STATUS_UPDATE_INTERVAL"], update_all_messages)
            )


async def open_category_btns(message):
    user_id = message.from_user.id
    msg_id = message.id
    buttons = ButtonMaker()
    _tick = True
    if len(utds := await fetch_user_tds(user_id)) > 1:
        for _name in utds.keys():
            buttons.ibutton(
                f'{"✅️" if _tick else ""} {_name}',
                f"scat {user_id} {msg_id} {_name.replace(' ', '_')}",
            )
            if _tick:
                _tick, cat_name = False, _name
    elif len(categories_dict) > 1:
        for _name in categories_dict.keys():
            buttons.ibutton(
                f'{"✅️" if _tick else ""} {_name}',
                f"scat {user_id} {msg_id} {_name.replace(' ', '_')}",
            )
            if _tick:
                _tick, cat_name = False, _name
    buttons.ibutton("Cancel", f"scat {user_id} {msg_id} scancel", "footer")
    buttons.ibutton(f"Done (60)", f"scat {user_id} {msg_id} sdone", "footer")
    prompt = await sendMessage(
        message,
        f"<b>Select the category where you want to upload</b>\n\n<i><b>Upload Category:</b></i> <code>{cat_name}</code>\n\n<b>Timeout:</b> 60 sec",
        buttons.build_menu(3),
    )
    start_time = time()
    bot_cache[msg_id] = [None, None, False, False, start_time]
    while time() - start_time <= 60:
        await sleep(0.5)
        if bot_cache[msg_id][2] or bot_cache[msg_id][3]:
            break
    drive_id, index_link, _, is_cancelled, __ = bot_cache[msg_id]
    if not is_cancelled:
        await deleteMessage(prompt)
    else:
        await editMessage(prompt, "<b>Task Cancelled</b>")
    del bot_cache[msg_id]
    return drive_id, index_link, is_cancelled


async def open_dump_btns(message):
    user_id = message.from_user.id
    msg_id = message.id
    buttons = ButtonMaker()
    _tick = True
    if len(udmps := await fetch_user_dumps(user_id)) > 1:
        for _name in udmps.keys():
            buttons.ibutton(
                f'{"✅️" if _tick else ""} {_name}',
                f"dcat {user_id} {msg_id} {_name.replace(' ', '_')}",
            )
            if _tick:
                _tick, cat_name = False, _name
    buttons.ibutton("Upload in All", f"dcat {user_id} {msg_id} All", "header")
    buttons.ibutton("Cancel", f"dcat {user_id} {msg_id} dcancel", "footer")
    buttons.ibutton(f"Done (60)", f"dcat {user_id} {msg_id} ddone", "footer")
    prompt = await sendMessage(
        message,
        f"<b>Select the Dump category where you want to upload</b>\n\n<i><b>Upload Category:</b></i> <code>{cat_name}</code>\n\n<b>Timeout:</b> 60 sec",
        buttons.build_menu(3),
    )
    start_time = time()
    bot_cache[msg_id] = [None, False, False, start_time]
    while time() - start_time <= 60:
        await sleep(0.5)
        if bot_cache[msg_id][1] or bot_cache[msg_id][2]:
            break
    dump_chat, _, is_cancelled, __ = bot_cache[msg_id]
    if not is_cancelled:
        await deleteMessage(prompt)
    else:
        await editMessage(prompt, "<b>Task Cancelled</b>")
    del bot_cache[msg_id]
    return dump_chat, is_cancelled


async def forcesub(message, ids, button=None):
    join_button = {}
    _msg = ""
    for channel_id in ids.split():
        chat = await chat_info(channel_id)
        try:
            await chat.get_member(message.from_user.id)
        except UserNotParticipant:
            if username := chat.username:
                invite_link = f"https://t.me/{username}"
            else:
                invite_link = chat.invite_link
            join_button[chat.title] = invite_link
        except RPCError as e:
            LOGGER.error(f"{e.NAME}: {e.MESSAGE} for {channel_id}")
        except Exception as e:
            LOGGER.error(f"{e} for {channel_id}")
    if join_button:
        if button is None:
            button = ButtonMaker()
        _msg = "You haven't joined our channel yet!"
        for key, value in join_button.items():
            button.ubutton(f"Join {key}", value, "footer")
    return _msg, button


async def user_info(user_id):
    try:
        return await bot.get_users(user_id)
    except Exception:
        return ""


async def check_botpm(message, button=None):
    try:
        temp_msg = await message._client.send_message(
            chat_id=message.from_user.id, text="<b>Checking Access...</b>"
        )
        await deleteMessage(temp_msg)
        return None, button
    except Exception:
        if button is None:
            button = ButtonMaker()
        _msg = "<i>You didn't START the bot in PM (Private)</i>"
        button.ubutton(
            "Start Bot Now", f"https://t.me/{bot_name}?start=start", "header"
        )
        return _msg, button


class MentionStr(str):
    def __call__(self, *args, **kwargs):
        return str(self)


class CustomUser:
    def __init__(self, uid, uname, fname, m, client=None):
        self.id = uid
        self.username = uname
        self.first_name = fname
        self.last_name = ""
        self.mention = m if isinstance(m, MentionStr) else MentionStr(m)
        self.is_bot = False
        self._client = client


def parse_tag_info(text, bot_uname=None):
    if not text:
        return "", "", ""
    tag = ""
    id_ = ""
    cleaned = text
    bot_n = (bot_uname or bot_name or "").lower()

    # Case 1: Explicit 'Tag:' (case insensitive)
    # Matches 'Tag: @user 123', 'Tag:@user 123', 'Tag: 123', 'Tag: @user', etc.
    m = re_search(r"(?i)(?:^|[\s\n])tag:\s*([^\s\n]+)(?:\s+(-?\d+))?", text)
    if m:
        first = m.group(1).strip()
        second = m.group(2).strip() if m.group(2) else ""
        cleaned = text[: m.start()] + text[m.end() :]
        if first.startswith("@"):
            tag = first
            id_ = second
        elif first.lstrip("-").isdigit():
            id_ = first
            tag = ""
        else:
            tag = first
            id_ = second
        return tag, id_, cleaned.strip()

    # Case 2: Multi-line where line 2 is @user [id] or just id
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if len(lines) > 1:
        line2 = lines[1]
        m2 = re_match(r"^(@[A-Za-z0-9_]+)(?:\s+(-?\d+))?$", line2)
        if m2 and (not bot_n or m2.group(1).lstrip("@").lower() != bot_n):
            tag = m2.group(1)
            id_ = m2.group(2) or ""
            cleaned = "\n".join([lines[0]] + lines[2:])
            return tag, id_, cleaned.strip()
        m_id = re_match(r"^(-?\d{6,14})$", line2)
        if m_id:
            id_ = m_id.group(1)
            cleaned = "\n".join([lines[0]] + lines[2:])
            return tag, id_, cleaned.strip()

    # Case 3: Inline @username [id]
    m3 = re_search(r"(?:^|\s)(@[A-Za-z0-9_]+)(?:\s+(-?\d{6,14}))?(?:\s|$)", text)
    if m3 and (not bot_n or m3.group(1).lstrip("@").lower() != bot_n):
        prefix = text[: m3.start()].strip()
        if not prefix.endswith(("-u", "-user")):
            tag = m3.group(1)
            id_ = m3.group(2) or ""
            cleaned = text[: m3.start()] + " " + text[m3.end() :]
            return tag, id_, re_sub(r"\s+", " ", cleaned).strip()

    # Case 4: Pure numeric ID at end of command (e.g. /lx 7995560265 or /lx <link> 7995560265)
    m4 = re_search(r"(?:^|\s)(-?\d{6,14})(?:\s|$)", text)
    if m4:
        prefix = text[: m4.start()].strip()
        flags = ("-i", "-ss", "-screenshots", "-ud", "-dump", "-c", "-category", "-id")
        if not any(prefix.endswith(f) for f in flags):
            id_ = m4.group(1)
            cleaned = text[: m4.start()] + " " + text[m4.end() :]
            return tag, id_, re_sub(r"\s+", " ", cleaned).strip()

    return tag, id_, cleaned.strip()


async def get_tagged_user(client, tag="", id_="", fallback_user=None):
    try:
        if fallback_user is None and not isinstance(id_, (int, str)):
            fallback_user = id_
            id_ = ""
        if tag and (tag.startswith("Tag: ") or "tag:" in tag.lower() or "\n" in tag):
            t, i, _ = parse_tag_info(tag, bot_name)
            if t or i:
                tag, id_ = t, i

        if not id_ and tag and tag.lstrip("-").isdigit():
            id_ = tag
            tag = ""

        user_id = int(id_) if id_ and str(id_).lstrip("-").isdigit() else None
        user = None

        if user_id:
            try:
                user = await client.get_users(user_id)
            except Exception:
                pass

        if not user and tag and tag.startswith("@"):
            try:
                user = await client.get_users(tag)
                if user:
                    user_id = user.id
            except Exception:
                pass

        if user:
            user_id = user.id
            user._client = client
        elif user_id or tag:
            user_id = user_id or (fallback_user.id if fallback_user else 0)
            clean_name = tag.lstrip("@") if tag else str(user_id)
            username = clean_name if tag.startswith("@") else None
            mention_text = tag if tag.startswith("@") else f'<a href="tg://user?id={user_id}">{clean_name}</a>'
            user = CustomUser(user_id, username, clean_name, MentionStr(mention_text), client)
        else:
            return fallback_user

        if user_id:
            try:
                from bot.helper.ext_utils.db_handler import DbManger
                db_data = await DbManger().get_user_data(user_id)
                if db_data:
                    LOGGER.info(f"Loaded user settings from DB for tagged user {user_id}")
            except Exception as ex:
                LOGGER.error(f"Error loading user_data for {user_id}: {ex}")
            user_data.setdefault(user_id, {})

        return user
    except Exception as e:
        LOGGER.error(f"Failed to resolve tagged user: {e}")
        return fallback_user
