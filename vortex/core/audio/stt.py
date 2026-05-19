import json
import asyncio
import logging
from typing import Callable, Awaitable
from vosk import Model, KaldiRecognizer
from core import DATA_DIR

class STTManager:
    """
    Wraps the Vosk offline acoustic model. 
    Processes continuous audio chunks and fires a callback upon recognizing a full sentence.
    """
    def __init__(self, model_path: str = str(DATA_DIR / "vosk-model"), sample_rate: int = 16000):
        self.sample_rate = sample_rate
        logging.info(f"Loading Vosk offline model from {model_path}...")
        try:
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            logging.info("Vosk model loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load Vosk model: {e}")
            self.model = None

    async def process_audio_stream(self, audio_manager, callback: Callable[[str], Awaitable[None]]) -> None:
        """
        Continuously listens to the async audio queue and processes speech-to-text live.
        Executes callback whenever a full sentence is formed.
        """
        if not self.model:
            logging.error("Cannot process stream: STT model failed to load.")
            return

        audio_manager.start_listening()
        try:
            while audio_manager.is_listening:
                data = await audio_manager.get_audio_chunk()
                
                # Push heavy audio analysis to a thread to unblock the main asyncio event loop
                loop = asyncio.get_running_loop()
                is_speech = await loop.run_in_executor(None, self.recognizer.AcceptWaveform, data)
                
                if is_speech:
                    result = await loop.run_in_executor(None, self.recognizer.Result)
                    text = json.loads(result).get("text", "").strip()
                    if text:
                        await callback(text)
        except asyncio.CancelledError:
            pass
        finally:
            audio_manager.stop_listening()
