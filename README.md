# Vortex Personal AI OS

**Vortex** is a hybrid personal AI assistant for Windows that combines cloud reasoning with offline fallback, desktop automation, voice interaction, semantic memory, and local observability in one system.

It is designed for real desktop use: launching apps, handling system controls, answering live queries, reading on-screen errors, and continuing to function even when cloud APIs are unavailable.

---

## Overview

Vortex connects natural language understanding to direct Windows actions through a modular architecture.

It uses Gemini for primary reasoning, Ollama for offline fallback, Vosk for offline speech recognition, ChromaDB for semantic memory, and SQLite for telemetry. The result is a Windows-focused assistant that can automate tasks, answer questions, and operate with graceful degradation when connectivity or API limits become a problem.

---

## Core Features

### Hybrid AI Routing
- **Planner V2:** Uses Gemini models to convert natural language and desktop context into structured JSON execution plans.
- **Model fallback cascade:** Handles quota and rate-limit failures by switching across backup Gemini models, REST fallbacks, and local models.
- **Offline local fallback:** Uses Ollama models such as `gemma3:4b` or `llama3.2` when internet or API access is unavailable.
- **Rule-based fallback:** Uses a regex-driven router for basic deterministic commands when LLMs are unavailable.
- **Personalized prompting:** Injects stored user profile context into prompts for more relevant responses.
- **Offline dictionary:** Resolves common computer science terms locally through `data/dictionary.json`.

### Voice and Audio
- **Wake word detection:** Continuously listens for the wake word “Vortex”.
- **Offline STT:** Supports local speech recognition using Vosk with `--offline-voice`.
- **Natural TTS:** Uses Microsoft Edge TTS with `en-US-JennyNeural`.
- **Barge-in interruption:** Stops active speech instantly when a new wake word or input is detected.

### Desktop UI and Tray
- **Tkinter dashboard:** Lightweight dark-themed desktop chat interface.
- **Live system state:** Shows states such as `SYSTEM ONLINE`, `LISTENING`, `THINKING`, and `READY`.
- **Responsive concurrency:** Keeps the UI responsive while async tasks and tool calls run in the background.
- **System tray support:** Minimizes to tray and supports background execution controls.

### Live Intelligence
- **Web updates:** Fetches current headlines and live information.
- **Sports lookups:** Retrieves live scores and schedules.
- **Weather queries:** Provides current weather and forecasts.
- **Grounded search:** Uses search-backed model responses for fresher answers.

### Windows Automation
- **Installed app indexing:** Scans Start Menu apps, Win32 binaries, shortcuts, and UWP apps into `data/apps.json`.
- **Fuzzy app launching:** Matches apps using exact, substring, cleaned, and fuzzy matching.
- **Volume control:** Uses `pycaw` to set and mute master volume.
- **Process management:** Uses `psutil` to find and terminate running apps.
- **Explorer and file tools:** Opens common folders and can locate files recursively.

### Productivity Modes
- **Interview mode:** Opens interview-prep resources such as Calendar, LeetCode, and system design references.
- **Study mode:** Uses profile context to open practice material for weak topics.
- **Productivity mode:** Lowers volume for focused work.
- **Gaming mode:** Adjusts the environment for entertainment use.

### Screen Awareness
- **Silent screenshots:** Captures the current desktop to `data/last_screenshot.png`.
- **OCR support:** Uses Tesseract to read on-screen text and help diagnose visible errors.

### Memory and Observability
- **Semantic memory:** Uses ChromaDB with sentence embeddings for retrieval over prior context.
- **Telemetry logging:** Stores latency, success rate, routing confidence, and model source data in SQLite.
- **Analytics dashboard:** Exposes performance insights through a Streamlit dashboard.

---

## Architecture

Vortex is organized into modular components with clear responsibilities:

1. **Orchestrator** — Runs the main assistant loop.
2. **Planner** — Converts user input into structured execution plans.
3. **Tool Registry** — Wraps system capabilities as safe tool interfaces.
4. **Memory Layer** — Stores and retrieves semantic conversation context.
5. **Telemetry Layer** — Logs performance, routing, and execution data.

See `docs/ARCHITECTURE.md` for the detailed system design.

---

## Tech Stack

- **Primary reasoning:** Gemini
- **Offline LLM fallback:** Ollama
- **Offline STT:** Vosk
- **TTS:** Edge TTS
- **Desktop UI:** Tkinter
- **System tray:** pystray, pywin32
- **Automation and system control:** PowerShell, psutil, pycaw, pyautogui
- **OCR:** Tesseract
- **Vector memory:** ChromaDB
- **Telemetry:** SQLite
- **Analytics:** Streamlit, pandas, plotly

---

## Requirements

Vortex is built specifically for **Windows 10/11**.

### Prerequisites
- **Python:** 3.12+
- **Gemini API key:** from [Google AI Studio](https://aistudio.google.com/)
- **Ollama** (optional, for offline fallback): from [Ollama](https://ollama.com/)
- **Tesseract OCR** (optional, for screen reading): from the [UB Mannheim Tesseract builds](https://github.com/UB-Mannheim/tesseract/wiki)

To pull a local Ollama model:
```powershell
ollama pull llama3.2:1b
```

---

## Installation

### Option 1: Automated Windows Setup
Run the root setup script:

```powershell
setup.bat
```

This can automate:
- virtual environment creation
- dependency installation
- launch of the setup wizard

### Option 2: Manual Setup

1. Clone the repository:
```bash
git clone https://github.com/Heerav04/Vortex.git
cd Vortex
```

2. Create and activate a virtual environment:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. Install dependencies:
```powershell
pip install -r vortex/requirements.txt
pip install streamlit pandas plotly
```

---

## Configuration

Vortex includes an interactive setup wizard, so manual configuration is usually unnecessary.

After installing dependencies, run:

```powershell
python main.py
```

If configuration is missing, the onboarding flow will guide you through:
- license and privacy acceptance
- Gemini API key setup
- Ollama fallback selection
- wake word customization
- personal profile setup

### Optional `.env` example
For manual configuration, create a `.env` file inside `vortex/`:

```ini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_PLANNER=gemini-2.0-flash
VORTEX_WAKE_WORD=vortex
OLLAMA_MODEL=gemma3:4b
OLLAMA_BASE_URL=http://127.0.0.1:11434
ENABLE_PLANNER_V2=true
EDGE_TTS_VOICE=en-US-JennyNeural
LOG_LEVEL=INFO
```

---

## Running Vortex

### Start the assistant
```powershell
python main.py
```

### Runtime modes

**Default mode:**
```powershell
python main.py --mode both
```

**Voice-only mode:**
```powershell
python main.py --mode voice
```

**Chat-only mode:**
```powershell
python main.py --mode chat
```

**Offline voice loop:**
```powershell
python main.py --offline-voice
```

### Start the analytics dashboard
Run this in a separate terminal:

```powershell
cd vortex
python -m streamlit run dashboard/app.py
```

---

## Usage Examples

### Voice workflow
1. Say **“Vortex”**.
2. Wait for the assistant to enter listening mode.
3. Speak a command such as:
   - “Open VS Code”
   - “What is the weather today?”
   - “What is this error?”
4. Vortex processes the request, responds on screen, and can read the result aloud.
5. To interrupt speech, say **“Vortex”** again or type a new query.

### Chat workflow
- Type a message in the dashboard input box.
- Press `Enter` or click **Send**.
- Minimize the app to the system tray if you want it to continue running in the background.

---

## Supported Commands

| Category | Example | Result |
|---|---|---|
| App launch | `open WhatsApp` | Finds and launches the matching app |
| App close | `close Chrome` | Terminates matching processes |
| Volume control | `set volume to 40%` | Adjusts system master volume |
| Folder access | `open downloads` | Opens a known Windows folder |
| File search | `open resume.pdf in Desktop` | Searches and opens a matching file |
| Web search | `search for Python recursion tutorials` | Opens browser search results |
| Website launch | `open youtube.com` | Opens a website directly |
| Media query | `play lo-fi music on YouTube` | Opens relevant YouTube results |
| Screen OCR | `what is this error?` | Captures screen text and analyzes it |
| Live info | `what's the latest tech news?` | Retrieves current headlines |
| Personal context | `do you know my name?` | Uses saved local profile data |
| Study macro | `study DSA` | Opens practice resources |

---

## Testing

### Run unit and routing tests
```powershell
cd vortex
$env:PYTHONPATH="."
pytest tests/
```

### Run RAG evaluation and reports
```powershell
cd vortex
python evals/run_rag_eval.py
python evals/report.py
```

---

## Repository Structure

```text
Vortex/
├── vortex/
├── dashboard/
├── data/
├── docs/
├── tests/
├── evals/
├── setup.bat
└── README.md
```

Update this tree if your folder layout changes.

---

## Roadmap

- Move Planner V2 to a fully local small language model
- Add richer local document indexing for `.pdf` and `.docx`
- Improve contextual screen understanding
- Expand offline-first capabilities
- Extend automation coverage across more Windows workflows

---

## Notes

- Vortex is a **Windows-first** project and depends on native Windows tooling such as PowerShell and platform-specific automation libraries.
- Some capabilities, including voice, OCR, and offline fallback, depend on optional local tools being installed correctly.
- Live information quality depends on external services and connectivity.

---

## License

Add your project license here, for example:

```md
This project is licensed under the MIT License - see the LICENSE file for details.
```
