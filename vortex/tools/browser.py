import asyncio
import logging
import webbrowser
from typing import Any, Dict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions


def _get_driver() -> webdriver.Chrome:
    opts = ChromeOptions()
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--start-maximized")
    try:
        return webdriver.Chrome(options=opts)
    except Exception:
        logging.exception("Selenium Chrome failed; falling back to default browser only")
        raise


async def vortex_open_url(url: str) -> Dict[str, Any]:
    u = (url or "").strip()
    if not u:
        return {"ok": False, "error": "URL is empty"}
    webbrowser.open(u)
    return {"ok": True, "message": f"Opening {u}"}


async def vortex_web_search(query: str) -> Dict[str, Any]:
    q = (query or "").strip()
    if not q:
        return {"ok": False, "error": "Search query is empty"}
    import urllib.parse as _up

    url = "https://www.google.com/search?q=" + _up.quote_plus(q)
    return await vortex_open_url(url)


async def vortex_play_youtube_music(query: str) -> Dict[str, Any]:
    q = (query or "").strip() or "coding music"
    import urllib.parse as _up

    url = "https://www.youtube.com/results?search_query=" + _up.quote_plus(q)
    webbrowser.open(url)
    return {"ok": True, "message": f"Playing YouTube results for {q}"}


__all__ = ["vortex_open_url", "vortex_web_search", "vortex_play_youtube_music"]

