from typing import Any, Dict

from tools.base import BaseTool
from tools.system import vortex_scan_apps


class ScanAppsTool(BaseTool):
    @property
    def name(self) -> str:
        return "scan_apps"

    @property
    def category(self) -> str:
        return "system"

    @property
    def description(self) -> str:
        return "Scans and indexes installed Windows applications."

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        # Tolerate empty kwargs / ignore extras
        return await vortex_scan_apps()

