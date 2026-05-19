from typing import Any, Dict
from tools.base import BaseTool
from tools.system import vortex_close_app

class CloseAppTool(BaseTool):
    @property
    def name(self) -> str: return "close_app"
    @property
    def category(self) -> str: return "system"
    @property
    def description(self) -> str: return "Closes a locally running Windows application."
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return await vortex_close_app(**kwargs)
