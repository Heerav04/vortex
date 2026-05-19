from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseTool(ABC):
    """
    Standard interface for all Vortex Tools.
    Ensures safe execution, expected schemas, and telemetry hooks.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The action name of the tool (e.g., 'open_app')."""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """The namespace or category (e.g., 'system')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """LLM-friendly description of what this tool does."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute the tool logic.
        Must return a dict containing at least {"ok": bool, "message": str}.
        """
        pass
