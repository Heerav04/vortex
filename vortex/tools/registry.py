import logging
from typing import Any, Dict, Optional
from tools.base import BaseTool

class ToolRegistry:
    """
    Dynamic registry for resolving and validating tool execution.
    Replaces the hardcoded function mapping with an object-oriented approach.
    """
    def __init__(self):
        self._tools: Dict[str, Dict[str, BaseTool]] = {}
        self._auto_register()

    def _auto_register(self):
        try:
            from tools.info.time_tool import TimeTool
            # NOTE: `tools/system.py` exists (legacy module), so we cannot import `tools.system.*`
            # as a package. Keep modular wrappers at top-level to avoid import collisions.
            from tools.system_open_app_tool import OpenAppTool
            from tools.system_close_app_tool import CloseAppTool
            from tools.system_set_volume_tool import SetVolumeTool
            from tools.system_scan_apps_tool import ScanAppsTool
            from tools.filesystem.open_folder_tool import OpenFolderTool
            from tools.filesystem.open_drive_tool import OpenDriveTool
            from tools.filesystem.search_tool import SearchTool
            from tools.filesystem.search_by_size_tool import SearchBySizeTool
            from tools.filesystem.open_in_explorer_tool import OpenInExplorerTool
            from tools.info.realtime_wrappers import (NewsTool, LiveScoreTool, WeatherTool, RealtimeSearchTool, GroundedSearchTool)
            from tools.web.browser_wrappers import (OpenUrlTool, BrowserSearchTool, PlayMusicTool)
            from tools.info.screen_wrappers import (CaptureOcrTool, AnalyzeErrorTool)
            from tools.info.llm_wrappers import (LLMQATool, LLMChatTool)
            
            # Group 0
            self.register(TimeTool())
            self.register(OpenAppTool())
            self.register(CloseAppTool())
            self.register(SetVolumeTool())
            self.register(ScanAppsTool())

            # Filesystem
            self.register(OpenFolderTool())
            self.register(OpenDriveTool())
            self.register(SearchTool())
            self.register(SearchBySizeTool())
            self.register(OpenInExplorerTool())
            
            # Group 1: Realtime
            self.register(NewsTool())
            self.register(LiveScoreTool())
            self.register(WeatherTool())
            self.register(RealtimeSearchTool())
            self.register(GroundedSearchTool())
            
            # Group 2: Browser
            self.register(OpenUrlTool())
            self.register(BrowserSearchTool())
            self.register(PlayMusicTool())
            
            # Group 3: Screen
            self.register(CaptureOcrTool())
            self.register(AnalyzeErrorTool())
            
            # Group 4: LLM
            self.register(LLMQATool())
            self.register(LLMChatTool())
            
        except Exception as e:
            logging.error(f"Failed to auto-register modular tools: {e}")

    def register(self, tool: BaseTool) -> None:
        if tool.category not in self._tools:
            self._tools[tool.category] = {}
        self._tools[tool.category][tool.name] = tool
        logging.debug(f"Registered modular tool: {tool.category}.{tool.name}")

    def get_tool(self, category: str, name: str) -> Optional[BaseTool]:
        return self._tools.get(category, {}).get(name)

    async def execute(self, category: str, name: str, **kwargs: Any) -> Dict[str, Any]:
        tool = self.get_tool(category, name)
        if not tool:
            return {"ok": False, "error": f"Tool {category}.{name} not found in registry."}
            
        try:
            # Here we will add telemetry logging for tool execution duration later
            result = await tool.execute(**kwargs)
            return result
        except Exception as e:
            logging.exception(f"Tool {category}.{name} crashed during execution.")
            return {"ok": False, "error": str(e)}

# Global registry instance
registry = ToolRegistry()
