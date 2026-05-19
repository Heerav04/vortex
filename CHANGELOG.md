# Changelog

## [2.1.0] - Neural Voice & Resilient Routing Update
- **Microsoft Edge TTS Integration:** Replaced legacy `pyttsx3` with high-fidelity, natural neural voice (`JennyNeural`) with full barge-in/interrupt support. Configurable via `EDGE_TTS_VOICE` in `.env`.
- **Upgraded Local Fallback:** Swapped `llama3.2` for `gemma3:4b` with optimized 45s warm-up timeouts for seamless offline execution.
- **Intelligent Website Routing:** Planner V2 now instantly routes known web platforms (YouTube, ChatGPT, Gmail, LeetCode) directly to `browser: open_url` instead of searching for local Windows `.exe` files.
- **Conversational Follow-Up Handling:** Planner V2 remembers past context to execute follow-up agreements (e.g. "yes", "sure", "ok") seamlessly when Vortex offers to search the web or open an app.
- **Robust Tool Execution:** Added strict parameter validation safety nets across all tools to prevent missing argument `TypeErrors`.

## [1.0.0] - Flagship Production Release
- **Planner V2 Overhaul:** Integrated an autonomous LLM reasoning engine utilizing Gemini to output strict JSON execution plans.
- **Proxy Fallback Implementation:** Engineered a zero-downtime fallback system degrading from Planner V2 to legacy regex routing seamlessly.
- **Evaluation Framework:** Shipped an automated `pytest` and `run_rag_eval.py` framework computing Recall@K and Intent Routing Accuracy.
- **Dashboard Metrics:** Launched a standalone Streamlit dashboard visualizing SQLite telemetry for latency, success rates, and architectural adoption.
- **Local Vector RAG:** Migrated legacy hash memory to an enterprise ChromaDB implementation for localized, privacy-first semantic recall.
- **Modular Tool Migration:** Audited and wrapped 16+ legacy capabilities into a robust Object-Oriented `ToolRegistry`.
- **Offline Audio Restructure:** Safely extracted the Vosk prototype into a non-blocking `asyncio` background loop seamlessly injected into the main orchestrator pipeline.
- **Codebase Audit:** Permanently archived obsolete FastAPI web prototypes and monolithic setup scripts to ensure a pristine, resume-ready codebase.

