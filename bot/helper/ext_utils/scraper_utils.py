#!/usr/bin/env python3
from aiohttp import ClientSession
from bot import LOGGER


# Domain to API endpoint mapping
SCRAPER_APIS = {
    # Streaming Platforms
    "zee5.com": "https://zee5.the-zake.workers.dev/?url=",
    "apple.com": "https://appletv.the-zake.workers.dev/?url=",
    "airtelxstream.in": "https://airtelxstream.the-zake.workers.dev/?url=",
    "sunnxt.com": "https://sunnxt.the-zake.workers.dev/?url=",
    "aha.video": "https://ahavideo.the-zake.workers.dev/?url=",
    "iqiyi.com": "https://iqiyi.the-zake.workers.dev/?url=",
    "wetv.vip": "https://wetv.the-zake.workers.dev/?url=",
    "shemaroome.com": "https://shemaroo.the-zake.workers.dev/?url=",
    "bookmyshow.com": "https://bookmyshow.the-zake.workers.dev/?url=",
    "plex.tv": "https://plextv.the-zake.workers.dev/?url=",
    "addatimes.com": "https://addatimes.the-zake.workers.dev/?url=",
    "stage.in": "https://stage.the-zake.workers.dev/?url=",
    "netflix.com": "https://netflix.the-zake.workers.dev/?url=",
    "mxplayer.in": "https://mxplayer.the-zake.workers.dev/?url=",
    "primevideo.com": "https://primevideo.pbx1bots.workers.dev/?url=",
    "amazon.com/prime": "https://primevideo.pbx1bots.workers.dev/?url=",
    
    # Social Media
    "youtube.com": "https://youtubedl.the-zake.workers.dev/?url=",
    "youtu.be": "https://youtubedl.the-zake.workers.dev/?url=",
    "instagram.com": "https://instagramdl.the-zake.workers.dev/?url=",
    "facebook.com": "https://facebookdl.the-zake.workers.dev/?url=",
    "tiktok.com": "https://tiktokdl.the-zake.workers.dev/?url=",
    
    # Anime/Crunchyroll - uses different format
    "crunchyroll.com": "CRUNCHYROLL_API",
}


def detect_platform(url):
    """
    Detect which platform a URL belongs to.
    
    Args:
        url: URL to check
        
    Returns:
        Tuple of (platform_name, api_endpoint) or (None, None)
    """
    if not url:
        return None, None
    
    url_lower = url.lower()
    
    for domain, api in SCRAPER_APIS.items():
        if domain in url_lower:
            platform_name = domain.split('.')[0].capitalize()
            return platform_name, api
    
    return None, None


async def scrape_url(url):
    """
    Scrape metadata/download links from supported platforms.
    
    Args:
        url: Platform URL to scrape
        
    Returns:
        Dict with scraped data or None if failed/unsupported
    """
    try:
        platform, api_endpoint = detect_platform(url)
        
        if not platform:
            LOGGER.error(f"[SCRAPER] Unsupported platform: {url}")
            return None
        
        LOGGER.info(f"[SCRAPER] Detected platform: {platform}")
        
        # Special handling for Crunchyroll
        if api_endpoint == "CRUNCHYROLL_API":
            return await scrape_crunchyroll(url)
        
        # Standard API scraping for other platforms
        return await scrape_with_api(url, api_endpoint, platform)
        
    except Exception as e:
        LOGGER.error(f"[SCRAPER] Error scraping {url}: {str(e)}")
        return None


async def scrape_with_api(url, api_endpoint, platform):
    """
    Scrape using the-zake/pbx1bots workers API.
    
    Args:
        url: Original URL
        api_endpoint: Worker API endpoint
        platform: Platform name
        
    Returns:
        Dict with scraped data or None
    """
    try:
        scrape_url_full = f"{api_endpoint}{url}"
        LOGGER.info(f"[SCRAPER] Calling API: {scrape_url_full[:100]}...")
        
        async with ClientSession() as session:
            async with session.get(scrape_url_full, timeout=30) as response:
                # Check HTTP status
                if response.status == 500:
                    LOGGER.error(f"[SCRAPER] API error 500 - Invalid URL or content not available")
                    return None
                elif response.status == 404:
                    LOGGER.error(f"[SCRAPER] API error 404 - Endpoint not found")
                    return None
                elif response.status != 200:
                    LOGGER.error(f"[SCRAPER] API returned status {response.status}")
                    return None
                
                try:
                    data = await response.json()
                except Exception as e:
                    LOGGER.error(f"[SCRAPER] Failed to parse JSON response: {str(e)}")
                    # Try reading as text
                    text = await response.text()
                    LOGGER.error(f"[SCRAPER] Response text: {text[:200]}...")
                    return None
                
                LOGGER.info(f"[SCRAPER] API response keys: {list(data.keys()) if isinstance(data, dict) else type(data).__name__}")
                
                # Parse response based on tested formats
                result = {
                    "platform": platform,
                    "title": None,
                    "download_links": [],
                    "thumbnail": None,
                    "poster": None,
                    "duration": None,
                    "quality": None,
                    "videoId": None,
                    "type": None,
                    "year": None,
                }
                
                if not isinstance(data, dict):
                    LOGGER.error(f"[SCRAPER] Unexpected response type: {type(data)}")
                    return None
                
                # YouTube format: {videoId, title, thumbnail}
                if "videoId" in data:
                    result["videoId"] = data["videoId"]
                    result["title"] = data.get("title")
                    result["thumbnail"] = data.get("thumbnail")
                
                # Netflix format: {poster}
                elif "poster" in data:
                    result["poster"] = data["poster"]
                    result["thumbnail"] = data["poster"]  # Use poster as thumbnail
                
                # Prime Video format: {type, landscape, portrait, title, year}
                elif "landscape" in data and "portrait" in data:
                    result["title"] = f"{data.get('title', 'Unknown')} ({data.get('year', 'N/A')})"
                    result["thumbnail"] = data.get("portrait")  # Portrait for thumbnail
                    result["poster"] = data.get("landscape")    # Landscape for poster
                    result["type"] = data.get("type")  # movie/series
                    result["year"] = data.get("year")
                
                # TikTok format: {success, data: {url, title, thumbnail, medias: [{url, quality}]}}
                elif "success" in data and data.get("success") and "data" in data:
                    tiktok_data = data["data"]
                    result["title"] = tiktok_data.get("title", "Unknown")
                    result["thumbnail"] = tiktok_data.get("thumbnail")
                    
                    # Extract medias array (videos with different qualities)
                    if "medias" in tiktok_data and isinstance(tiktok_data["medias"], list):
                        for media in tiktok_data["medias"]:
                            if isinstance(media, dict) and "url" in media and media["type"] == "video":
                                result["download_links"].append(media["url"])
                
                # Facebook format: {links: [{quality, url}], title, thumbnail}
                elif "links" in data and isinstance(data["links"], list):
                    result["title"] = data.get("title", "Unknown")
                    result["thumbnail"] = data.get("thumbnail")
                    
                    # Extract links array with quality options
                    for link in data["links"]:
                        if isinstance(link, dict) and "url" in link:
                            result["download_links"].append(link["url"])
                
                # Generic format extraction
                else:
                    # Extract title/name
                    result["title"] = (
                        data.get("title") or 
                        data.get("name") or 
                        data.get("filename") or
                        data.get("video_title")
                    )
                    
                    # Extract thumbnails
                    result["thumbnail"] = (
                        data.get("thumbnail") or 
                        data.get("thumb") or 
                        data.get("image") or
                        data.get("poster")
                    )
                    
                    # Extract metadata
                    result["duration"] = data.get("duration") or data.get("length")
                    result["quality"] = data.get("quality") or data.get("resolution")
                    
                    # Extract download links (priority order)
                    if "download_url" in data and data["download_url"]:
                        result["download_links"].append(data["download_url"])
                    elif "url" in data and isinstance(data["url"], str) and data["url"].startswith("http"):
                        result["download_links"].append(data["url"])
                    elif "links" in data and isinstance(data["links"], list):
                        result["download_links"].extend([link for link in data["links"] if isinstance(link, str)])
                    elif "formats" in data and isinstance(data["formats"], list):
                        # YouTube-like format array
                        for fmt in data["formats"]:
                            if isinstance(fmt, dict) and "url" in fmt and fmt["url"]:
                                result["download_links"].append(fmt["url"])
                    elif "media" in data and isinstance(data["media"], dict):
                        # Nested media object
                        if "url" in data["media"]:
                            result["download_links"].append(data["media"]["url"])
                
                # Return result if we got any useful data
                if result["title"] or result["thumbnail"] or result["download_links"] or result["poster"] or result["videoId"]:
                    return result
                
                LOGGER.error(f"[SCRAPER] No useful data extracted from response")
                return None
                
    except Exception as e:
        LOGGER.error(f"[SCRAPER] API error: {str(e)}")
        return None


async def scrape_crunchyroll(url):
    """
    Special handler for Crunchyroll using the existing implementation.
    
    Args:
        url: Crunchyroll URL
        
    Returns:
        Dict with Crunchyroll data
    """
    try:
        from requests import Session
        
        cid = url.split("/")[4]
        
        session = Session()
        session.headers = {"Authorization": "Basic Y3Jfd2ViOg=="}
        
        r = session.post(
            "https://www.crunchyroll.com/auth/v1/token",
            headers=session.headers,
            data={"grant_type": "client_id"}
        )
        bearer = r.json()["access_token"]
        
        session.headers = {"Authorization": f"Bearer {bearer}"}
        res = session.get(
            f"https://www.crunchyroll.com/content/v2/cms/series/{cid}?locale=en-US",
            headers=session.headers
        )
        
        data = res.json()["data"][0]
        
        return {
            "platform": "Crunchyroll",
            "title": f"{data.get('title')} - {data.get('series_launch_year')}",
            "download_links": [],  # Crunchyroll returns images, not download links
            "thumbnail": data["images"]["poster_tall"][0][-1]["source"],
            "landscape": data["images"]["poster_wide"][0][-1]["source"],
        }
        
    except Exception as e:
        LOGGER.error(f"[SCRAPER] Crunchyroll error: {str(e)}")
        return None


def get_supported_platforms():
    """Get list of supported platform names."""
    platforms = set()
    for domain in SCRAPER_APIS.keys():
        if domain != "CRUNCHYROLL_API":
            platform_name = domain.split('.')[0].capitalize()
            platforms.add(platform_name)
    return sorted(platforms)
