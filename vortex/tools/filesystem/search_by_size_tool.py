from typing import Any, Dict

from tools.base import BaseTool
from tools.filesystem import vortex_search_by_size


class SearchBySizeTool(BaseTool):
    @property
    def name(self) -> str:
        return "search_by_size"

    @property
    def category(self) -> str:
        return "filesystem"

    @property
    def description(self) -> str:
        return "Searches for files by name and approximate size within an optional scope."

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        # Planner/LLM sometimes emits `size` / `approx` instead of `approx_size`
        if "approx_size" not in kwargs:
            if "size" in kwargs:
                kwargs["approx_size"] = kwargs.pop("size")
            elif "approx" in kwargs:
                kwargs["approx_size"] = kwargs.pop("approx")
        return await vortex_search_by_size(**kwargs)

