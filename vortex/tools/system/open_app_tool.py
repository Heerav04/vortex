from typing import Any, Dict
from tools.base import BaseTool
from tools.system import vortex_open_app

class OpenAppTool(BaseTool):
    @property
    def name(self) -> str:
        return "open_app"

    @property
    def category(self) -> str:
        return "system"

    @property
    def description(self) -> str:
        return "Opens a locally installed Windows application based on the user query."

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return await vortex_open_app(**kwargs)
