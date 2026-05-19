from typing import Any, Dict
from tools.base import BaseTool
from tools.realtime import vortex_get_time

class TimeTool(BaseTool):
    @property
    def name(self) -> str:
        return "time"

    @property
    def category(self) -> str:
        return "realtime"

    @property
    def description(self) -> str:
        return "Returns the current local date and time."

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return await vortex_get_time(**kwargs)
