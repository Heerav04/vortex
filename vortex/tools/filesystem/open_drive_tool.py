from typing import Any, Dict

from tools.base import BaseTool
from tools.filesystem import vortex_open_drive


class OpenDriveTool(BaseTool):
    @property
    def name(self) -> str:
        return "open_drive"

    @property
    def category(self) -> str:
        return "filesystem"

    @property
    def description(self) -> str:
        return "Opens a drive letter in File Explorer (e.g. C:, D:)."

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        # Planner/LLM sometimes emits `drive_letter`
        if "drive" not in kwargs and "drive_letter" in kwargs:
            kwargs["drive"] = kwargs.pop("drive_letter")
        return await vortex_open_drive(**kwargs)

