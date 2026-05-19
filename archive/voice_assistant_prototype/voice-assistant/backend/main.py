import asyncio
from audio_manager import AudioInputManager
from stt import STTManager

async def voice_callback(text: str):
    # This fires the moment you finish speaking a sentence
    print(f"\n[USER SAID]: {text}")

async def main():
    print("Initializing STT Model (this takes a second)...")
    stt = STTManager(model_path="../models/vosk-model")
    audio = AudioInputManager()

    print("System READY. Speak into your microphone! (Press Ctrl+C to stop)")
    
    # Run the continuous audio stream into the STT manager
    try:
        await stt.process_audio_stream(audio, callback=voice_callback)
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())
