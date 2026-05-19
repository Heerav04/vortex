import asyncio
import logging
import os
import tempfile
import threading
from typing import Optional

import speech_recognition as sr

from core.audio.transcript_normalizer import normalize_transcript

# ── Microsoft Edge TTS — Permanent Voice ─────────────────────────────────────
# Default: Jenny Neural (natural, free Microsoft voice).
# Override via .env: EDGE_TTS_VOICE=en-US-AriaNeural (or any other Edge voice)
EDGE_VOICE = os.getenv("EDGE_TTS_VOICE", "en-US-JennyNeural")


class VortexVoice:
    """
    Wake-word + STT + TTS wrapper.
    TTS: Microsoft edge-tts (Jenny Neural) — permanent, no pyttsx3.
    STT: Google Speech Recognition via SpeechRecognition library.
    """

    def __init__(self, wake_word: str = "vortex"):
        self.wake_word = (wake_word or "vortex").lower()
        self._recognizer = sr.Recognizer()

        # --- Voice Sensitivity & Isolation Tuning ---
        self._recognizer.energy_threshold = 400
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.dynamic_energy_adjustment_damping = 0.15
        self._recognizer.dynamic_energy_ratio = 1.5
        # 1.2s pause: captures full sentence even with pauses mid-speech
        self._recognizer.pause_threshold = 1.2
        self._recognizer.non_speaking_duration = 0.6

        self._mic = sr.Microphone()
        self._tts_lock = threading.Lock()
        self._interrupted = False

    def interrupt(self) -> None:
        """Immediately cut off any currently playing TTS (barge-in support)."""
        self._interrupted = True

    async def speak(self, text: str) -> None:
        """Speak using Microsoft Edge TTS (Jenny Neural)."""
        import re
        msg = (text or "").strip()
        if not msg:
            return
        self._interrupted = False

        # Strip emojis and non-ASCII characters so TTS doesn't read out emoji descriptions
        clean_msg = re.sub(r'[^\x00-\x7F]+', '', msg).strip()
        if not clean_msg:
            clean_msg = msg

        try:
            import edge_tts

            async def _edge_speak():
                tmp = tempfile.NamedTemporaryFile(
                    suffix=".mp3", delete=False, dir=tempfile.gettempdir()
                )
                tmp.close()
                mp3_path = tmp.name
                try:
                    comm = edge_tts.Communicate(clean_msg, EDGE_VOICE)
                    await comm.save(mp3_path)
                    logging.info("Vortex says (%s): %s", EDGE_VOICE, clean_msg)

                    # pygame — best choice: supports interrupt/barge-in
                    try:
                        import pygame
                        pygame.mixer.init()
                        pygame.mixer.music.load(mp3_path)
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy():
                            if self._interrupted:
                                pygame.mixer.music.stop()
                                break
                            await asyncio.sleep(0.05)
                        pygame.mixer.music.unload()
                    except Exception:
                        # playsound fallback player (no interrupt support)
                        try:
                            from playsound import playsound
                            await asyncio.get_running_loop().run_in_executor(
                                None, playsound, mp3_path
                            )
                        except Exception:
                            os.system(f'start /wait wmplayer "{mp3_path}"')
                finally:
                    try:
                        os.unlink(mp3_path)
                    except Exception:
                        pass

            await _edge_speak()

        except Exception as e:
            logging.warning("edge-tts voice output failed (%s). Skipping audio.", e)

    async def wait_for_wake_word(self) -> None:
        """Block until the configured wake word is detected."""
        while True:
            text = await self._listen_once()
            if not text:
                continue
            if self.wake_word in text.lower():
                logging.info("Wake word detected in: %s", text)
                return

    async def listen(self) -> Optional[str]:
        """Listen for a command after the wake word."""
        return await self._listen_once()

    async def _listen_once(self) -> Optional[str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._listen_blocking)

    def _listen_blocking(self) -> Optional[str]:
        with self._mic as source:
            try:
                self._recognizer.adjust_for_ambient_noise(source, duration=1.0)
            except Exception:
                pass
            logging.info("Listening...")
            try:
                audio = self._recognizer.listen(source, timeout=6, phrase_time_limit=600)
            except Exception:
                return None
        try:
            text = self._recognizer.recognize_google(audio)
            nr = normalize_transcript(text)
            logging.info("Heard: %s", nr.raw)
            if nr.normalized != nr.raw:
                logging.info("Normalized: %s", nr.normalized)
            print(f"[Vortex heard] {nr.normalized}")
            return nr.normalized
        except Exception as e:
            logging.warning("STT error: %s", e)
            return None


__all__ = ["VortexVoice"]
