import re
from time import time
from datetime import datetime, timezone
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command, regex

from bot import user_data, DATABASE_URL, bot, LOGGER
from bot.helper.telegram_helper.message_utils import sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.bot_utils import update_user_ldata, get_readable_time, is_premium_user


async def authorize(client, message):
    msg = message.text.split()
    tid_ = ""
    if len(msg) > 1:
        nid_ = msg[1].split(":")
        id_ = int(nid_[0])
        if len(nid_) > 1:
            tid_ = int(nid_[1])
    elif (reply_to := message.reply_to_message) and (
        reply_to.text is None and reply_to.caption is None
    ):
        id_ = message.chat.id
        tid_ = message.reply_to_message_id
    elif reply_to:
        id_ = reply_to.from_user.id
    else:
        id_ = message.chat.id
    if id_ in user_data and user_data[id_].get("is_auth"):
        msg = "Already Authorized!"
        if tid_:
            if tid_ not in (tids_ := user_data[id_].get("topic_ids", [])):
                tids_.append(tid_)
                update_user_ldata(id_, "topic_ids", tids_)
                if DATABASE_URL:
                    await DbManger().update_user_data(id_)
                msg = "Topic Authorized!"
            else:
                msg = "Topic Already Authorized!"
    else:
        update_user_ldata(id_, "is_auth", True)
        if tid_:
            update_user_ldata(id_, "topic_ids", [tid_])
            msg = "Topic Authorized!"
        else:
            msg = "Authorized"
        if DATABASE_URL:
            await DbManger().update_user_data(id_)
    await sendMessage(message, msg)


async def unauthorize(client, message):
    msg = message.text.split()
    tid_ = ""
    if len(msg) > 1:
        nid_ = msg[1].split(":")
        id_ = int(nid_[0])
        if len(nid_) > 1:
            tid_ = int(nid_[1])
    elif (reply_to := message.reply_to_message) and (
        reply_to.text is None and reply_to.caption is None
    ):
        id_ = message.chat.id
        tid_ = message.reply_to_message_id
    elif reply_to := message.reply_to_message:
        id_ = reply_to.from_user.id
    else:
        id_ = message.chat.id
    tids_ = []
    if (
        tid_
        and id_ in user_data
        and tid_ in (tids_ := user_data[id_].get("topic_ids", []))
    ):
        tids_.remove(tid_)
        update_user_ldata(id_, "topic_ids", tids_)
    if id_ not in user_data or user_data[id_].get("is_auth"):
        if not tids_:
            update_user_ldata(id_, "is_auth", False)
        if DATABASE_URL:
            await DbManger().update_user_data(id_)
        msg = "Unauthorized"
    else:
        msg = "Already Unauthorized!"
    await sendMessage(message, msg)


async def addSudo(client, message):
    id_ = ""
    msg = message.text.split()
    if len(msg) > 1:
        id_ = int(msg[1].strip())
    elif reply_to := message.reply_to_message:
        id_ = reply_to.from_user.id
    if id_:
        if id_ in user_data and user_data[id_].get("is_sudo"):
            msg = "Already Sudo!"
        else:
            update_user_ldata(id_, "is_sudo", True)
            if DATABASE_URL:
                await DbManger().update_user_data(id_)
            msg = "Promoted as Sudo"
    else:
        msg = "<i>Give User's ID or Reply to User's message of whom you want to Promote as Sudo</i>"
    await sendMessage(message, msg)


async def removeSudo(client, message):
    id_ = ""
    msg = message.text.split()
    if len(msg) > 1:
        id_ = int(msg[1].strip())
    elif reply_to := message.reply_to_message:
        id_ = reply_to.from_user.id
    if id_:
        if id_ in user_data and not user_data[id_].get("is_sudo"):
            msg = "Not a Sudo User, Already Demoted"
        else:
            update_user_ldata(id_, "is_sudo", False)
            if DATABASE_URL:
                await DbManger().update_user_data(id_)
            msg = "Demoted"
    else:
        msg = "<i>Give User's ID or Reply to User's message of whom you want to Demote</i>"
    await sendMessage(message, msg)


async def addBlackList(_, message):
    id_ = ""
    msg = message.text.split()
    if len(msg) > 1:
        id_ = int(msg[1].strip())
    elif reply_to := message.reply_to_message:
        id_ = reply_to.from_user.id
    if id_:
        if id_ in user_data and user_data[id_].get("is_blacklist"):
            msg = "User Already BlackListed!"
        else:
            update_user_ldata(id_, "is_blacklist", True)
            if DATABASE_URL:
                await DbManger().update_user_data(id_)
            msg = "User BlackListed"
    else:
        msg = "Give ID or Reply To message of whom you want to blacklist."
    await sendMessage(message, msg)


async def rmBlackList(_, message):
    id_ = ""
    msg = message.text.split()
    if len(msg) > 1:
        id_ = int(msg[1].strip())
    elif reply_to := message.reply_to_message:
        id_ = reply_to.from_user.id
    if id_:
        if id_ in user_data and not user_data[id_].get("is_blacklist"):
            msg = "<i>User Already Freed</i>"
        else:
            update_user_ldata(id_, "is_blacklist", False)
            if DATABASE_URL:
                await DbManger().update_user_data(id_)
            msg = "<i>User Set Free as Bird!</i>"
    else:
        msg = "Give ID or Reply To message of whom you want to remove from blacklisted"
    await sendMessage(message, msg)


async def black_listed(_, message):
    await sendMessage(message, "<i>BlackListed Detected, Restricted from Bot</i>")


TIME_UNITS = {
    "s": 1, "sec": 1, "secs": 1, "second": 1, "seconds": 1,
    "min": 60, "mins": 60, "minute": 60, "minutes": 60,
    "h": 3600, "hr": 3600, "hrs": 3600, "hour": 3600, "hours": 3600,
    "d": 86400, "day": 86400, "days": 86400,
    "w": 7 * 86400, "week": 7 * 86400, "weeks": 7 * 86400,
    "m": 30 * 86400, "mo": 30 * 86400, "month": 30 * 86400, "months": 30 * 86400,
    "y": 365 * 86400, "yr": 365 * 86400, "yrs": 365 * 86400, "year": 365 * 86400, "years": 365 * 86400,
}


def parse_premium_args(message):
    reply_to = message.reply_to_message
    reply_id = None
    if reply_to:
        reply_id = reply_to.from_user.id if reply_to.from_user else reply_to.sender_chat.id if reply_to.sender_chat else None

    words = message.text.split()
    args_str = " ".join(words[1:]) if len(words) > 1 else ""

    total_seconds = 0
    pattern = r"(\d+)\s*([a-zA-Z]+)"
    consumed_spans = []
    for m in re.finditer(pattern, args_str):
        val = int(m.group(1))
        unit = m.group(2).lower()
        if unit in TIME_UNITS:
            total_seconds += val * TIME_UNITS[unit]
            consumed_spans.append((m.start(), m.end()))

    remaining = ""
    last_end = 0
    for start, end in consumed_spans:
        remaining += args_str[last_end:start] + " "
        last_end = end
    remaining += args_str[last_end:]
    remaining_tokens = remaining.strip().split()

    target_id = None
    if reply_id:
        target_id = reply_id
        if remaining_tokens:
            if len(remaining_tokens) == 1 and remaining_tokens[0].isdigit() and total_seconds == 0:
                total_seconds = int(remaining_tokens[0]) * 86400
            elif len(remaining_tokens) >= 1 and remaining_tokens[0].isdigit():
                target_id = int(remaining_tokens[0])
                if len(remaining_tokens) > 1 and remaining_tokens[1].isdigit() and total_seconds == 0:
                    total_seconds = int(remaining_tokens[1]) * 86400
    else:
        if remaining_tokens:
            if remaining_tokens[0].isdigit():
                target_id = int(remaining_tokens[0])
                if len(remaining_tokens) > 1 and remaining_tokens[1].isdigit() and total_seconds == 0:
                    total_seconds = int(remaining_tokens[1]) * 86400
            elif remaining_tokens[0].lstrip("-").isdigit():
                target_id = int(remaining_tokens[0])

    return target_id, total_seconds


async def addPremium(client, message):
    target_id, duration = parse_premium_args(message)
    if not target_id:
        msg = (
            "<i>Give User's ID or Reply to User's message of whom you want to add Premium!</i>\n\n"
            "<b>Usage:</b>\n"
            "• <code>/addpremium 30 d</code> (replying to user)\n"
            "• <code>/addpremium 1 y</code> (replying to user)\n"
            "• <code>/addpremium 2 m</code> (replying to user)\n"
            "• <code>/addpremium &lt;user_id&gt; 30 d</code>\n"
            "• <code>/addpremium &lt;user_id&gt; 1 y</code>\n"
            "• <code>/addpremium &lt;user_id&gt; 2 m</code>\n"
            "• <code>/addpremium &lt;user_id&gt; 30 d 1 y 2 m</code>"
        )
        return await sendMessage(message, msg)

    if duration <= 0:
        msg = (
            "<i>Please provide a valid duration for Premium!</i>\n\n"
            "<b>Examples:</b>\n"
            "• <code>30 d</code> (30 days)\n"
            "• <code>1 y</code> (1 year)\n"
            "• <code>2 m</code> (2 months)\n"
            "• <code>30 d 1 y 2 m</code> (cumulative)"
        )
        return await sendMessage(message, msg)

    user_dict = user_data.setdefault(target_id, {})
    curr_expiry = user_dict.get("expiry_time", 0)
    now = time()
    if curr_expiry and curr_expiry > now:
        new_expiry = curr_expiry + duration
    else:
        new_expiry = now + duration

    update_user_ldata(target_id, "is_premium", True)
    update_user_ldata(target_id, "expiry_time", new_expiry)
    if DATABASE_URL:
        await DbManger().update_user_data(target_id)

    time_added_str = get_readable_time(duration)
    total_time_str = get_readable_time(new_expiry - now)
    expiry_date = datetime.fromtimestamp(new_expiry, tz=timezone.utc).strftime("%d-%b-%Y %H:%M:%S UTC")

    reply_to = message.reply_to_message
    mention = f" {reply_to.from_user.mention(style='html')}" if reply_to and reply_to.from_user and reply_to.from_user.id == target_id else ""

    msg = (
        f"🌟 <b>Premium Added Successfully!</b>\n\n"
        f"👤 <b>User:</b>{mention} <code>{target_id}</code>\n"
        f"⏳ <b>Time Added:</b> <code>{time_added_str}</code>\n"
        f"⏱ <b>Total Time Remaining:</b> <code>{total_time_str}</code>\n"
        f"📅 <b>Expires On:</b> <code>{expiry_date}</code>\n\n"
        f"<i>This user can now use the bot without token verification!</i>"
    )
    await sendMessage(message, msg)


async def removePremium(client, message):
    id_ = ""
    msg = message.text.split()
    if len(msg) > 1 and msg[1].strip().lstrip("-").isdigit():
        id_ = int(msg[1].strip())
    elif (reply_to := message.reply_to_message) and reply_to.from_user:
        id_ = reply_to.from_user.id
    elif reply_to and reply_to.sender_chat:
        id_ = reply_to.sender_chat.id

    if id_:
        user_dict = user_data.get(id_, {})
        if not user_dict.get("is_premium"):
            msg = f"<b>User <code>{id_}</code> is not a Premium User!</b>"
        else:
            update_user_ldata(id_, "is_premium", False)
            update_user_ldata(id_, "expiry_time", 0)
            if DATABASE_URL:
                await DbManger().update_user_data(id_)
            msg = f"🚫 <b>Premium Removed for User:</b> <code>{id_}</code>"
    else:
        msg = (
            "<i>Give User's ID or Reply to User's message of whom you want to Remove Premium</i>\n"
            "<b>Usage:</b> <code>/rmpremium [user_id]</code> or reply with <code>/rmpremium</code>"
        )
    await sendMessage(message, msg)


async def checkPremium(client, message):
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    msg_args = message.text.split()
    is_sudo = await CustomFilters.sudo(client, message)
    target_id = user_id
    if len(msg_args) > 1 and msg_args[1].strip().lstrip("-").isdigit() and is_sudo:
        target_id = int(msg_args[1].strip())
    elif (reply_to := message.reply_to_message) and is_sudo:
        target_id = reply_to.from_user.id if reply_to.from_user else reply_to.sender_chat.id if reply_to.sender_chat else target_id

    user_dict = user_data.get(target_id, {})
    if is_premium_user(target_id):
        expiry = user_dict.get("expiry_time", 0)
        now = time()
        if expiry and expiry > now:
            remaining = get_readable_time(expiry - now)
            expiry_date = datetime.fromtimestamp(expiry, tz=timezone.utc).strftime("%d-%b-%Y %H:%M:%S UTC")
            msg = (
                f"👑 <b>Premium User Status:</b>\n\n"
                f"👤 <b>User ID:</b> <code>{target_id}</code>\n"
                f"✅ <b>Status:</b> <code>Active</code>\n"
                f"⏱ <b>Remaining:</b> <code>{remaining}</code>\n"
                f"📅 <b>Expires On:</b> <code>{expiry_date}</code>\n\n"
                f"<i>Token verification is disabled for this user.</i>"
            )
        else:
            msg = (
                f"👑 <b>Premium User Status:</b>\n\n"
                f"👤 <b>User ID:</b> <code>{target_id}</code>\n"
                f"✅ <b>Status:</b> <code>Lifetime Active</code>\n\n"
                f"<i>Token verification is disabled for this user.</i>"
            )
    else:
        msg = (
            f"👑 <b>Premium User Status:</b>\n\n"
            f"👤 <b>User ID:</b> <code>{target_id}</code>\n"
            f"❌ <b>Status:</b> <code>Not Premium / Expired</code>"
        )
    await sendMessage(message, msg)


bot.add_handler(
    MessageHandler(
        authorize, filters=command(BotCommands.AuthorizeCommand) & CustomFilters.sudo
    )
)
bot.add_handler(
    MessageHandler(
        unauthorize,
        filters=command(BotCommands.UnAuthorizeCommand) & CustomFilters.sudo,
    )
)
bot.add_handler(
    MessageHandler(
        addSudo, filters=command(BotCommands.AddSudoCommand) & CustomFilters.sudo
    )
)
bot.add_handler(
    MessageHandler(
        removeSudo, filters=command(BotCommands.RmSudoCommand) & CustomFilters.sudo
    )
)
bot.add_handler(
    MessageHandler(
        addPremium,
        filters=command(BotCommands.AddPremiumCommand) & CustomFilters.sudo,
    )
)
bot.add_handler(
    MessageHandler(
        removePremium,
        filters=command(BotCommands.RmPremiumCommand) & CustomFilters.sudo,
    )
)
bot.add_handler(
    MessageHandler(
        checkPremium,
        filters=command(BotCommands.PremiumCommand) & CustomFilters.authorized,
    )
)
bot.add_handler(
    MessageHandler(
        addBlackList,
        filters=command(BotCommands.AddBlackListCommand) & CustomFilters.sudo,
    )
)
bot.add_handler(
    MessageHandler(
        rmBlackList,
        filters=command(BotCommands.RmBlackListCommand) & CustomFilters.sudo,
    )
)
bot.add_handler(
    MessageHandler(
        black_listed,
        filters=regex(r"^/") & CustomFilters.authorized & CustomFilters.blacklisted,
    )
)
