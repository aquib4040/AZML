import re
from logging import getLogger
from asyncio import sleep
from httpx import AsyncClient, TimeoutException

from bot import config_dict

LOGGER = getLogger(__name__)

def apply_regex_rename(filename, pattern_str):
    if not pattern_str:
        return filename
    parts = pattern_str.strip().split("|")
    result = filename
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            pat, repl = part.split(":", 1)
        else:
            pat = part
            repl = ""
        try:
            result = re.sub(pat, repl, result)
        except re.error:
            continue
    if not result.strip():
        return filename
    return result

def _final_clean(title):
    title = re.sub(r"[\[\](){}]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title

def format_clean_poster_title(raw_title, rename_regex=None):
    from urllib.parse import unquote
    raw_title = unquote(raw_title)

    if rename_regex:
        try:
            raw_title = apply_regex_rename(raw_title, rename_regex)
        except Exception as e:
            LOGGER.warning(f"Failed to apply regex clean to TMDb title: {e}")

    title = re.sub(r"https?://\S+", " ", raw_title)
    title = re.sub(r"\bt\.me/\S+", " ", title, flags=re.IGNORECASE)
    title = re.sub(r"\btelegram\.me/\S+", " ", title, flags=re.IGNORECASE)
    title = re.sub(r"[\[\](){}]", " ", title)
    title = re.sub(r"\.\w{2,4}$", "", title)
    title = re.sub(r"\b(www\.)?\w+\.(com|net|org|xyz|me|in|to|co|cc|info|tv|link|app|online|site|club|work|icu|top|vip|pro)\b", " ", title, flags=re.IGNORECASE)
    title = re.sub(r"\bwww\S*", " ", title, flags=re.IGNORECASE)
    title = re.sub(r"[-_.]", " ", title)
    title = re.sub(r"\s+", " ", title).strip()
    
    try:
        import PTN
        parsed = PTN.parse(title)
        
        ptn_title = parsed.get("title")
        if ptn_title:
            if type(ptn_title) == list:
                ptn_title = ptn_title[0]
            title = ptn_title
        else:
            # If PTN fails to extract a title (e.g., S01E01 is at the very beginning)
            # Manually strip the identified tags (like 1080p) from the raw title
            for key in ["resolution", "codec", "quality", "audio", "container", "website", "group"]:
                val = parsed.get(key)
                if val and isinstance(val, str):
                    title = re.sub(rf"\b{re.escape(val)}\b", " ", title, flags=re.IGNORECASE)

        ptn_season = parsed.get("season")
        if type(ptn_season) == list:
            ptn_season = ptn_season[0]
            
        ptn_year = parsed.get("year")
        if type(ptn_year) == list:
            ptn_year = ptn_year[0]
            
    except Exception as e:
        LOGGER.warning(f"PTN parsing failed: {e}")
        ptn_season = None
        ptn_year = None

    season = None
    year = None

    sxx_exx = re.search(r"(?<!\w)S0*(\d{1,2})E\d{1,2}(?!\w)", title, re.IGNORECASE)
    if sxx_exx:
        season = f"Season {int(sxx_exx.group(1))}"
        if sxx_exx.start() <= 1:
            title = title[sxx_exx.end():].strip()
        else:
            title = title[: sxx_exx.start()].strip()
        return _final_clean(title), season, None

    season_match = re.search(r"\bSeason\s+(\d{1,2})\b", title, re.IGNORECASE)
    if season_match:
        season = f"Season {int(season_match.group(1))}"
        if season_match.start() <= 1:
            title = title[season_match.end():].strip()
        else:
            title = title[: season_match.start()].strip()
        return _final_clean(title), season, None

    s_simple = re.search(r"(?<!\w)S0*(\d{1,2})(?!\w)", title, re.IGNORECASE)
    if s_simple:
        season = f"Season {int(s_simple.group(1))}"
        if s_simple.start() <= 1:
            title = title[s_simple.end():].strip()
        else:
            title = title[: s_simple.start()].strip()
        return _final_clean(title), season, None

    ep_match = re.search(
        r"(?<!\w)(E\d{1,4}|EP\s*\d{1,4}|EPISODE\s*\d{1,4})(?!\w)",
        title,
        re.IGNORECASE,
    )
    if ep_match:
        if ep_match.start() <= 1:
            title = title[ep_match.end():].strip()
        else:
            title = title[: ep_match.start()].strip()

    all_years = list(re.finditer(r"\b(19|20)\d{2}\b", title))
    if all_years:
        last_year_match = all_years[-1]
        year = last_year_match.group(0)
        if last_year_match.start() <= 1:
            title = title[last_year_match.end():].strip()
        else:
            title = title[: last_year_match.start()].strip()
        return _final_clean(title), (season or (f"Season {ptn_season}" if ptn_season else None)), (year or ptn_year)

    return _final_clean(title), (season or (f"Season {ptn_season}" if ptn_season else None)), (year or ptn_year)

async def get_tmdb_poster_link(title, year=None, as_doc=False):
    access_token = config_dict.get("TMDB_ACCESS_TOKEN", "").strip()
    if not access_token:
        LOGGER.warning("TMDB_ACCESS_TOKEN not configured, skipping TMDb lookup")
        return None

    try:
        headers = {"accept": "application/json"}
        params = {
            "query": title,
            "include_adult": "false",
            "language": "en-US",
            "page": "1",
        }
        
        # If token is short, it's an API Key (v3). If it's very long, it's a Read Access Token (v4 Bearer).
        if len(access_token) < 50:
            params["api_key"] = access_token
        else:
            headers["Authorization"] = f"Bearer {access_token}"

        search_url = "https://api.themoviedb.org/3/search/multi"
        if year:
            params["year"] = year

        for attempt in range(3):
            try:
                async with AsyncClient(timeout=10) as client:
                    resp = await client.get(search_url, params=params, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        results = data.get("results", [])
                        if not results:
                            LOGGER.info(f"No TMDb results for '{title}'")
                            return None

                        first_result = results[0]
                        tmdb_id = first_result.get("id")
                        media_type = first_result.get("media_type", "movie")
                        result_name = first_result.get("title") or first_result.get("name")

                        if media_type == "person":
                            LOGGER.info(f"TMDb result is a person, skipping: {result_name}")
                            return None

                        images_url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}/images"
                        images_params = {
                            "include_image_languages": "en,null",
                        }
                        if len(access_token) < 50:
                            images_params["api_key"] = access_token
                            
                        img_resp = await client.get(images_url, params=images_params, headers=headers)

                        if img_resp.status_code == 200:
                            img_data = img_resp.json()
                            backdrops = img_data.get("backdrops", [])
                            posters = img_data.get("posters", [])

                            en_backdrops = [b for b in backdrops if b.get("iso_639_1") == "en"]
                            clean_backdrops = [b for b in backdrops if b.get("iso_639_1") is None]
                            en_posters = [p for p in posters if p.get("iso_639_1") == "en"]
                            other_posters = [p for p in posters if p.get("iso_639_1") is None]

                            image_path = None
                            image_type = "unknown"

                            if as_doc:
                                if en_posters:
                                    image_path = en_posters[0]["file_path"]
                                    image_type = "poster (en)"
                                elif other_posters:
                                    image_path = other_posters[0]["file_path"]
                                    image_type = "poster (clean)"
                                elif posters:
                                    image_path = posters[0]["file_path"]
                                    image_type = "poster (other)"
                                elif en_backdrops:
                                    image_path = en_backdrops[0]["file_path"]
                                    image_type = "backdrop (en)"
                                elif clean_backdrops:
                                    image_path = clean_backdrops[0]["file_path"]
                                    image_type = "backdrop (clean)"
                            else:
                                if en_backdrops:
                                    image_path = en_backdrops[0]["file_path"]
                                    image_type = "landscape (en)"
                                elif clean_backdrops:
                                    image_path = clean_backdrops[0]["file_path"]
                                    image_type = "landscape (clean)"
                                elif backdrops:
                                    image_path = backdrops[0]["file_path"]
                                    image_type = "landscape (other)"
                                elif en_posters:
                                    image_path = en_posters[0]["file_path"]
                                    image_type = "poster (en)"
                                elif posters:
                                    image_path = posters[0]["file_path"]
                                    image_type = "poster (fallback)"

                            if image_path:
                                poster_url = f"https://image.tmdb.org/t/p/original{image_path}"
                                LOGGER.info(f"Found TMDb {image_type}: {result_name}")
                                return poster_url

                        LOGGER.info("Images endpoint failed, using search fallback")
                        backdrop_path = first_result.get("backdrop_path")
                        poster_path = first_result.get("poster_path")
                        fallback = (poster_path or backdrop_path) if as_doc else (backdrop_path or poster_path)
                        
                        if fallback:
                            LOGGER.info(f"Found TMDb fallback image: {result_name}")
                            return f"https://image.tmdb.org/t/p/original{fallback}"

                        LOGGER.info(f"No images available for '{title}' on TMDb")
                        return None

                    elif resp.status_code == 401:
                        LOGGER.warning("TMDb authentication failed. Check your token")
                        return None
                    elif resp.status_code >= 500:
                        LOGGER.warning(f"TMDb server error {resp.status_code} (attempt {attempt + 1}/3)")
                        await sleep(2)
                    else:
                        LOGGER.warning(f"TMDb API returned status {resp.status_code} for '{title}'")
                        return None

            except TimeoutException:
                LOGGER.warning(f"Timeout on attempt {attempt + 1}/3 for TMDb API")
            except Exception as e:
                LOGGER.warning(f"Client error on attempt {attempt + 1}/3: {e}")
            await sleep(1)

    except Exception as e:
        LOGGER.error(f"TMDb API error for '{title}': {e}")
    return None

async def get_final_poster_url(raw_filename, as_doc=False, rename_regex=None):
    title, season, year = format_clean_poster_title(raw_filename, rename_regex)
    if not title or len(title.strip()) < 2:
        LOGGER.info(f"Title too short for TMDb search: '{title}'")
        return None
    LOGGER.info(f"Poster search title: {title}")
    if season:
        LOGGER.info(f"Season extracted: {season}")
    if year:
        LOGGER.info(f"Year extracted: {year}")

    poster_url = await get_tmdb_poster_link(title, year, as_doc)
    if poster_url:
        LOGGER.info("Poster found via TMDb API")
        return poster_url

    LOGGER.info("No poster found from TMDb")
    return None
