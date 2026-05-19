import json
import asyncio
from typing import Callable, Awaitable
from vosk import Model, KaldiRecognizer

class STTManager:
    def __init__(self, model_path: str = "../models/vosk-model", sample_rate: int = 16000):
        self.sample_rate = sample_rate
        # Initializes Vosk Offline Model (requires downloading the vosk model into the /models dir)
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)

    async def process_audio_stream(self, audio_manager, callback: Callable[[str], Awaitable[None]]) -> None:
        """
        Continuously listens to the async audio queue and processes speech-to-text live.
        Executes callback whenever a full sentence is formed.
        """
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
        finally:
            audio_manager.stop_listening()
