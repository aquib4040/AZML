from bot import bot, LOGGER
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.scraper_utils import scrape_url, get_supported_platforms
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command


async def scrape_command(client, message):
    """
    Universal scraper command for streaming platforms and social media.
    Usage: /scrape <url> or /sc <url>
    """
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        platforms = get_supported_platforms()
        platform_list = ", ".join(platforms[:10]) + f"... and {len(platforms)-10} more"
        
        await sendMessage(
            message,
            "<b>🔍 Universal Scraper</b>\n\n"
            "<b>Usage:</b> <code>/scrape &lt;url&gt;</code>\n\n"
            f"<b>Supported Platforms ({len(platforms)}):</b>\n"
            f"<code>{platform_list}</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/scrape https://zee5.com/...</code>\n"
            "• <code>/scrape https://youtube.com/watch?v=...</code>\n"
            "• <code>/scrape https://crunchyroll.com/series/...</code>\n\n"
            "<i>Automatically detects platform and extracts metadata/download links!</i>"
        )
        return
    
    url = args[1].strip()
    
    if not url.startswith("http"):
        await sendMessage(message, "❌ <b>Invalid URL!</b> Please provide a valid URL starting with http:// or https://")
        return
    
    status_msg = await sendMessage(message, "🔄 <b>Scraping...</b>")
    
    try:
        result = await scrape_url(url)
        
        if not result:
            await editMessage(
                status_msg,
                "❌ <b>Failed to scrape!</b>\n\n"
                "Possible reasons:\n"
                "• Platform not supported\n"
                "• Invalid URL\n"
                "• Content not available\n"
                "• API error"
            )
            return
        
        # Format response
        response = f"<b>🎬 {result['platform']}</b>\n\n"
        
        if result.get('title'):
            response += f"<b>Title:</b> {result['title']}\n"
        
        if result.get('type'):
            response += f"<b>Type:</b> {result['type'].capitalize()}\n"
        
        if result.get('year'):
            response += f"<b>Year:</b> {result['year']}\n"
        
        if result.get('duration'):
            response += f"<b>Duration:</b> {result['duration']}\n"
        
        if result.get('quality'):
            response += f"<b>Quality:</b> {result['quality']}\n"
        
        if result.get('thumbnail'):
            response += f"\n<b>📸 Thumbnail/Portrait:</b>\n<code>{result['thumbnail']}</code>\n"
        
        if result.get('landscape'):
            response += f"\n<b>🖼️ Landscape:</b>\n<code>{result['landscape']}</code>\n"
        elif result.get('poster'):
            response += f"\n<b>🖼️ Poster:</b>\n<code>{result['poster']}</code>\n"
        
        if result.get('download_links'):
            response += f"\n<b>📥 Download Links ({len(result['download_links'])}):</b>\n"
            for idx, link in enumerate(result['download_links'][:5], 1):  # Show max 5 links
                short_link = link[:80] + "..." if len(link) > 80 else link
                response += f"{idx}. <code>{short_link}</code>\n"
            
            if len(result['download_links']) > 5:
                response += f"\n<i>...and {len(result['download_links']) - 5} more links</i>"
        
        # Edit the status message with final result
        await editMessage(status_msg, response)
        LOGGER.info(f"[SCRAPER] Successfully scraped {result['platform']}: {result.get('title', 'Unknown')}")
        
    except Exception as e:
        LOGGER.error(f"[SCRAPER] Command error: {str(e)}")
        await editMessage(
            status_msg,
            f"❌ <b>Error:</b>\n<code>{str(e)}</code>"
        )


bot.add_handler(
    MessageHandler(
        scrape_command,
        filters=command(BotCommands.ScrapeCommand)
        & CustomFilters.authorized
        & ~CustomFilters.blacklisted,
    )
)
