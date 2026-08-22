from base64 import b64encode
from random import choice, random, randrange
from time import sleep
from urllib.parse import quote

from cloudscraper import create_scraper
from urllib3 import disable_warnings

from bot import LOGGER, shorteners_list


def short_url(longurl, attempt=0):
    if not shorteners_list:
        return longurl
    if attempt >= 4:
        return longurl
    i = 0 if len(shorteners_list) == 1 else randrange(len(shorteners_list))
    _shorten_dict = shorteners_list[i]
    _shortener = _shorten_dict.get("domain", "")
    _shortener_api = _shorten_dict.get("api_key", "")
    cget = create_scraper().request
    disable_warnings()
    try:
        if "%s" in _shortener:
            if _shortener.count("%s") >= 2:
                req_url = _shortener % (_shortener_api, quote(longurl))
            else:
                req_url = _shortener % quote(longurl)
            res = cget("GET", req_url)
            try:
                data = res.json()
                shorted = (
                    data.get("shortenedUrl")
                    or data.get("shorturl")
                    or data.get("url")
                    or data.get("short")
                    or data.get("link")
                )
                if shorted:
                    return shorted
            except Exception:
                pass
            text = res.text.strip()
            if text.startswith("http://") or text.startswith("https://"):
                return text
            return longurl
        elif "{api}" in _shortener or "{url}" in _shortener:
            req_url = _shortener.replace("{api}", _shortener_api).replace("{url}", quote(longurl))
            res = cget("GET", req_url)
            try:
                data = res.json()
                shorted = (
                    data.get("shortenedUrl")
                    or data.get("shorturl")
                    or data.get("url")
                    or data.get("short")
                    or data.get("link")
                )
                if shorted:
                    return shorted
            except Exception:
                pass
            text = res.text.strip()
            if text.startswith("http://") or text.startswith("https://"):
                return text
            return longurl
        elif "shorte.st" in _shortener:
            headers = {"public-api-token": _shortener_api}
            data = {"urlToShorten": quote(longurl)}
            return cget(
                "PUT", "https://api.shorte.st/v1/data/url", headers=headers, data=data
            ).json()["shortenedUrl"]
        elif "linkvertise" in _shortener:
            url = quote(b64encode(longurl.encode("utf-8")))
            linkvertise = [
                f"https://link-to.net/{_shortener_api}/{random() * 1000}/dynamic?r={url}",
                f"https://up-to-down.net/{_shortener_api}/{random() * 1000}/dynamic?r={url}",
                f"https://direct-link.net/{_shortener_api}/{random() * 1000}/dynamic?r={url}",
                f"https://file-link.net/{_shortener_api}/{random() * 1000}/dynamic?r={url}",
            ]
            return choice(linkvertise)
        elif "bitly.com" in _shortener:
            headers = {"Authorization": f"Bearer {_shortener_api}"}
            return cget(
                "POST",
                "https://api-ssl.bit.ly/v4/shorten",
                json={"long_url": longurl},
                headers=headers,
            ).json()["link"]
        elif "ouo.io" in _shortener:
            return cget(
                "GET", f"http://ouo.io/api/{_shortener_api}?s={longurl}", verify=False
            ).text
        elif "cutt.ly" in _shortener:
            return cget(
                "GET",
                f"http://cutt.ly/api/api.php?key={_shortener_api}&short={longurl}",
            ).json()["url"]["shortLink"]
        else:
            domain = _shortener.replace("http://", "").replace("https://", "").rstrip("/")
            res = cget(
                "GET",
                f"https://{domain}/api?api={_shortener_api}&url={quote(longurl)}",
            )
            try:
                data = res.json()
                shorted = (
                    data.get("shortenedUrl")
                    or data.get("shorturl")
                    or data.get("url")
                    or data.get("short")
                    or data.get("link")
                )
                if shorted:
                    return shorted
            except Exception:
                pass
            text = res.text.strip()
            if text.startswith("http://") or text.startswith("https://"):
                return text
            return longurl
    except Exception as e:
        LOGGER.error(f"Shortener error on {_shortener}: {e}")
        sleep(1)
        attempt += 1
        return short_url(longurl, attempt)
