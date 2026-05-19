import logging
from typing import Any, Awaitable, Callable, Dict

from tools import browser as browser_tools
from tools import filesystem as filesystem_tools
from tools import screen as screen_tools
from tools import system as system_tools
from tools import plugins as plugin_tools
from tools import realtime as realtime_tools
from core import llm_qa as llm_tools

ToolFunc = Callable[..., Awaitable[Dict[str, Any]]]


class VortexToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, ToolFunc]] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register("system", "open_app", system_tools.vortex_open_app)
        self.register("system", "close_app", system_tools.vortex_close_app)
        self.register("system", "set_volume", system_tools.vortex_set_volume)
        self.register("system", "scan_apps", system_tools.vortex_scan_apps)

        self.register("filesystem", "open_drive", filesystem_tools.vortex_open_drive)
        self.register("filesystem", "open_folder", filesystem_tools.vortex_open_folder)
        self.register("filesystem", "search", filesystem_tools.vortex_search)
        self.register("filesystem", "search_by_size", filesystem_tools.vortex_search_by_size)
        self.register("filesystem", "open_in_explorer", filesystem_tools.vortex_open_in_explorer)
        self.register("filesystem", "find_and_open", filesystem_tools.vortex_find_and_open)

        self.register("screen", "capture_and_ocr", screen_tools.vortex_capture_and_ocr)
        self.register("screen", "analyze_error", screen_tools.vortex_analyze_error)

        self.register("browser", "open_url", browser_tools.vortex_open_url)
        self.register("browser", "web_search", browser_tools.vortex_web_search)
        self.register("browser", "play_youtube_music", browser_tools.vortex_play_youtube_music)

        self.register("plugins", "set_mode", plugin_tools.vortex_set_mode)

        # LLM Brain (Gemini + Ollama fallback)
        self.register("llm", "qa", llm_tools.vortex_llm_qa)
        self.register("llm", "chat", llm_tools.vortex_llm_chat)

        # Real-time tools
        self.register("realtime", "time", realtime_tools.vortex_get_time)
        self.register("realtime", "news", realtime_tools.vortex_news)
        self.register("realtime", "live_score", realtime_tools.vortex_live_score)
        self.register("realtime", "weather", realtime_tools.vortex_weather)
        self.register("realtime", "search", realtime_tools.vortex_web_search_realtime)
        self.register("realtime", "grounded", realtime_tools.vortex_grounded_search)

    def register(self, namespace: str, name: str, func: ToolFunc) -> None:
        self._tools.setdefault(namespace, {})[name] = func

    async def execute(self, namespace: str, name: str, **params: Any) -> Dict[str, Any]:
        # Planner compatibility: normalize common alternate parameter names.
        if namespace == "system" and name == "open_app":
            if "query" not in params and "app_name" in params:
                params["query"] = params.pop("app_name")
            if "query" not in params or not params["query"]:
                return {"ok": False, "error": "No app name specified to open."}

        if namespace == "system" and name == "close_app":
            if "query" not in params and "app_name" in params:
                params["query"] = params.pop("app_name")
            if "query" not in params or not params["query"]:
                return {"ok": False, "error": "No app name specified to close."}

        if namespace == "system" and name == "set_volume":
            if "percent" not in params:
                params["percent"] = 50

        if namespace == "llm" and name in {"chat", "qa"}:
            if "query" not in params and "message" in params:
                params["query"] = params.pop("message")
            if "query" not in params or not params["query"]:
                params["query"] = "Hello"

        if namespace == "filesystem" and name in {"search", "find_and_open"}:
            if "query" not in params and "file_name" in params:
                params["query"] = params.pop("file_name")
            if "query" not in params or not params["query"]:
                return {"ok": False, "error": "No file name specified to search."}

        if namespace == "browser" and name == "open_url":
            if "url" not in params:
                return {"ok": False, "error": "No URL specified to open."}

        if namespace == "browser" and name == "web_search":
            if "query" not in params or not params["query"]:
                return {"ok": False, "error": "No search query specified."}

        ns = self._tools.get(namespace)
        if not ns or name not in ns:
            msg = f"Unknown tool {namespace}.{name}"
            logging.error(msg)
            return {"ok": False, "error": msg}
        try:
            return await ns[name](**params)
        except Exception as e:
            logging.exception("Tool %s.%s failed", namespace, name)
            return {"ok": False, "error": str(e)}


__all__ = ["VortexToolRegistry"]

