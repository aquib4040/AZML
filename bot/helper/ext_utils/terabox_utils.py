#!/usr/bin/env python3
from playwright.async_api import async_playwright
from bot import LOGGER


async def get_terabox_link(terabox_url):
    """
    Extract direct download link from Terabox URL using 1024teradownloader.com API.
    
    Args:
        terabox_url: Terabox share URL
        
    Returns:
        Direct download link or None if failed
    """
    try:
        LOGGER.info(f"[TERABOX] Resolving link: {terabox_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
                viewport={"width": 390, "height": 844}
            )
            
            page = await context.new_page()
            
            LOGGER.info("[TERABOX] Opening 1024teradownloader.com...")
            
            await page.goto(
                "https://1024teradownloader.com/fastdownload",
                wait_until="domcontentloaded",
                timeout=60000
            )
            
            await page.wait_for_timeout(5000)
            
            LOGGER.info("[TERABOX] Calling /api/stream...")
            
            response = await page.evaluate(f"""
                (async () => {{
                    const form = new FormData();
                    form.append("url", "{terabox_url}");
                    
                    const res = await fetch("/api/stream", {{
                        method: "POST",
                        body: form,
                        credentials: "include"
                    }});
                    
                    return await res.text();
                }})()
            """)
            
            await browser.close()
            
            LOGGER.info(f"[TERABOX] API Response: {response[:500]}...")
            
            # Parse the response to extract actual download link
            import json
            
            # Try different response formats
            try:
                # Case 1: Response is JSON
                if response.startswith("{") or response.startswith("["):
                    data = json.loads(response)
                    
                    # Check various possible JSON structures
                    if isinstance(data, dict):
                        # Check for list array (Terabox API format)
                        if "list" in data and isinstance(data["list"], list) and len(data["list"]) > 0:
                            first_item = data["list"][0]
                            if isinstance(first_item, dict):
                                # Priority order: fast_download_link > premium_link > direct_link > download_link
                                for key in ["fast_download_link", "premium_link", "direct_link", "download_link"]:
                                    if key in first_item and first_item[key]:
                                        link = first_item[key].strip()
                                        if key in ["fast_download_link", "premium_link", "direct_link"]:
                                            LOGGER.info(f"[TERABOX] Using {key}: {link[:100]}...")
                                        else:
                                            LOGGER.info(f"[TERABOX] Using regular download_link (no fast link available)")
                                        return link
                        
                        # Try common field names
                        for key in ["url", "download_link", "downloadLink", "link", "dlink", "direct_link"]:
                            if key in data and data[key]:
                                return data[key].strip()
                        
                        # Check nested structures
                        if "data" in data and isinstance(data["data"], dict):
                            for key in ["url", "download_link", "downloadLink", "link"]:
                                if key in data["data"] and data["data"][key]:
                                    return data["data"][key].strip()
                    
                    elif isinstance(data, list) and len(data) > 0:
                        # If response is array, try first item
                        if isinstance(data[0], dict):
                            for key in ["url", "download_link", "downloadLink", "link"]:
                                if key in data[0] and data[0][key]:
                                    return data[0][key].strip()
                
                # Case 2: Response is direct URL
                elif response.startswith("http"):
                    return response.strip()
                
                # Case 3: Extract URL from text using regex
                else:
                    import re
                    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
                    urls = re.findall(url_pattern, response)
                    if urls:
                        return urls[0].strip()
                
            except Exception as e:
                LOGGER.error(f"[TERABOX] Error parsing response: {str(e)}")
            
            LOGGER.error(f"[TERABOX] Could not extract download link from response: {response[:200]}")
            return None
            
    except Exception as e:
        LOGGER.error(f"[TERABOX] Error resolving link: {str(e)}")
        return None


def is_terabox_link(url):
    """Check if URL is a Terabox link"""
    if not url:
        return False
    
    url_lower = url.lower()
    terabox_domains = [
        "terabox.com",
        "1024terabox.com",
        "teraboxshare.com",
        "teraboxapp.com",
        "terabox.app",
        "mirrobox.com",
        "nephobox.com",
        "freeterabox.com",
        "4funbox.com",
    ]
    
    return any(domain in url_lower for domain in terabox_domains)
