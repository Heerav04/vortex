import json
import logging
import os
import queue
import re
import sqlite3
import subprocess
import threading
import time
import traceback
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timedelta
from difflib import get_close_matches
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus

import requests
import schedule
import speech_recognition as sr
import pyttsx3
from dotenv import load_dotenv

import psutil

# Optional Windows-only extras. These are required for app scanning/opening shortcuts and volume control.
try:
    import pythoncom  # type: ignore
    import win32com.client  # type: ignore
except Exception:  # pragma: no cover
    pythoncom = None
    win32com = None

try:
    from comtypes import CLSCTX_ALL  # type: ignore
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # type: ignore
except Exception:  # pragma: no cover
    CLSCTX_ALL = None
    AudioUtilities = None
    IAudioEndpointVolume = None

try:
    import wmi  # type: ignore
except Exception:  # pragma: no cover
    wmi = None

try:
    from pytube import Search as YouTubeSearch  # type: ignore
except Exception:  # pragma: no cover
    YouTubeSearch = None


APP_INDEX_PATH = Path("apps_index.json")
HISTORY_DB_PATH = Path("assistant_history.sqlite3")
LOG_PATH = Path("assistant.log")


ALLOWED_INTENTS = {"open_app", "volume", "play_song", "set_alarm", "search", "none"}


@dataclass
class AssistantConfig:
    ollama_base_url: str
    ollama_model: str
    wake_word: str
    listen_timeout_s: float
    phrase_time_limit_s: float
    stt_backend: str
    tts_rate: int
    tts_voice_contains: str
    youtube_use_pytube: bool
    youtube_download_audio: bool
    youtube_download_dir: str
    log_level: str


def load_config() -> AssistantConfig:
    load_dotenv(override=False)

    def getenv_bool(name: str, default: bool) -> bool:
        v = os.getenv(name)
        if v is None:
            return default
        return v.strip().lower() in {"1", "true", "yes", "y", "on"}

    return AssistantConfig(
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2"),
        wake_word=os.getenv("WAKE_WORD", "").strip(),
        listen_timeout_s=float(os.getenv("LISTEN_TIMEOUT_S", "6.0")),
        phrase_time_limit_s=float(os.getenv("PHRASE_TIME_LIMIT_S", "10.0")),
        stt_backend=os.getenv("STT_BACKEND", "google").strip().lower(),  # google|sphinx|text
        tts_rate=int(os.getenv("TTS_RATE", "185")),
        tts_voice_contains=os.getenv("TTS_VOICE_CONTAINS", "").strip(),
        youtube_use_pytube=getenv_bool("YOUTUBE_USE_PYTUBE", True),
        youtube_download_audio=getenv_bool("YOUTUBE_DOWNLOAD_AUDIO", False),
        youtube_download_dir=os.getenv("YOUTUBE_DOWNLOAD_DIR", str(Path("downloads").resolve())),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


def setup_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def init_history_db(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts_utc TEXT NOT NULL,
              transcript TEXT,
              intent_json TEXT,
              action TEXT,
              result_json TEXT,
              error TEXT
            )
            """.strip()
        )
        conn.commit()


def add_history(
    db_path: Path,
    *,
    transcript: Optional[str],
    intent: Optional[Dict[str, Any]],
    action: Optional[str],
    result: Optional[Dict[str, Any]],
    error: Optional[str],
) -> None:
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "INSERT INTO history (ts_utc, transcript, intent_json, action, result_json, error) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    datetime.utcnow().isoformat(timespec="seconds") + "Z",
                    transcript,
                    json.dumps(intent, ensure_ascii=False) if intent is not None else None,
                    action,
                    json.dumps(result, ensure_ascii=False) if result is not None else None,
                    error,
                ),
            )
            conn.commit()
    except Exception:
        logging.exception("Failed writing history")


def _safe_write_json(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


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


def _resolve_lnk_target(lnk_path: Path) -> Optional[Dict[str, Any]]:
    if pythoncom is None or win32com is None:
        return None

    try:
        pythoncom.CoInitialize()
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(lnk_path))
        target = (shortcut.Targetpath or "").strip()
        args = (shortcut.Arguments or "").strip()
        working_dir = (shortcut.WorkingDirectory or "").strip()
        if not target:
            return None
        return {
            "target": target,
            "args": args,
            "working_dir": working_dir,
            "shortcut": str(lnk_path),
        }
    except Exception:
        return None
    finally:
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass


def scan_apps_to_json(out_path: Path) -> Dict[str, Any]:
    """
    Builds a lightweight app index from Start Menu / Desktop shortcuts.
    Output shape:
      {
        "generated_at": "...",
        "apps": {
           "notepad": {"type":"exe","path":"C:\\...\\notepad.exe", ...},
           "google chrome": {"type":"lnk","path":"C:\\...\\Chrome.lnk", "resolved": {...}}
        }
      }
    """
    apps: Dict[str, Any] = {}
    shortcut_dirs = _iter_shortcut_dirs()

    for root in shortcut_dirs:
        for p in root.rglob("*.lnk"):
            name = p.stem.strip()
            if not name:
                continue

            key = name.lower()
            if key in apps:
                continue

            resolved = _resolve_lnk_target(p)
            apps[key] = {
                "type": "lnk",
                "name": name,
                "path": str(p),
                "resolved": resolved,
            }

    # Add a few common built-ins as fallbacks.
    builtins = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "paint": "mspaint.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
    }
    for k, exe in builtins.items():
        apps.setdefault(k, {"type": "exe", "name": k, "path": exe})

    index = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "sources": [str(d) for d in shortcut_dirs],
        "apps": apps,
    }
    _safe_write_json(out_path, index)
    logging.info("App index generated: %s (%d apps)", out_path, len(apps))
    return index


def speak(engine: pyttsx3.Engine, text: str) -> None:
    text = (text or "").strip()
    if not text:
        return
    logging.info("Assistant says: %s", text)
    engine.say(text)
    engine.runAndWait()


def init_tts(cfg: AssistantConfig) -> pyttsx3.Engine:
    engine = pyttsx3.init()
    engine.setProperty("rate", cfg.tts_rate)
    if cfg.tts_voice_contains:
        want = cfg.tts_voice_contains.lower()
        try:
            for v in engine.getProperty("voices"):
                name = (getattr(v, "name", "") or "").lower()
                vid = (getattr(v, "id", "") or "").lower()
                if want in name or want in vid:
                    engine.setProperty("voice", v.id)
                    break
        except Exception:
            logging.exception("Failed setting voice")
    return engine


def listen_once(recognizer: sr.Recognizer, mic: sr.Microphone, cfg: AssistantConfig) -> Optional[str]:
    if cfg.stt_backend == "text":
        try:
            return input("You: ").strip()
        except EOFError:
            return None

    with mic as source:
        recognizer.pause_threshold = 0.7
        recognizer.energy_threshold = 300
        try:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
        except Exception:
            pass
        logging.info("Listening...")
        try:
            audio = recognizer.listen(
                source,
                timeout=cfg.listen_timeout_s,
                phrase_time_limit=cfg.phrase_time_limit_s,
            )
        except sr.WaitTimeoutError:
            return None

    try:
        if cfg.stt_backend == "sphinx":
            return recognizer.recognize_sphinx(audio)
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        logging.warning("STT request error: %s", e)
        return None


def _strip_wake_word(text: str, wake_word: str) -> Optional[str]:
    t = (text or "").strip()
    if not t:
        return None
    if not wake_word:
        return t

    w = wake_word.lower()
    tl = t.lower()
    if w in tl:
        # stub: accept wake word anywhere; strip first occurrence
        i = tl.find(w)
        cleaned = (t[:i] + t[i + len(w) :]).strip(" ,.-")
        return cleaned.strip() or None
    return None


OLLAMA_SYSTEM_PROMPT = """You are a Windows voice PC assistant.
Return ONLY valid JSON. No markdown, no prose.

Choose one intent from: open_app, volume, play_song, set_alarm, search, none.

Schema:
{
  "intent": "open_app|volume|play_song|set_alarm|search|none",
  "app": "string (for open_app only)",
  "volume": 0-100 (for volume only),
  "query": "string (for play_song/search only)",
  "time": "HH:MM (24h) or ISO timestamp" (for set_alarm only),
  "say": "short assistant response to speak"
}

Rules:
- If user asks to open an app, set intent=open_app and fill app with the closest app name.
- If user asks volume (up/down/mute/percent), set intent=volume and set volume 0-100.
- If user asks to play music/song, set intent=play_song and query.
- If user asks to set an alarm/reminder at a time, set intent=set_alarm and time.
- If user asks to search the web, set intent=search and query.
- If unclear, intent=none and ask a brief clarifying question in say.
""".strip()


def ollama_intent(
    cfg: AssistantConfig,
    user_text: str,
    *,
    app_index: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    apps_hint = ""
    if app_index and isinstance(app_index.get("apps"), dict):
        # Keep context small: include first N app keys.
        keys = list(app_index["apps"].keys())[:80]
        apps_hint = "Known apps (lowercase keys): " + ", ".join(keys)

    payload = {
        "model": cfg.ollama_model,
        "format": "json",
        "stream": False,
        "messages": [
            {"role": "system", "content": OLLAMA_SYSTEM_PROMPT},
            {"role": "user", "content": f"{apps_hint}\nUser: {user_text}".strip()},
        ],
        "options": {"temperature": 0.2},
    }
    url = f"{cfg.ollama_base_url}/api/chat"
    r = requests.post(url, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    content = (((data or {}).get("message") or {}).get("content") or "").strip()
    if not content:
        raise ValueError("Empty Ollama response content")

    # Robust JSON extraction (in case model returns surrounding text despite instructions).
    m = re.search(r"\{[\s\S]*\}$", content)
    raw = m.group(0) if m else content
    intent = json.loads(raw)
    if not isinstance(intent, dict):
        raise ValueError("Intent JSON must be an object")
    return intent


def _normalize_intent(intent: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(intent)
    out["intent"] = str(out.get("intent", "none")).strip().lower()
    if out["intent"] not in ALLOWED_INTENTS:
        out["intent"] = "none"
    if "volume" in out and out["volume"] is not None:
        try:
            out["volume"] = int(round(float(out["volume"])))
        except Exception:
            out["volume"] = None
    for k in ("app", "query", "time", "say"):
        if k in out and out[k] is not None:
            out[k] = str(out[k]).strip()
    return out


def _fuzzy_find_app(apps: Dict[str, Any], query: str) -> Optional[str]:
    q = (query or "").strip().lower()
    if not q:
        return None
    if q in apps:
        return q

    # Try common cleanup
    q2 = re.sub(r"[^a-z0-9 +.-]", " ", q)
    q2 = re.sub(r"\s+", " ", q2).strip()
    if q2 in apps:
        return q2

    candidates = list(apps.keys())
    matches = get_close_matches(q2, candidates, n=1, cutoff=0.55)
    return matches[0] if matches else None


def open_app(app_index: Dict[str, Any], app_name: str) -> Tuple[bool, str]:
    apps = (app_index or {}).get("apps") or {}
    if not isinstance(apps, dict) or not apps:
        return False, "App index is missing or empty."

    key = _fuzzy_find_app(apps, app_name)
    if not key:
        return False, f"I couldn't find '{app_name}' in your app list."

    entry = apps[key]
    path = entry.get("path")
    resolved = entry.get("resolved") or {}
    target = resolved.get("target") or path
    args = resolved.get("args") or ""
    working_dir = resolved.get("working_dir") or ""

    try:
        if entry.get("type") == "lnk":
            # Open the shortcut directly (best chance of correct behavior).
            os.startfile(path)  # type: ignore[attr-defined]
            return True, f"Opening {entry.get('name') or key}."

        if target:
            if args:
                cmd = [target] + _split_args(args)
                subprocess.Popen(cmd, cwd=working_dir or None)
            else:
                subprocess.Popen([target], cwd=working_dir or None)
            return True, f"Opening {entry.get('name') or key}."
    except Exception as e:
        logging.exception("Failed opening app: %s", key)
        return False, f"Failed to open {entry.get('name') or key}: {e}"

    return False, "App entry was not runnable."


def _split_args(arg_string: str) -> List[str]:
    # Minimal Windows-ish splitter: respects quoted segments.
    s = (arg_string or "").strip()
    if not s:
        return []
    return re.findall(r'"[^"]*"|\S+', s)


def set_volume_percent(percent: int) -> Tuple[bool, str]:
    percent = max(0, min(100, int(percent)))
    if AudioUtilities is None or IAudioEndpointVolume is None or CLSCTX_ALL is None:
        return False, "Volume control is unavailable (pycaw/comtypes not installed)."
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        volume.SetMasterVolumeLevelScalar(percent / 100.0, None)
        return True, f"Volume set to {percent}%."
    except Exception as e:
        logging.exception("Failed setting volume")
        return False, f"Failed to set volume: {e}"


def open_web_search(query: str) -> Tuple[bool, str]:
    q = (query or "").strip()
    if not q:
        return False, "Search query is empty."
    url = f"https://www.google.com/search?q={quote_plus(q)}"
    webbrowser.open(url)
    return True, f"Searching for {q}."


def play_song(query: str, cfg: AssistantConfig) -> Tuple[bool, str]:
    q = (query or "").strip()
    if not q:
        return False, "Song query is empty."

    # Always open YouTube search in browser (reliable).
    url = f"https://www.youtube.com/results?search_query={quote_plus(q)}"
    webbrowser.open(url)

    if not (cfg.youtube_use_pytube and YouTubeSearch is not None):
        return True, f"Searching YouTube for {q}."

    # Optional: use pytube to grab first result and optionally download audio-only stream.
    try:
        s = YouTubeSearch(q)
        results = getattr(s, "results", []) or []
        if not results:
            return True, f"Searching YouTube for {q}."
        first = results[0]
        watch_url = getattr(first, "watch_url", None)
        title = getattr(first, "title", "") or q
        if watch_url:
            webbrowser.open(watch_url)

        if cfg.youtube_download_audio:
            out_dir = Path(cfg.youtube_download_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            yt = first
            stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
            if stream:
                stream.download(output_path=str(out_dir))
                return True, f"Playing {title}. Downloaded audio to {out_dir}."
        return True, f"Playing {title}."
    except Exception as e:
        logging.exception("pytube play/download failed")
        return True, f"Searching YouTube for {q}. (Download failed: {e})"


def parse_alarm_time(time_str: str) -> Optional[datetime]:
    t = (time_str or "").strip()
    if not t:
        return None

    # Accept ISO.
    try:
        if re.match(r"^\d{4}-\d{2}-\d{2}T", t):
            dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
            return dt.replace(tzinfo=None)
    except Exception:
        pass

    # HH:MM (24h)
    m = re.match(r"^(?:at\s+)?(\d{1,2}):(\d{2})\s*$", t.lower())
    if not m:
        return None
    hh, mm = int(m.group(1)), int(m.group(2))
    if hh < 0 or hh > 23 or mm < 0 or mm > 59:
        return None

    now = datetime.now()
    dt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if dt <= now:
        dt += timedelta(days=1)
    return dt


class SchedulerThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self._stop = threading.Event()

    def run(self) -> None:
        while not self._stop.is_set():
            try:
                schedule.run_pending()
            except Exception:
                logging.exception("Scheduler error")
            time.sleep(0.5)

    def stop(self) -> None:
        self._stop.set()


def list_running_apps() -> List[str]:
    names: List[str] = []
    for p in psutil.process_iter(attrs=["name"]):
        try:
            n = (p.info.get("name") or "").strip()
            if n:
                names.append(n)
        except Exception:
            continue
    names = sorted(set(names), key=str.lower)
    return names[:200]


def wmi_top_processes() -> List[Dict[str, Any]]:
    if wmi is None:
        return []
    try:
        c = wmi.WMI()
        procs = []
        for p in c.Win32_Process()[:30]:
            procs.append({"name": p.Name, "pid": int(p.ProcessId)})
        return procs
    except Exception:
        return []


def main() -> None:
    cfg = load_config()
    setup_logging(cfg.log_level)
    init_history_db(HISTORY_DB_PATH)

    logging.info("Starting assistant (model=%s, base=%s)", cfg.ollama_model, cfg.ollama_base_url)

    # Scan apps on start.
    try:
        app_index = scan_apps_to_json(APP_INDEX_PATH)
    except Exception:
        logging.exception("App scan failed; continuing with empty index")
        app_index = {"generated_at": None, "apps": {}}

    # Start scheduler thread.
    sched = SchedulerThread()
    sched.start()

    # TTS and STT.
    tts = init_tts(cfg)
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    # Warm greeting.
    speak(tts, "Assistant ready.")

    # Main loop.
    while True:
        transcript = None
        intent = None
        action_name = None
        result = None
        error = None
        try:
            raw = listen_once(recognizer, mic, cfg)
            if raw is None:
                continue
            transcript = raw

            cleaned = _strip_wake_word(raw, cfg.wake_word)
            if cleaned is None:
                continue

            logging.info("Heard: %s", cleaned)

            # Local quick commands (no LLM roundtrip).
            if cleaned.lower() in {"quit", "exit", "goodbye"}:
                speak(tts, "Goodbye.")
                add_history(HISTORY_DB_PATH, transcript=transcript, intent={"intent": "none", "say": "quit"}, action="quit", result={"ok": True}, error=None)
                break

            if cleaned.lower() in {"what's running", "whats running", "list running apps"}:
                running = list_running_apps()
                speak(tts, f"I see {len(running)} processes running. For example: {', '.join(running[:8])}.")
                add_history(HISTORY_DB_PATH, transcript=transcript, intent={"intent": "none", "say": "list running"}, action="list_running", result={"count": len(running), "sample": running[:20]}, error=None)
                continue

            # Intent via Ollama.
            intent = ollama_intent(cfg, cleaned, app_index=app_index)
            intent = _normalize_intent(intent)
            logging.info("Intent: %s", intent)

            say = (intent.get("say") or "").strip()
            if say:
                speak(tts, say)

            it = intent.get("intent", "none")
            if it == "none":
                add_history(HISTORY_DB_PATH, transcript=transcript, intent=intent, action=None, result=None, error=None)
                continue

            if it == "open_app":
                action_name = "open_app"
                ok, msg = open_app(app_index, intent.get("app") or "")
                result = {"ok": ok, "message": msg}
                speak(tts, msg)

            elif it == "volume":
                action_name = "volume"
                vol = intent.get("volume")
                if vol is None:
                    ok, msg = False, "Tell me what volume percent you want."
                else:
                    ok, msg = set_volume_percent(int(vol))
                result = {"ok": ok, "message": msg}
                speak(tts, msg)

            elif it == "play_song":
                action_name = "play_song"
                ok, msg = play_song(intent.get("query") or "", cfg)
                result = {"ok": ok, "message": msg}
                speak(tts, msg)

            elif it == "search":
                action_name = "search"
                ok, msg = open_web_search(intent.get("query") or "")
                result = {"ok": ok, "message": msg}
                speak(tts, msg)

            elif it == "set_alarm":
                action_name = "set_alarm"
                dt = parse_alarm_time(intent.get("time") or "")
                if dt is None:
                    ok, msg = False, "I couldn't understand the alarm time. Try HH colon MM, like 07:30."
                    result = {"ok": ok, "message": msg}
                    speak(tts, msg)
                else:
                    ok, msg = True, f"Alarm set for {dt.strftime('%H:%M')}."
                    result = {"ok": ok, "message": msg, "alarm_at": dt.isoformat(timespec="seconds")}
                    speak(tts, msg)

                    def alarm_job() -> None:
                        try:
                            speak(tts, "Alarm. Time's up.")
                        except Exception:
                            logging.exception("Alarm speak failed")

                    delay = max(0.1, (dt - datetime.now()).total_seconds())
                    threading.Timer(delay, alarm_job).start()

            else:
                action_name = "none"
                result = {"ok": True, "message": "No action."}

        except KeyboardInterrupt:
            speak(tts, "Goodbye.")
            break
        except Exception as e:
            error = f"{e}\n{traceback.format_exc()}"
            logging.error("Loop error: %s", error)
            try:
                speak(tts, "Sorry, something went wrong.")
            except Exception:
                pass
        finally:
            add_history(
                HISTORY_DB_PATH,
                transcript=transcript,
                intent=intent,
                action=action_name,
                result=result,
                error=error,
            )

    try:
        sched.stop()
    except Exception:
        pass


if __name__ == "__main__":
    main()

