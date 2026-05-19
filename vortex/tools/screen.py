import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import pyautogui
import pytesseract

from core import DATA_DIR

import os

SCREENSHOT_PATH = DATA_DIR / "last_screenshot.png"

# --- TESSERACT CONFIGURATION ---
def _setup_tesseract():
    # Common Windows paths for Tesseract
    paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe".format(os.getlogin()),
    ]
    for p in paths:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            logging.info(f"Tesseract found at {p}")
            return True
    return False

TESSERACT_AVAILABLE = _setup_tesseract()


def _capture_and_ocr_sync() -> Dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        img = pyautogui.screenshot()
        img.save(SCREENSHOT_PATH)
        if not TESSERACT_AVAILABLE:
            return {"ok": True, "message": "Screenshot saved, but Tesseract not found (OCR disabled).", "text": "", "path": str(SCREENSHOT_PATH)}
        
        text = pytesseract.image_to_string(str(SCREENSHOT_PATH))
        return {"ok": True, "message": "Screenshot captured and read.", "text": text, "path": str(SCREENSHOT_PATH)}
    except Exception as e:
        logging.exception("Screenshot/OCR failed")
        return {"ok": False, "error": str(e), "text": "", "path": str(SCREENSHOT_PATH)}


async def vortex_capture_and_ocr() -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _capture_and_ocr_sync)


async def vortex_capture_and_ocr_text_only() -> Optional[str]:
    res = await vortex_capture_and_ocr()
    if not res.get("ok"):
        return None
    return (res.get("text") or "").strip() or None


async def vortex_analyze_error(query: str, screenshot_text: Optional[str]) -> Dict[str, Any]:
    # For now, keep it simple and just summarize the OCR text and query.
    txt = (screenshot_text or "").strip()
    snippet = txt[:400].replace("\n", " ")
    if not snippet:
        return {
            "ok": False,
            "error": "No text detected on screen. Try enlarging the error message.",
        }
    message = f"I see this on screen: {snippet}"
    return {"ok": True, "message": message}


__all__ = [
    "vortex_capture_and_ocr",
    "vortex_capture_and_ocr_text_only",
    "vortex_analyze_error",
    "SCREENSHOT_PATH",
]

