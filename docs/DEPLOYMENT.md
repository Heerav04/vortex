# Deployment & Setup Guide

## Local Installation

Vortex is designed to run locally on Windows Desktop environments.

1. **Clone & Environment**
   ```bash
   git clone <repo-url>
   cd vortex
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   pip install streamlit pandas plotly
   ```

2. **Environment Variables (`.env`)**
   Create a `.env` file in the `vortex/` directory:
   ```ini
   # Required for Planner V2 and Cloud Chat
   GEMINI_API_KEY=your_key_here
   
   # Required for Offline Fallback Mode
   OLLAMA_MODEL=llama3.2:1b
   OLLAMA_BASE_URL=http://127.0.0.1:11434
   
   # Feature Flags
   ENABLE_PLANNER_V2=true
   ```

3. **Vosk Offline Audio (Optional)**
   If you wish to use the background voice listener:
   - Download the `vosk-model-en-us-0.22-lgraph` (or similar).
   - Extract it into `vortex/data/vosk-model/`.

## Startup Sequence

**Start the Assistant:**
```bash
cd vortex
python main.py
```
*(Append `--offline-voice` to enable the Vosk microphone loop).*

**Start the Dashboard:**
```bash
cd vortex
python -m streamlit run dashboard/app.py
```

## Rollback Strategy

Vortex is built with safe defaults.
- If Planner V2 creates latency or parsing errors, disable it in `.env` (`ENABLE_PLANNER_V2=false`). The app will instantly revert to Planner V1 logic.
- If ChromaDB RAG fails, the assistant relies on standard Ollama local contexts.
