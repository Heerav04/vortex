import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Optional

from . import BASE_DIR

DUAL_BRAIN_LOG_PATH = BASE_DIR / "dual_brain.log"


def _trim(text: Optional[str], limit: int = 4000) -> str:
    t = (text or "").strip()
    if len(t) <= limit:
        return t
    return t[:limit] + "... [truncated]"


def log_dual_brain_event(
    *,
    stage: str,
    source: str,
    model: str,
    query: str,
    response: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    entry = {
        "ts_utc": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "stage": stage,
        "source": source,
        "model": model,
        "query": _trim(query, 1000),
        "response": _trim(response, 4000),
        "metadata": metadata or {},
    }
    line = json.dumps(entry, ensure_ascii=False)
    Path(DUAL_BRAIN_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(DUAL_BRAIN_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")

