# System Architecture

Vortex is designed as a modular, event-driven desktop assistant capable of hybrid (cloud/local) execution.

## End-to-End Query Flow

1. **Input Generation**: User provides input via the Text Dashboard (`main.py`) or the isolated Offline Audio Listener (`core/audio/`).
2. **Context Gathering**: The `VortexOrchestrator` triggers a background OS screenshot and OCR parse (`capture_and_ocr_text_only`) to inject visual context.
3. **Autonomous Routing (Planner V2)**: The query and screen context are passed to `VortexPlannerV2`, which queries the Gemini API using a strict JSON-schema prompt.
4. **Graceful Fallback (Planner V1)**: If Planner V2 returns low confidence, hallucinates malformed JSON, or the user lacks internet access, the orchestrator instantly falls back to `VortexPlanner` (Rule-Based Regex matching).
5. **Execution Loop**: The Orchestrator iterates over the generated `PlanStep` array, executing tools via the `ToolRegistry`.
6. **Telemetry Injection**: Every tool execution is timed in milliseconds and logged to `telemetry.sqlite3`.
7. **Response Generation**: The final action outputs are injected into `VortexMemory` (ChromaDB) and synthesized via `llm_qa` for a conversational output.

## Modular Tool Registry

The codebase transitioned from a hardcoded mapping dictionary to an OOP `ToolRegistry`. 
Every action inherits from `BaseTool` and guarantees an `async def execute(**kwargs)` contract, returning `{"ok": bool, "message": str}`.

**Categories:**
- `system`: App execution, volume control.
- `browser`: OS-level URL navigation, YouTube execution.
- `info/realtime`: API calls for weather, live scores, and news.
- `screen`: Tesseract OCR extraction.
- `llm`: Context-aware conversational capabilities.

## Failure Handling

Vortex prioritizes keeping the assistant online over throwing tracebacks.
- **Model Failure**: If Ollama goes OOM, it returns a friendly "Low Memory Mode" chat message.
- **Tool Failure**: If `system.open_app` fails to locate an app, the Registry catches the exception and returns the error gracefully to the LLM to apologize.
- **RAG Failure**: RAG operates on top of SQLite chron-logs; if ChromaDB fails, chronological history persists.
