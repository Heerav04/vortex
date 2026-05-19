import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Resolve the project base directory correctly for both
# local development and compiled PyInstaller .exe
if getattr(sys, "frozen", False):
    # Running in a bundled executable
    BASE_DIR = Path(sys.executable).parent
else:
    # Standard script run
    BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"

def ensure_data_dirs() -> None:
    # Ensure logs go to the base folder
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logging.exception("Failed loading JSON: %s", path)
        return default


def save_json(path: Path, data: Any) -> None:
    try:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        logging.exception("Failed writing JSON: %s", path)


__all__ = ["BASE_DIR", "DATA_DIR", "ensure_data_dirs", "load_json", "save_json"]
