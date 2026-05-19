# Vortex Runbook & Troubleshooting

## 1. Planner V2 Fails to Route Commands
**Symptoms:** Vortex repeatedly falls back to basic regex routing, or logging shows `Planner V2 unavailable or error`.
**Resolution:**
- Check internet connection (Planner V2 uses Gemini).
- Check `GEMINI_API_KEY` in `.env`.
- Ensure `ENABLE_PLANNER_V2=true` in `.env`.
- Fallback: The system will automatically run via V1. No downtime will occur.

## 2. A Modular Tool Crashes
**Symptoms:** Vortex says "Tool execution failed" but does not crash.
**Resolution:**
- Use the Dashboard: Run `python -m streamlit run dashboard/app.py` and check the "Recent Failures" list.
- Check `vortex.log` in the root directory for the stack trace.
- The `ToolRegistry` isolates crashes. The orchestrator will simply skip the broken step.

## 3. Telemetry DB is Locked
**Symptoms:** `sqlite3.OperationalError: database is locked`.
**Resolution:**
- Ensure you aren't running two instances of `main.py` simultaneously.
- The Streamlit dashboard only reads data and will not lock the DB.
- Delete `vortex/data/telemetry.sqlite3` to reset the metrics tracking.

## 4. OCR / Screen Tools Fail
**Symptoms:** Vortex cannot read the screen.
**Resolution:**
- Ensure `tesseract` is installed on your Windows machine and available in the system PATH.
- If Tesseract is missing, Vortex falls back gracefully without screen context.

## 5. Offline Voice is Not Triggering
**Symptoms:** Running `--offline-voice` does nothing.
**Resolution:**
- Ensure the `vosk-model` is extracted inside `vortex/data/vosk-model/`.
- Ensure your microphone isn't locked by another application.
