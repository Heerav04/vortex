from typing import Any, Dict

from tools.base import BaseTool
from tools.system import vortex_close_app


class CloseAppTool(BaseTool):
    @property
    def name(self) -> str:
        return "close_app"

    @property
    def category(self) -> str:
        return "system"

    @property
    def description(self) -> str:
        return "Closes a locally running Windows application."

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
            return {"ok": False, "error": "No app specified to close."}
        return await vortex_close_app(query=str(app))

