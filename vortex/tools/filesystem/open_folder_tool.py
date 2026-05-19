from typing import Any, Dict

from tools.base import BaseTool
from tools.filesystem import vortex_open_folder


class OpenFolderTool(BaseTool):
    @property
    def name(self) -> str:
        return "open_folder"

    @property
    def category(self) -> str:
        return "filesystem"

    @property
    def description(self) -> str:
        return "Opens a folder path or known folder alias (Downloads, Documents, Desktop)."

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        # Planner/LLM sometimes emits `folder` instead of `path`
        if "path" not in kwargs and "folder" in kwargs:
            kwargs["path"] = kwargs.pop("folder")
        return await vortex_open_folder(**kwargs)

