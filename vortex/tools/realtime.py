"""
Real-time information tools for Vortex.
Provides live news, search results, sports scores, weather, and time.
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

# DuckDuckGo search
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

# IST timezone offset
IST = timezone(timedelta(hours=5, minutes=30))


# ── Time & Date (Zero latency, offline) ─────────────────────────────────────

async def vortex_get_time(**kwargs) -> Dict[str, Any]:
    """Returns current date, time, and day in IST."""
    now = datetime.now(IST)
    time_str = now.strftime("%I:%M %p")  # 08:30 PM
    date_str = now.strftime("%A, %B %d, %Y")  # Friday, March 07, 2025
    return {
        "ok": True,
        "message": f"It's {time_str} on {date_str} (IST).",
        "data": {
            "time": time_str,
            "date": date_str,
            "day": now.strftime("%A"),
            "iso": now.isoformat(),
        },
    }


# ── DuckDuckGo Web Search ───────────────────────────────────────────────────

def _ddg_search_sync(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Synchronous DuckDuckGo web search."""
    if not DDGS:
        return []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return results
    except Exception as e:
        logging.warning("DuckDuckGo search failed: %s", e)
        return []


async def vortex_web_search_realtime(query: str, **kwargs) -> Dict[str, Any]:
    """Real-time web search using DuckDuckGo."""
    q = (query or "").strip()
    if not q:
        return {"ok": False, "error": "Empty search query"}

    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, lambda: _ddg_search_sync(q, 5))

    if not results:
        return {"ok": False, "error": f"No results found for '{q}'"}

    # Format results into a readable summary
    lines = []
    for i, r in enumerate(results[:5], 1):
        title = r.get("title", "")
        body = r.get("body", "")
        href = r.get("href", "")
        lines.append(f"{i}. **{title}**\n   {body}")

    summary = "\n".join(lines)
    return {"ok": True, "message": summary, "source": "duckduckgo", "data": results}


# ── DuckDuckGo News ─────────────────────────────────────────────────────────

def _ddg_news_sync(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Synchronous DuckDuckGo news search."""
    if not DDGS:
        return []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=max_results))
            return results
    except Exception as e:
        logging.warning("DuckDuckGo news failed: %s", e)
        return []


async def vortex_news(query: str = "latest news India", **kwargs) -> Dict[str, Any]:
    """Fetch real-time news headlines using DuckDuckGo."""
    q = (query or "").strip() or "latest news India"

    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, lambda: _ddg_news_sync(q, 5))

    if not results:
        return {"ok": False, "error": "Couldn't fetch news right now. Try again in a moment."}

    lines = []
    for i, r in enumerate(results[:5], 1):
        title = r.get("title", "")
        source = r.get("source", "")
        date = r.get("date", "")
        body = r.get("body", "")
        source_info = f" ({source})" if source else ""
        lines.append(f"{i}. {title}{source_info}\n   {body[:120]}")

    summary = "\n".join(lines)
    return {"ok": True, "message": summary, "source": "duckduckgo_news", "data": results}


# ── Live Sports Scores ──────────────────────────────────────────────────────

async def vortex_live_score(query: str = "cricket live score", **kwargs) -> Dict[str, Any]:
    """Fetch live sports scores by searching for them online."""
    q = (query or "").strip()

    # Build a targeted search query
    sport_keywords = ["cricket", "football", "soccer", "ipl", "nba", "nfl", "tennis", "f1"]
    has_sport = any(s in q.lower() for s in sport_keywords)

    if not has_sport:
        search_q = f"{q} live score today"
    else:
        search_q = f"{q} live score today"

    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, lambda: _ddg_search_sync(search_q, 5))

    if not results:
        return {"ok": False, "error": "Couldn't fetch live scores right now."}

    # Filter out junk results (like the YouTube help you saw)
    junk_words = ["youtube", "help", "how to", "support", "google help"]
    if results and any(w in results[0].get("title", "").lower() for w in junk_words):
        return {"ok": False, "error": "No clear match found in live scores. Trying grounded search."}

    lines = []
    for i, r in enumerate(results[:3], 1):
        title = r.get("title", "")
        body = r.get("body", "")
        lines.append(f"{i}. {title}\n   {body[:150]}")

    summary = "\n".join(lines)
    return {"ok": True, "message": summary, "source": "duckduckgo_scores", "data": results}


# ── Weather ─────────────────────────────────────────────────────────────────

async def vortex_weather(query: str = "weather Mumbai", **kwargs) -> Dict[str, Any]:
    """Fetch current weather by searching for it online."""
    q = (query or "").strip() or "weather Mumbai"

    if "weather" not in q.lower():
        q = f"weather {q} today"

    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, lambda: _ddg_search_sync(q, 3))

    if not results:
        return {"ok": False, "error": "Couldn't fetch weather right now."}

    lines = []
    for r in results[:2]:
        title = r.get("title", "")
        body = r.get("body", "")
        lines.append(f"{title}\n{body[:200]}")

    summary = "\n".join(lines)
    return {"ok": True, "message": summary, "source": "duckduckgo_weather", "data": results}


# ── Gemini Grounded Search (Google Search integration) ──────────────────────

async def vortex_grounded_search(query: str, **kwargs) -> Dict[str, Any]:
    """
    Use Gemini with Google Search grounding for real-time answers.
    This gives the LLM access to live Google Search results.
    """
    import os
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        # Fallback to DuckDuckGo if SDK not available
        return await vortex_web_search_realtime(query=query)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return await vortex_web_search_realtime(query=query)

    loop = asyncio.get_running_loop()
    now = datetime.now(IST)
    time_context = now.strftime("%I:%M %p, %A %B %d, %Y (IST)")

    prompt = (
        f"Current date & time: {time_context}\n\n"
        f"User asks: {query}\n\n"
        "Use Google Search to find the latest real-time information. "
        "Respond with a concise, helpful summary. Include specific facts, scores, numbers, or headlines."
    )

    try:
        client = genai.Client(api_key=api_key)
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                ),
            )
        )

        if hasattr(response, 'text') and response.text:
            return {"ok": True, "message": response.text.strip(), "source": "gemini_grounded"}
    except Exception as e:
        logging.warning("Gemini grounded search failed: %s", e)

    # Fallback to DuckDuckGo
    return await vortex_web_search_realtime(query=query)


__all__ = [
    "vortex_get_time",
    "vortex_web_search_realtime",
    "vortex_news",
    "vortex_live_score",
    "vortex_weather",
    "vortex_grounded_search",
]
