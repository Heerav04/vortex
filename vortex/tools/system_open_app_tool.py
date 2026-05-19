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
        # Canonical internal name: `app`
        app = None
        if "app" in kwargs:
            app = kwargs.pop("app")
        else:
            for k in ("app_name", "name", "target_app", "application"):
                if k in kwargs:
                    app = kwargs.pop(k)
                    break
            # Planner V1 uses `query`
            if app is None and "query" in kwargs:
                app = kwargs.pop("query")

        if app is None:
            return {"ok": False, "error": "No app specified to open."}
        return await vortex_open_app(query=str(app))

