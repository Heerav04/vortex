from typing import Any, Dict

from tools.base import BaseTool
from tools.system import vortex_set_volume


class SetVolumeTool(BaseTool):
    @property
    def name(self) -> str:
        return "set_volume"

    @property
    def category(self) -> str:
        return "system"

    @property
    def description(self) -> str:
        return "Sets Windows system volume to a percentage (0-100)."

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        # Canonical internal name: `percent`
        percent = None
        if "percent" in kwargs:
            percent = kwargs.pop("percent")
        elif "level" in kwargs:
            percent = kwargs.pop("level")
        elif "volume" in kwargs:
            percent = kwargs.pop("volume")

        if percent is None:
            return {"ok": False, "error": "No volume level provided."}
        return await vortex_set_volume(percent=int(percent))

