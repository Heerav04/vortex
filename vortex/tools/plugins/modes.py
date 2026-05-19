import asyncio
import logging
from typing import Any, Dict

_CURRENT_MODE = "general"


async def vortex_set_mode(mode: str) -> Dict[str, Any]:
    global _CURRENT_MODE
    m = (mode or "").strip().lower() or "general"
    _CURRENT_MODE = m
    logging.info("Vortex mode set to %s", m)
    await asyncio.sleep(0)  # keep this async-friendly
    return {"ok": True, "message": f"Mode set to {m}"}


def current_mode() -> str:
    return _CURRENT_MODE


__all__ = ["vortex_set_mode", "current_mode"]

