from typing import Any, Dict
from tools.base import BaseTool
from tools.screen import vortex_capture_and_ocr, vortex_analyze_error

class CaptureOcrTool(BaseTool):
    @property
    def name(self) -> str: return "capture_and_ocr"
    @property
    def category(self) -> str: return "screen"
    @property
    def description(self) -> str: return "Captures screen and performs OCR."
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return await vortex_capture_and_ocr(**kwargs)

class AnalyzeErrorTool(BaseTool):
    @property
    def name(self) -> str: return "analyze_error"
    @property
    def category(self) -> str: return "screen"
    @property
    def description(self) -> str: return "Analyzes screen errors."
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return await vortex_analyze_error(**kwargs)
