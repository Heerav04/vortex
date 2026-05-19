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
        return "Adjusts the system volume to a specified percentage."

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return await vortex_set_volume(**kwargs)
