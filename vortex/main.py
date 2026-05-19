import argparse
import asyncio
import logging
import os
import signal
import threading

import aiohttp
from dotenv import load_dotenv

from core import BASE_DIR, ensure_data_dirs
from core.orchestrator import VortexConfig, VortexOrchestrator
from ui.tray import start_tray
from ui.dashboard import VortexDashboard


def setup_logging() -> None:
    log_path = BASE_DIR / "vortex.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def load_config() -> VortexConfig:
    load_dotenv()
    wake = os.getenv("VORTEX_WAKE_WORD", "vortex")
    return VortexConfig(wake_word=wake)


from ui.login import get_saved_token, VortexLogin
import sys

def main() -> None:
    parser = argparse.ArgumentParser(description="Vortex - Personal AI OS")
    parser.add_argument(
        "--mode",
        choices=["voice", "chat", "both"],
        default="both",
        help="Run Vortex in voice-only, chat-only, or both modes (default: both).",
    )
    parser.add_argument(
        "--offline-voice",
        action="store_true",
        help="Enable the high-performance offline Vosk audio listener instead of the default."
    )
    args = parser.parse_args()
    
    # ----------------------------------------------------
    # VORTEX DESKTOP APP - STANDALONE MODE
    # ----------------------------------------------------
    # (Remote Web login removed during cleanup)

    setup_logging()
    ensure_data_dirs()
    VortexLogin().prompt()
    cfg = load_config()

    # The background thread will run the asyncio event loop
    loop = asyncio.new_event_loop()
    
    def run_async_loop(l):
        asyncio.set_event_loop(l)
        l.run_forever()

    threading.Thread(target=run_async_loop, args=(loop,), daemon=True).start()

    orch = VortexOrchestrator(cfg)
    
    # Dual-Brain Verification Task
    async def verify_brains():
        logging.info("VORTEX: Initializing Dual-Brain Strategy (Gemini + Ollama)...")
        # Check Ollama
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:11434/api/tags", timeout=1) as r:
                    if r.status == 200:
                        logging.info("OLLAMA: Found local brain! Privacy + Offline mode is READY.")
                    else:
                        logging.warning("OLLAMA: Not detected. TIP: Start Ollama for 100% offline support.")
        except Exception:
             logging.warning("OLLAMA: Not detected. TIP: Start Ollama for 100% offline support.")

    # Schedule the check
    loop.call_soon_threadsafe(lambda: asyncio.run_coroutine_threadsafe(verify_brains(), loop))

    def _on_quit():
        # Stop everything
        loop.call_soon_threadsafe(loop.stop)
        db.stop()

    def _submit_from_dashboard(text: str) -> None:
        if not text.strip():
            return
        asyncio.run_coroutine_threadsafe(orch.handle_query(text, speak=True), loop)

    db = VortexDashboard(
        _submit_from_dashboard, 
        on_quit=_on_quit, 
        on_toggle_continuous=lambda state: orch.toggle_continuous_mode(state)
    )
    orch.set_ui_callback(db.add_message)
    orch.set_status_callback(db.set_status)

    # Secondary startup logic in the thread
    async def startup_sequence():
        await asyncio.sleep(1)
        db.add_message("Vortex", "Systems initialized. Neural links are active.")
        await orch.voice.speak("Vortex starting up.")
        
        # Background app scan
        try:
            from tools import system as system_tools
            await system_tools.vortex_scan_apps()
            logging.info("Background app scan complete.")
        except Exception:
            logging.exception("Initial background app scan failed")

        # Optional Offline Voice engine
        if args.offline_voice:
            try:
                from core.audio import AudioInputManager, STTManager
                audio_mgr = AudioInputManager()
                stt_mgr = STTManager()
                
                async def offline_voice_callback(text: str):
                    logging.info(f"[Offline Voice Recognized] {text}")
                    # 1. Interrupt any ongoing TTS response instantly (barge-in)
                    orch.voice.interrupt()
                    
                    # 2. Pass recognized text directly into the unified orchestrator pipeline
                    try:
                        from core.audio.transcript_normalizer import normalize_transcript
                        text = normalize_transcript(text).normalized
                    except Exception:
                        pass
                    await orch.handle_query(text, speak=True)
                    
                if stt_mgr.model:
                    asyncio.create_task(stt_mgr.process_audio_stream(audio_mgr, offline_voice_callback))
                    logging.info("Offline voice engine started in the background.")
                else:
                    logging.warning("Offline voice fallback: Model missing, disabled.")
            except Exception as e:
                logging.warning(f"Offline voice fallback: Failed to start ({e})")

        if args.mode in {"voice", "both"}:
            asyncio.create_task(orch.run_voice_forever())
        if args.mode in {"chat", "both"}:
            asyncio.create_task(orch.run_chat_forever())

    asyncio.run_coroutine_threadsafe(startup_sequence(), loop)

    # Start tray (runs in its own thread)
    start_tray(_on_quit)

    # Allow Ctrl+C to forcefully kill the blocking Tkinter/Input loops
    import signal
    def handle_sigint(sig, frame):
        print("\n[Vortex] Ctrl+C detected. Shutting down immediately...")
        _on_quit()
        os._exit(0)
    
    signal.signal(signal.SIGINT, handle_sigint)

    # Start the Dashboard on the MAIN THREAD (Blocking)
    try:
        db.start()
    except KeyboardInterrupt:
        handle_sigint(None, None)

if __name__ == "__main__":
    main()

