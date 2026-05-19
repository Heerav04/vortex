from typing import Any, Dict

from tools.base import BaseTool
from tools.filesystem import vortex_search


class SearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "search"

    @property
    def category(self) -> str:
        return "filesystem"

    @property
    def description(self) -> str:
        return "Searches for files/folders by name within an optional drive/folder scope."

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return await vortex_search(**kwargs)

