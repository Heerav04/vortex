from typing import Any, Dict
from tools.base import BaseTool
from tools.browser import vortex_open_url, vortex_web_search, vortex_play_youtube_music

class OpenUrlTool(BaseTool):
    @property
    def name(self) -> str: return "open_url"
    @property
    def category(self) -> str: return "browser"
    @property
    def description(self) -> str: return "Opens a URL in the browser."
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return await vortex_open_url(**kwargs)

class BrowserSearchTool(BaseTool):
    @property
    def name(self) -> str: return "web_search"
    @property
    def category(self) -> str: return "browser"
    @property
    def description(self) -> str: return "Performs a web search in the browser."
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return await vortex_web_search(**kwargs)

class PlayMusicTool(BaseTool):
    @property
    def name(self) -> str: return "play_youtube_music"
    @property
    def category(self) -> str: return "browser"
    @property
    def description(self) -> str: return "Plays music on YouTube."
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return await vortex_play_youtube_music(**kwargs)
