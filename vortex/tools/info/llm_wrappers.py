from typing import Any, Dict
from tools.base import BaseTool
from core.llm_qa import vortex_llm_qa, vortex_llm_chat

class LLMQATool(BaseTool):
    @property
    def name(self) -> str: return "qa"
    @property
    def category(self) -> str: return "llm"
    @property
    def description(self) -> str: return "Answers questions using LLM."
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return await vortex_llm_qa(**kwargs)

class LLMChatTool(BaseTool):
    @property
    def name(self) -> str: return "chat"
    @property
    def category(self) -> str: return "llm"
    @property
    def description(self) -> str: return "Chats using LLM."
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return await vortex_llm_chat(**kwargs)
