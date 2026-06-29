#!/usr/bin/env python3
import asyncio
from pyrogram import Client
from bot import TELEGRAM_API, TELEGRAM_HASH, LOGGER

class PersonalBotManager:
    _instance = None
    _lock = asyncio.Lock()

    def __init__(self):
        self.clients = {}  # {user_id: pyrogram.Client}
        self._starting = set()  # {user_id}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def get_client(self, user_id, bot_token):
        if user_id in self.clients:
            client = self.clients[user_id]
            if client.is_connected:
                return client
            else:
                try:
                    await client.start()
                    return client
                except Exception as e:
                    LOGGER.error(f"Failed to start cached personal bot for {user_id}: {e}")
                    self.clients.pop(user_id, None)

        while user_id in self._starting:
            await asyncio.sleep(0.5)
            if user_id in self.clients:
                return self.clients[user_id]

        self._starting.add(user_id)
        try:
            LOGGER.info(f"Starting personal upload bot client for user {user_id}")
            client = Client(
                name=f"personal_bot_{user_id}",
                api_id=TELEGRAM_API,
                api_hash=TELEGRAM_HASH,
                bot_token=bot_token,
                in_memory=True,
                no_updates=True
            )
            await client.start()
            self.clients[user_id] = client
            return client
        except Exception as e:
            LOGGER.error(f"Failed to start personal upload bot client for user {user_id}: {e}")
            raise e
        finally:
            self._starting.discard(user_id)

    async def stop_client(self, user_id):
        client = self.clients.pop(user_id, None)
        if client:
            try:
                await client.stop()
                LOGGER.info(f"Stopped personal upload bot client for user {user_id}")
            except Exception as e:
                LOGGER.error(f"Error stopping personal bot for {user_id}: {e}")

async def verify_personal_bot(bot_token):
    temp_client = Client(
        "verify_bot",
        api_id=TELEGRAM_API,
        api_hash=TELEGRAM_HASH,
        bot_token=bot_token,
        in_memory=True,
        no_updates=True
    )
    try:
        await temp_client.start()
        me = await temp_client.get_me()
        username = me.username
        await temp_client.stop()
        return True, username
    except Exception as e:
        try:
            await temp_client.stop()
        except:
            pass
        return False, str(e)

async def verify_personal_dump(bot_token, dump_chat_id):
    # Parse dump_chat_id
    if isinstance(dump_chat_id, str):
        if dump_chat_id.startswith("-100"):
            try:
                chat_id = int(dump_chat_id)
            except ValueError:
                chat_id = dump_chat_id
        elif dump_chat_id.startswith("-") or dump_chat_id.isdigit():
            try:
                chat_id = int(dump_chat_id)
            except ValueError:
                chat_id = dump_chat_id
        else:
            chat_id = dump_chat_id
    else:
        chat_id = dump_chat_id

    temp_client = Client(
        "verify_dump",
        api_id=TELEGRAM_API,
        api_hash=TELEGRAM_HASH,
        bot_token=bot_token,
        in_memory=True,
        no_updates=True
    )
    try:
        await temp_client.start()
        test_msg = await temp_client.send_message(
            chat_id=chat_id,
            text="✨ Personal Upload Bot Verification Message. This will be deleted shortly.",
            disable_notification=True
        )
        await temp_client.delete_messages(chat_id=chat_id, message_ids=test_msg.id)
        await temp_client.stop()
        return True, "Permissions verified successfully!"
    except Exception as e:
        try:
            await temp_client.stop()
        except:
            pass
        return False, str(e)
