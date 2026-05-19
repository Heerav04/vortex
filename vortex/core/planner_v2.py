import json
import logging
import os
from typing import Optional

from .plan_schema import VortexPlanV2, PlanStepV2
from .memory import VortexMemory
from .llm_qa import _get_client, _gemini_available, _is_rate_limit_error, _mark_rate_limited
from .dual_brain_log import log_dual_brain_event
from .planner import VortexPlan, PlanStep

class VortexPlannerV2:
    """
    LLM-driven routing engine with strict validation. 
    It returns a structured VortexPlanV2 object.
    """
    def __init__(self, memory: VortexMemory):
        self.memory = memory

    async def create_plan_async(self, query: str, screenshot_text: Optional[str] = None, history: Optional[list] = None) -> Optional[VortexPlan]:
        """Returns a backward-compatible VortexPlan if successful, else None to trigger fallback."""
        try:
            system_prompt = """You are the intent routing engine for VORTEX AI OS.
Output a strict JSON object mapping the user's query to modular tools.

Available Tools:
- system: open_app, close_app, set_volume, scan_apps
- filesystem: open_folder, open_drive, search, search_by_size, find_and_open
- realtime: time, weather, news, live_score, search, grounded
- browser: open_url, web_search, play_youtube_music
- screen: capture_and_ocr, analyze_error
- llm: chat, qa

Rules:
1. If the user asks to "open [name]" and [name] is a known website (e.g. youtube, chatgpt, gmail, github, google, netflix, spotify, linkedin, notion, leetcode), ALWAYS use `browser` tool with action `open_url` and the correct URL (e.g. "https://youtube.com").
2. If the user asks to "open [name]" and it is a desktop app (e.g. notepad, calculator, word, excel, vscode, browser, chrome), use `system` tool with action `open_app` and params `{"query": "<app_name>"}`.
3. If the user agrees (e.g. "yes", "sure", "ok", "do it") to a previous assistant prompt offering to search the web or open a browser, look at the chat history and use `browser` tool with action `web_search` or `open_url` for the previously discussed topic.
4. If user asks to open a file in a location (examples: "open resume pdf in desktop", "open invoice in downloads"), use filesystem.find_and_open with `query`, `scope`, and `kind`.
5. For greetings ("hey", "hi", "hello", "sup") or general conversation, ALWAYS use tool "llm", action "chat", params {"query": "<user query>"}.

JSON Schema:
{
    "intent": "Brief description of user intent",
    "mode": "direct_answer" | "single_step" | "multi_step",
    "needs_internet": bool,
    "needs_memory": bool,
    "confidence": float (0.0 to 1.0),
    "summary": "Short user-friendly summary",
    "steps": [
        {
            "tool": "<namespace>",
            "action": "<tool_name>",
            "params": {"<key>": "<value>"}
        }
    ]
}"""
            import asyncio
            loop = asyncio.get_event_loop()
            
            user_msg = f"User query: {query}"
            if screenshot_text:
                user_msg += f"\nScreen context: {screenshot_text}"
            if history:
                hist_str = "\n".join([f"{msg.get('role', 'Unknown')}: {msg.get('content', '')}" for msg in history[-3:]])
                user_msg = f"Recent Chat History:\n{hist_str}\n\n{user_msg}"

            # ── Cloud brain: Gemini (primary, skipped when rate-limited) ──
            text = None
            if _gemini_available():
                client = _get_client()
                if client:
                    model = os.getenv("GEMINI_MODEL_PLANNER", "gemini-2.0-flash")
                    try:
                        response = await loop.run_in_executor(
                            None,
                            lambda: client.models.generate_content(
                                model=model,
                                contents=[system_prompt, user_msg],
                            ),
                        )
                        if response and response.text:
                            text = response.text.strip()
                            if text:
                                log_dual_brain_event(
                                    stage="planner",
                                    source="gemini",
                                    model=model,
                                    query=query,
                                    response=text,
                                    metadata={"route": "planner_v2_primary"},
                                )
                    except Exception as gemini_err:
                        if _is_rate_limit_error(gemini_err):
                            _mark_rate_limited()  # shared flag → llm_qa also skips Gemini
                        else:
                            logging.warning(
                                "Gemini planner failed (%s). Falling back to Ollama.",
                                gemini_err.__class__.__name__,
                            )
                        text = None  # ensure Ollama fallback runs
            else:
                logging.info("[Planner V2] Gemini rate-limited — using fast offline Ollama.")

            # ── Local brain: Ollama (fast offline fallback) ─────────────
            # Uses llama3.2:1b by default – the fastest model Ollama ships.
            if not text:
                ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
                ollama_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/") + "/api/generate"
                try:
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        prompt = system_prompt + "\n\n" + user_msg + "\n\nReturn ONLY valid JSON."
                        payload = {"model": ollama_model, "prompt": prompt, "stream": False}
                        async with session.post(ollama_url, json=payload, timeout=aiohttp.ClientTimeout(total=45)) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                text = (data.get("response") or "").strip()
                                if text:
                                    log_dual_brain_event(
                                        stage="planner",
                                        source="ollama",
                                        model=ollama_model,
                                        query=query,
                                        response=text,
                                        metadata={"route": "planner_v2_local_fallback"},
                                    )
                except Exception:
                    text = None

            # If both Gemini and Ollama failed or returned nothing, bail out gracefully
            if not text:
                logging.warning("[Planner V2] Both Gemini and Ollama returned nothing. Falling back to Planner V1.")
                return None

            if text.startswith("```"):
                lines = text.split("\n")
                inner_lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(inner_lines).strip()
                
            data = json.loads(text)
            
            plan_v2 = VortexPlanV2(
                intent=data.get("intent", "unknown"),
                mode=data.get("mode", "single_step"),
                needs_internet=data.get("needs_internet", False),
                needs_memory=data.get("needs_memory", False),
                confidence=float(data.get("confidence", 0.0)),
                summary=data.get("summary", "Processing..."),
                steps=[PlanStepV2(**s) for s in data.get("steps", [])]
            )
            
            if plan_v2.is_valid():
                # Cast to standard VortexPlan for backward compatibility with orchestrator
                return VortexPlan(
                    mode=plan_v2.mode,
                    summary=plan_v2.summary,
                    steps=[PlanStep(tool=s.tool, action=s.action, params=s.params) for s in plan_v2.steps]
                ), plan_v2.confidence
            else:
                logging.warning(f"Planner V2 generated invalid plan or low confidence ({plan_v2.confidence}).")
                return None
                
        except Exception as e:
            logging.error(f"Planner V2 failed: {e}")
            
        return None
