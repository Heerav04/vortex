import logging
import os
import json
import asyncio
import time
import aiohttp
from typing import Any, Dict, List, Optional
from core import DATA_DIR
from .dual_brain_log import log_dual_brain_event

# Modern google-genai SDK
try:
    from google import genai
except ImportError:
    genai = None

DICTIONARY_PATH = DATA_DIR / "dictionary.json"

_GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.0-flash",
]

_gemini_client = None

# ── Rate-limit guard ─────────────────────────────────────────────────────────
# When Gemini returns a 429 / quota error we flip this flag and record the
# time. For the next GEMINI_COOLDOWN_SECS seconds every call skips Gemini
# entirely and goes straight to the fast local Ollama model.
_gemini_rate_limited: bool = False
_gemini_rl_until: float = 0.0  # epoch seconds
GEMINI_COOLDOWN_SECS: int = int(os.getenv("GEMINI_COOLDOWN_SECS", "60"))

# Keywords that indicate a quota / rate-limit error from any Gemini exception
_QUOTA_KEYWORDS = (
    "429",
    "quota",
    "rate limit",
    "ratelimit",
    "resource exhausted",
    "resourceexhausted",
    "too many requests",
)


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(k in msg for k in _QUOTA_KEYWORDS)


def _mark_rate_limited() -> None:
    global _gemini_rate_limited, _gemini_rl_until
    _gemini_rate_limited = True
    _gemini_rl_until = time.monotonic() + GEMINI_COOLDOWN_SECS
    logging.warning(
        "[Vortex] Gemini quota/rate-limit hit. "
        "Switching to fast offline Ollama for %ds.",
        GEMINI_COOLDOWN_SECS,
    )


def _gemini_available() -> bool:
    """Return True only when Gemini is configured AND not in cooldown."""
    global _gemini_rate_limited, _gemini_rl_until
    if _gemini_rate_limited:
        if time.monotonic() > _gemini_rl_until:
            _gemini_rate_limited = False
            logging.info("[Vortex] Gemini cooldown expired – resuming cloud calls.")
        else:
            return False
    api_key = os.getenv("GEMINI_API_KEY", "")
    return bool(api_key and api_key != "your_gemini_api_key_here")
# ─────────────────────────────────────────────────────────────────────────────


def _get_client():
    global _gemini_client
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
    if _gemini_client is None and genai:
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client

def _extract_clean_response(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        inner_lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(inner_lines).strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            if "response" in data: return str(data["response"]).strip()
            if "message" in data: return str(data["message"]).strip()
    except:
        pass
    return text

def _response_quality_score(text: str) -> float:
    """
    Very lightweight quality heuristic for routing decisions.
    Returns 0..1.
    """
    t = (text or "").strip()
    if not t:
        return 0.0
    if len(t) < 40:
        return 0.25
    low = t.lower()
    if "i could not reach" in low or "try again" in low:
        return 0.1
    if "as an ai" in low and "i can't" in low:
        return 0.2
    return 0.8

async def vortex_llm_chat(
    query: Optional[str] = None,
    history: Optional[List[Dict[str, Any]]] = None,
    message: Optional[str] = None,
    **_: Any,
) -> Dict[str, Any]:
    """
    Local-first + cloud-fallback chat.

    Rules:
    - Prefer local Ollama for privacy/offline reasoning.
    - Only call Gemini when local output is weak/unavailable and GEMINI_API_KEY is set.
    """
    q = (query or message or "").strip()
    if not q:
        return {"ok": False, "message": "Please provide a message."}
    profile_ctx = ""
    try:
        from core.memory import VortexMemory
        mem = VortexMemory()
        p = mem.profile
        profile_ctx = f"User: {p.name}\n"
    except: pass

    system_prompt = f"You are VORTX, a personal assistant. {profile_ctx}\nUser: {q}\nVortex:"

    # 1) Cloud-first: Gemini (only when configured AND not rate-limited)
    if _gemini_available():
        client = _get_client()
        if client:
            try:
                loop = asyncio.get_event_loop()
                model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
                response = await loop.run_in_executor(
                    None, lambda: client.models.generate_content(model=model, contents=system_prompt)
                )
                if response and response.text:
                    clean = _extract_clean_response(response.text)
                    log_dual_brain_event(
                        stage="chat",
                        source="gemini",
                        model=model,
                        query=q,
                        response=clean,
                        metadata={"route": "gemini_primary"},
                    )
                    return {"ok": True, "message": clean, "source": "gemini_primary"}
            except Exception as _exc:
                if _is_rate_limit_error(_exc):
                    _mark_rate_limited()
                else:
                    logging.exception("Gemini primary failed")

    # 2) Fast offline fallback: Ollama (llama3.2:1b is the fastest local model)
    # When Gemini is rate-limited this path is taken immediately with no delay.
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/") + "/api/generate"
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"model": ollama_model, "prompt": system_prompt, "stream": False}
            async with session.post(ollama_url, json=payload, timeout=aiohttp.ClientTimeout(total=45)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    msg = _extract_clean_response(data.get("response", ""))
                    if _response_quality_score(msg) >= float(os.getenv("LOCAL_CONFIDENCE_THRESHOLD", "0.62")):
                        log_dual_brain_event(
                            stage="chat",
                            source="ollama",
                            model=ollama_model,
                            query=q,
                            response=msg,
                            metadata={"route": "local_ollama_fallback"},
                        )
                        return {"ok": True, "message": msg, "source": "local_ollama_fallback"}
                try:
                    err_data = await resp.json()
                    err_msg = str(err_data.get("error", ""))
                except Exception:
                    err_msg = ""
                if "requires more system memory" in err_msg.lower():
                    fallback_msg = "I am in low-memory mode right now. Please ask short questions, or switch OLLAMA_MODEL to a smaller model in your .env and restart Vortex."
                    log_dual_brain_event(
                        stage="chat",
                        source="ollama",
                        model=ollama_model,
                        query=q,
                        response=fallback_msg,
                        metadata={"route": "local_fallback", "error": err_msg},
                    )
                    return {
                        "ok": True,
                        "message": fallback_msg,
                        "source": "local_fallback",
                    }
    except Exception:
        logging.info("Ollama unavailable after Gemini failure.")

    # Final local fallback so UI still gets a direct in-app response.
    fallback = {
        "ok": True,
        "message": "I could not reach my language model right now, but I am still online. Try 'open vscode', 'scan apps', or ask again after Ollama is ready.",
        "source": "local_fallback",
    }
    log_dual_brain_event(
        stage="chat",
        source="fallback",
        model="none",
        query=q,
        response=fallback["message"],
        metadata={"route": "final_fallback"},
    )
    return fallback

async def vortex_llm_qa(
    query: Optional[str] = None,
    history: Optional[List[Dict[str, Any]]] = None,
    message: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    # QA uses the same cloud-first logic
    return await vortex_llm_chat(query=query, history=history, message=message, **kwargs)

__all__ = ["vortex_llm_qa", "vortex_llm_chat"]
