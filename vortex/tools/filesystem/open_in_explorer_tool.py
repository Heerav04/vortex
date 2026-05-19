from typing import Any, Dict

from tools.base import BaseTool
from tools.filesystem import vortex_open_in_explorer


class OpenInExplorerTool(BaseTool):
    @property
    def name(self) -> str:
        return "open_in_explorer"

    @property
    def category(self) -> str:
        return "filesystem"

    @property
    def description(self) -> str:
        return "Opens a file or folder in Windows File Explorer (selects file if applicable)."

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        # Planner/LLM sometimes emits `target` instead of `path`
        if "path" not in kwargs and "target" in kwargs:
            kwargs["path"] = kwargs.pop("target")
        return await vortex_open_in_explorer(**kwargs)

