# Vortex Architecture Update - Context for AI Assistants

*This document is intended to provide AI assistants (like Perplexity, Claude, or ChatGPT) with a clear update on the recent massive architectural changes, code cleanups, and codebase audits performed on the Vortex Personal AI OS.*

---

## 1. The Master Audit
An exhaustive audit was conducted to transform Vortex from a prototype into a production-grade, resume-ready flagship AI project.
- **Findings:** The project possessed strong local features (Ollama local intent routing, offline STT, OS-level Python integrations like pycaw/pywin32, and OCR context). However, it suffered from codebase fragmentation (multiple entry points, monolithic legacy scripts) and lacked enterprise features (telemetry, real vector memory, evaluation metrics).
- **Target Architecture:** We planned a migration toward a clean Python package structure, merging the audio looping, introducing `ChromaDB` for Local RAG, and adding evaluation harnesses (`pytest`).

## 2. The Cleanup & Deletion Phase
To reduce clutter and focus purely on the local desktop AI assistant, aggressive cleanup was executed:
- **Archived Prototypes:** The monolithic legacy `assistant.py`, old SQLite databases, legacy logs, and the disconnected `voice-assistant` prototype directory were moved into a safe `/archive` folder.
- **Web App Deletion:** The remote cloud proxy backend and frontend (`/vortex-web`) were **permanently deleted**. The project is now solely focused on the `vortex/` local Windows OS Desktop application.
- **Setup & Installer Deletion:** All PyInstaller scripts (`build.bat`, `deploy.bat`, `.spec` files) and compile error logs were permanently deleted to declutter the workspace.
- **Decoupling Login:** `vortex/main.py` was patched to completely bypass the previous web-based authentication check. Vortex now boots entirely offline in standalone mode.

## 3. Phase 2 Implementation Started (Telemetry)
We began modifying the core structure to support staff-level AI Engineering practices:
- **Dependencies Installed:** `chromadb` (for vector storage), `sentence-transformers` (for RAG embeddings), and `pytest` (for evaluation harnesses).
- **Telemetry Module Created:** A new modular `vortex/telemetry/logger.py` was created. It uses a structured SQLite database (`telemetry.sqlite3`) to track AI system events, replacing the old, brittle `query_logs.json`.
- **Orchestrator Refactored:** `vortex/core/orchestrator.py` was patched to calculate intent-routing and tool-execution **latency in milliseconds**, logging the exact payload, tool count, and latency to the new Telemetry database.

## 4. Current State
The project now runs entirely via `cd vortex && python main.py`. 
The next immediate goals are to:
1. Rewrite `vortex/core/memory.py` to replace the "bag-of-words hash" embedding with true Local RAG via `chromadb`.
2. Introduce an Evaluation Harness using `pytest` to benchmark intent routing accuracy.
3. Merge the archived offline audio loop back into the core orchestrator.
