from typing import Any, Dict
from tools.base import BaseTool
from tools.realtime import (
    vortex_news, vortex_live_score, vortex_weather, 
    vortex_web_search_realtime, vortex_grounded_search
)

class NewsTool(BaseTool):
    @property
    def name(self) -> str: return "news"
    @property
    def category(self) -> str: return "realtime"
    @property
    def description(self) -> str: return "Fetches live news headlines."
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return await vortex_news(**kwargs)

class LiveScoreTool(BaseTool):
    @property
    def name(self) -> str: return "live_score"
    @property
    def category(self) -> str: return "realtime"
    @property
    def description(self) -> str: return "Fetches live sports scores."
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return await vortex_live_score(**kwargs)

class WeatherTool(BaseTool):
    @property
    def name(self) -> str: return "weather"
    @property
    def category(self) -> str: return "realtime"
    @property
    def description(self) -> str: return "Fetches current weather."
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return await vortex_weather(**kwargs)

class RealtimeSearchTool(BaseTool):
    @property
    def name(self) -> str: return "search"
    @property
    def category(self) -> str: return "realtime"
    @property
    def description(self) -> str: return "Performs a realtime web search."
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return await vortex_web_search_realtime(**kwargs)

class GroundedSearchTool(BaseTool):
    @property
    def name(self) -> str: return "grounded"
    @property
    def category(self) -> str: return "realtime"
    @property
    def description(self) -> str: return "Performs a grounded search using LLM."
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return await vortex_grounded_search(**kwargs)
