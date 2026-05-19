import asyncio
import logging
import os
import re
import subprocess
from difflib import get_close_matches
from pathlib import Path
from typing import Any, Dict, List, Tuple

import psutil
from ctypes import POINTER, cast  # type: ignore
from comtypes import CLSCTX_ALL  # type: ignore
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # type: ignore

from core import DATA_DIR, load_json, save_json

APPS_JSON_PATH = DATA_DIR / "apps.json"


def _iter_shortcut_dirs() -> List[Path]:
    dirs: List[Path] = []
    programdata = os.getenv("ProgramData")
    appdata = os.getenv("APPDATA")
    userprofile = os.getenv("USERPROFILE")

    if programdata:
        dirs.append(Path(programdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
    if appdata:
        dirs.append(Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
    if userprofile:
        dirs.append(Path(userprofile) / "Desktop")
    return [d for d in dirs if d.exists()]


def _iter_program_dirs() -> List[Path]:
    """
    Common install locations to scan for EXEs.
    This is a best-effort scan and may be pruned in size for performance.
    """
    dirs: List[Path] = []
    for env in ("ProgramFiles", "ProgramFiles(x86)"):
        val = os.getenv(env)
        if val:
            p = Path(val)
            if p.exists():
                dirs.append(p)
    # Optionally add a custom folder later if you want.
    return dirs


def _resolve_lnk_target(lnk_path: Path) -> Dict[str, Any]:
    # Use os.startfile later; don't depend on win32com here to keep things simpler.
    return {"shortcut": str(lnk_path)}


def _scan_apps_sync() -> Dict[str, Any]:
    apps: Dict[str, Any] = {}
    try:
        # Use PowerShell to get ALL apps (Store, Win32, System)
        cmd = ["powershell", "-Command", "Get-StartApps | ConvertTo-Json"]
        result = subprocess.check_output(cmd, text=True, encoding="utf-8")
        import json
        raw_apps = json.loads(result)
        
        if not isinstance(raw_apps, list):
            raw_apps = [raw_apps] if raw_apps else []

        for item in raw_apps:
            name = item.get("Name", "").strip()
            appid = item.get("AppID", "").strip()
            if not name or not appid:
                continue
            
            key = name.lower()
            apps[key] = {
                "name": name,
                "path": f"shell:AppsFolder\\{appid}",
                "resolved": {"target": appid, "type": "store_or_lnk"}
            }
            
    except Exception as e:
        logging.error("PowerShell Get-StartApps failed: %s", e)

    # Built-in fallbacks (just in case)
    builtins = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "paint": "mspaint.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
    }
    for k, exe in builtins.items():
        if k not in apps:
            apps[k] = {"name": k, "path": exe, "resolved": {"target": exe}}

    data = {"apps": apps}
    save_json(APPS_JSON_PATH, data)
    logging.info("Scanned %d apps using PowerShell method.", len(apps))
    return data


async def vortex_scan_apps() -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, _scan_apps_sync)
    return {"ok": True, "message": f"{len(data.get('apps', {}))} apps indexed.", "data": data}


def _load_apps() -> Dict[str, Any]:
    data = load_json(APPS_JSON_PATH, default={"apps": {}})
    if not data.get("apps"):
        data = _scan_apps_sync()
    return data


def _score_match(key: str, query: str) -> float:
    """Score how well `key` matches `query`. Higher = better match."""
    q = query.lower().strip()
    k = key.lower().strip()
    q_clean = re.sub(r"[^a-z0-9]", "", q)
    k_clean = re.sub(r"[^a-z0-9]", "", k)

    if k == q:                         return 1.0   # exact
    if k.startswith(q):                return 0.92  # prefix: "google chrome" starts with "chrome"? no but reverse:
    if q in k and k.startswith(q):     return 0.92
    if q in k:                         return 0.85  # substring: query inside key name
    if k in q:                         return 0.80  # key inside query
    if q_clean and q_clean in k_clean: return 0.78  # cleaned substring
    # difflib ratio
    from difflib import SequenceMatcher
    ratio = SequenceMatcher(None, q, k).ratio()
    if ratio >= 0.72:                  return ratio * 0.7
    return 0.0


def _fuzzy_find_apps(apps: Dict[str, Any], query: str) -> List[Tuple[str, Dict[str, Any], float]]:
    """Return (key, entry, score) sorted by score descending."""
    q = (query or "").lower().strip()
    scored = []
    for k, v in apps.items():
        s = _score_match(k, q)
        if s > 0:
            scored.append((k, v, s))
    scored.sort(key=lambda x: x[2], reverse=True)
    return scored


async def vortex_open_app(query: str) -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    apps_data = await loop.run_in_executor(None, _load_apps)
    apps = apps_data.get("apps", {})

    scored = _fuzzy_find_apps(apps, query)

    if not scored:
        return {"ok": False, "error": f"App '{query}' not found. I can search for it in the browser if you'd like."}

    best_key, best_entry, best_score = scored[0]

    # Auto-open if the top result is a clear winner (high confidence)
    # OR if the top score is significantly better than #2
    auto_open = False
    if best_score >= 0.85:
        auto_open = True
    elif len(scored) >= 2:
        gap = best_score - scored[1][2]
        if gap >= 0.15:  # top result is clearly better
            auto_open = True
    else:
        auto_open = True  # only one result

    if auto_open:
        key, entry = best_key, best_entry
    else:
        # Only show genuinely ambiguous candidates (within 0.15 of best score)
        threshold = best_score - 0.15
        candidates = [(k, v, s) for k, v, s in scored if s >= threshold][:4]
        names = [v.get("name", k) for k, v, s in candidates]
        opts  = [f"{i+1}. {n}" for i, n in enumerate(names)]
        return {
            "ok": False,
            "error": f"I found a few apps matching '{query}':\n" + "\n".join(opts) +
                     "\nWhich one should I open?",
        }

    path = entry.get("path")
    if not path:
        return {"ok": False, "error": f"No path for app {key}"}

    def _launch() -> None:
        try:
            if path.startswith("shell:") or path.lower().endswith(".lnk"):
                os.startfile(path)
            else:
                subprocess.Popen([path], shell=True if " " in path else False)
        except Exception:
            logging.exception("Failed launching app %s", path)
            raise

    try:
        await loop.run_in_executor(None, _launch)
        return {"ok": True, "message": f"Opening {entry.get('name') or key}."}
    except Exception as e:
        return {"ok": False, "error": f"Failed to open {entry.get('name') or key}: {e}"}


async def vortex_set_volume(percent: int) -> Dict[str, Any]:
    p = max(0, min(100, int(percent)))
    try:
        device = AudioUtilities.GetSpeakers()

        # Newer pycaw versions wrap the underlying COM device in _ctl.
        # Prefer _ctl.Activate when available; otherwise fall back to Activate.
        com_device = getattr(device, "_ctl", device)
        activate = getattr(com_device, "Activate", None)
        if activate is None:
            # pycaw version / backend does not expose Activate; fail gracefully.
            msg = "Volume control is not supported by the current audio backend/pycaw version."
            logging.warning(msg)
            return {"ok": False, "error": msg}

        interface = activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        volume.SetMasterVolumeLevelScalar(p / 100.0, None)
        return {"ok": True, "message": f"Volume set to {p}%."}
    except Exception as e:
        logging.exception("Failed setting volume")
        return {"ok": False, "error": f"Failed to set volume: {e}"}

async def vortex_close_app(query: str) -> Dict[str, Any]:
    q = (query or "").lower().strip()
    if not q:
        return {"ok": False, "error": "No app specified to close."}
        
    closed = []
    # Strip some common words
    q = q.replace(".exe", "").replace("app", "").strip()
    
    for proc in psutil.process_iter(['name']):
        try:
            pinfo = proc.info
            pname = (pinfo.get('name') or '').lower()
            if q in pname or pname.startswith(q) or q == pname.replace(".exe", ""):
                proc.terminate()
                closed.append(pname)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    if closed:
        # Avoid huge lists in message
        return {"ok": True, "message": f"Successfully closed {query}."}
    else:
        return {"ok": False, "error": f"Could not find any running app matching '{query}' to close."}


__all__ = ["vortex_scan_apps", "vortex_open_app", "vortex_close_app", "vortex_set_volume", "APPS_JSON_PATH"]

