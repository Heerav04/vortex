"""
Audio subsystem.

Important: keep imports lazy/guarded so lightweight modules (like transcript normalization)
can be imported without requiring optional native deps (e.g. sounddevice).
"""

from typing import Any

try:
    from .audio_manager import AudioInputManager  # noqa: F401
    from .stt import STTManager  # noqa: F401

    __all__ = ["AudioInputManager", "STTManager"]
except Exception:
    # Offline audio components are optional at import-time.
    __all__ = []
