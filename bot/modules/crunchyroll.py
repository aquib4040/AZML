#!/usr/bin/env python3
from curl_cffi import requests

from bot import bot, LOGGER
from bot.helper.telegram_helper.message_utils import sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command


class Crunchyroll:
    def __init__(self):
        self.headers = None
        self.session = requests.Session(impersonate="firefox")
        self.bearer = self.get_token()

    def get_token(self):
        self.headers = {
            "Authorization": "Basic Y3Jfd2ViOg=="
        }
        r = self.session.post(
            "https://www.crunchyroll.com/auth/v1/token",
            headers=self.headers,
            data={"grant_type": "client_id"}
        )
        return r.json()["access_token"]

    def parse_data(self, data):
        self.data = {}
        self.data["title"] = f"{data.get('title')} - {data.get('series_launch_year')}"
        self.data["landscape"] = data["images"]["poster_wide"][0][-1]["source"]
        self.data["portrait"] = data["images"]["poster_tall"][0][-1]["source"]

    def get_poster(self, url):
        self.cid = url.split("/")[4]
        self.headers = {
            "Authorization": f"Bearer {self.bearer}"
        }
        res = self.session.get(
            f"https://www.crunchyroll.com/content/v2/cms/series/{self.cid}?locale=en-US",
            headers=self.headers
        )
        self.parse_data(res.json()["data"][0])
        return self.data


async def crunchyroll_poster(client, message):
    """
    Fetch Crunchyroll series poster and backdrop links.
    Usage: /cr <crunchyroll_series_url>
    """
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await sendMessage(
            message,
            "<b>Usage:</b> <code>/cr &lt;crunchyroll_series_url&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/cr https://www.crunchyroll.com/series/GG5H5XQX4/frieren-beyond-journeys-end</code>"
        )
        return
    
    url = args[1].strip()
    
    # Validate Crunchyroll URL
    if not url.startswith("https://www.crunchyroll.com/series/"):
        await sendMessage(
            message,
            "❌ Invalid URL! Please provide a valid Crunchyroll series URL.\n\n"
            "<b>Example:</b>\n"
            "<code>https://www.crunchyroll.com/series/GG5H5XQX4/frieren-beyond-journeys-end</code>"
        )
        return
    
    try:
        cr = Crunchyroll()
        data = cr.get_poster(url)
        
        response = (
            f"<b>📺 {data['title']}</b>\n\n"
            f"<b>🖼️ Landscape Poster:</b>\n"
            f"<code>{data['landscape']}</code>\n\n"
            f"<b>🎬 Portrait Poster:</b>\n"
            f"<code>{data['portrait']}</code>"
        )
        
        await sendMessage(message, response)
        LOGGER.info(f"Crunchyroll poster fetched for: {data['title']}")
        
    except Exception as e:
        LOGGER.error(f"Crunchyroll error: {str(e)}")
        await sendMessage(
            message,
            f"❌ <b>Error fetching poster:</b>\n<code>{str(e)}</code>\n\n"
            "Make sure the URL is correct and the series exists on Crunchyroll."
        )


bot.add_handler(
    MessageHandler(
        crunchyroll_poster,
        filters=command(BotCommands.CrunchyrollCommand)
        & CustomFilters.authorized
        & ~CustomFilters.blacklisted,
    )
)
