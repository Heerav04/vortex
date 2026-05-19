import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from tools import screen as screen_tools
from ui.voice import VortexVoice

from .memory import VortexMemory
from .planner import VortexPlan, VortexPlanner
from .planner_v2 import VortexPlannerV2
from .tools import VortexToolRegistry


@dataclass
class VortexConfig:
    wake_word: str


@dataclass
class _ExecutionContext:
    original_query: str
    screenshot_text: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None
    step_results: List[Dict[str, Any]] = field(default_factory=list)
    last_result: Optional[Dict[str, Any]] = None
    opened_path: Optional[str] = None


class VortexOrchestrator:
    def __init__(self, config: VortexConfig):
        self.config = config
        self.memory = VortexMemory()
        self.planner = VortexPlanner(self.memory)
        self.planner_v2 = VortexPlannerV2(self.memory)
        self.tools = VortexToolRegistry()
        self.voice = VortexVoice(config.wake_word)
        self._continuous_mode = False
        self._ui_callback: Callable[[str, str], None] = lambda _sender, _text: None
        self._status_callback: Callable[[str, str], None] = lambda _text, _color="#8b5cf6": None
        self._history: List[Dict[str, str]] = []

    def set_ui_callback(self, cb: Callable[[str, str], None]) -> None:
        self._ui_callback = cb

    def set_status_callback(self, cb: Callable[[str, str], None]) -> None:
        self._status_callback = cb

    def toggle_continuous_mode(self, enabled: bool) -> None:
        self._continuous_mode = bool(enabled)
        logging.info("Continuous mode: %s", "ON" if self._continuous_mode else "OFF")

    async def _build_plan(self, query: str, screenshot_text: Optional[str] = None) -> VortexPlan:
        use_v2 = os.getenv("ENABLE_PLANNER_V2", "true").lower() not in ("false", "0", "no")
        if use_v2:
            v2_result = await self.planner_v2.create_plan_async(
                query=query,
                screenshot_text=screenshot_text,
                history=self._history,
            )
            if v2_result:
                plan, confidence = v2_result
                logging.info("Planner V2 selected (confidence=%.2f): %s", confidence, plan.summary)
                return plan
        plan = self.planner.create_plan(query=query, screenshot_text=screenshot_text)
        logging.info("Rule planner fallback selected: %s", plan.summary)
        return plan

    async def _execute_plan(self, plan: VortexPlan, ctx: _ExecutionContext) -> Dict[str, Any]:
        result: Dict[str, Any] = {"ok": True, "message": plan.summary}
        for step in plan.steps:
            step_result = await self.tools.execute(step.tool, step.action, **step.params)
            ctx.step_results.append(step_result)
            ctx.last_result = step_result
            if not step_result.get("ok", False):
                return step_result
            result = step_result
        return result

    @staticmethod
    def _result_message(result: Dict[str, Any], fallback: str) -> str:
        if not result:
            return fallback
        for key in ("message", "summary", "result", "text", "answer", "response"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        data = result.get("data")
        if isinstance(data, str) and data.strip():
            return data.strip()
        if isinstance(data, dict):
            for key in ("message", "summary", "text"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        err = result.get("error")
        if isinstance(err, str) and err.strip():
            return f"Error: {err.strip()}"
        return fallback

    async def handle_query(self, query: str, speak: bool = True) -> Dict[str, Any]:
        raw_query = (query or "").strip()
        if not raw_query:
            return {"ok": False, "error": "Empty query"}

        self._ui_callback("You", raw_query)
        self._status_callback("Thinking...", "#60a5fa")

        screenshot_text: Optional[str] = None
        if any(k in raw_query.lower() for k in ("screen", "error", "screenshot")):
            try:
                screenshot_text = await screen_tools.vortex_capture_and_ocr_text_only()
            except Exception:
                logging.exception("Screen OCR capture failed")

        ctx = _ExecutionContext(
            original_query=raw_query,
            screenshot_text=screenshot_text,
            history=self._history[-10:],
        )
        plan = await self._build_plan(raw_query, screenshot_text=screenshot_text)
        result = await self._execute_plan(plan, ctx)
        response_text = self._result_message(result, plan.summary)

        self._ui_callback("Vortex", response_text)
        self._status_callback("Online", "#8b5cf6")
        self.memory.learn(raw_query, response_text, plan.mode)
        self._history.append({"role": "user", "content": raw_query})
        self._history.append({"role": "assistant", "content": response_text})

        if speak:
            try:
                await self.voice.speak(response_text)
            except Exception:
                logging.exception("Voice speak failed")

        return result

    async def run_voice_forever(self) -> None:
        logging.info("Voice loop started")
        while True:
            try:
                if not self._continuous_mode:
                    await self.voice.wait_for_wake_word()
                text = await self.voice.listen()
                if text:
                    await self.handle_query(text, speak=True)
            except asyncio.CancelledError:
                raise
            except Exception:
                logging.exception("Voice loop error")
                await asyncio.sleep(0.5)

    async def run_chat_forever(self) -> None:
        loop = asyncio.get_running_loop()
        logging.info("Console chat loop started")
        while True:
            try:
                text = await loop.run_in_executor(None, input, "You > ")
                if not text:
                    continue
                await self.handle_query(text, speak=False)
            except asyncio.CancelledError:
                raise
            except Exception:
                logging.exception("Chat loop error")
                await asyncio.sleep(0.5)


__all__ = ["VortexConfig", "VortexOrchestrator"]