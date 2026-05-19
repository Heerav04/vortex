import asyncio
import sounddevice as sd
import numpy as np
import logging

class AudioInputManager:
    """
    Manages low-latency audio capture using sounddevice.
    Buffers audio frames into an asyncio queue for the STT engine.
    """
    def __init__(self, sample_rate: int = 16000, channels: int = 1, dtype: str = 'int16'):
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.audio_queue = asyncio.Queue()
        self.stream = None
        self.is_listening = False

    def _audio_callback(self, indata: np.ndarray, frames: int, time, status: sd.CallbackFlags) -> None:
        if status:
            logging.debug(f"[Audio Status] {status}")
        
        if self.is_listening:
            try:
                loop = asyncio.get_running_loop()
                loop.call_soon_threadsafe(self.audio_queue.put_nowait, bytes(indata))
            except RuntimeError:
                pass

    def start_listening(self) -> None:
        if self.is_listening:
            return
            
        self.is_listening = True
        self.stream = sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=int(self.sample_rate / 4), # 250ms chunks to process fast speech and prevent drops
            channels=self.channels,
            dtype=self.dtype,
            callback=self._audio_callback
        )
        self.stream.start()
        logging.info("AudioInputManager started listening with 250ms latency.")

    def stop_listening(self) -> None:
        self.is_listening = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            logging.info("AudioInputManager stopped listening.")

    def flush_queue(self) -> None:
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def get_audio_chunk(self) -> bytes:
        return await self.audio_queue.get()
