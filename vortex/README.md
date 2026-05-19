# 🌌 VORTEX AI — Personal AI Operating System for Windows

> A premium, voice-first AI assistant that lives on your desktop. Think **Jarvis**, but real — voice control, system integration, screen awareness, and a living memory that knows who you are.

Vortex is a full-stack AI Operating System layer designed for Windows. It combines **Gemini 2.5 Flash** intelligence, **wake-word voice control**, **deep system integration**, and a sleek **Neural Dashboard UI** into a single, cohesive experience.

---

## ✨ Feature Overview

| Category | Highlights |
|---|---|
| 🧠 **AI Brain** | Gemini 2.5 Flash (primary) → Google Search Grounding → Ollama local fallback |
| 🎙️ **Voice** | Wake-word detection ("Vortex"), Google STT, SAPI5 TTS |
| 🆕 **Real-Time** | Live news (DuckDuckGo), sports scores, market updates, weather, and time |
| 🖥️ **Dashboard** | Dark-mode Tkinter UI with real-time status, chat bubbles, and input bar |
| 🛠️ **System** | PowerShell app indexing, fuzzy app search, volume control, multi-app modes |
| 🌐 **Browser** | Google search, YouTube music, URL opening via Selenium + webbrowser |
| 👁️ **Screen** | Screenshot capture + Tesseract OCR for context-aware assistance |
| 🧬 **Memory** | SQLite interaction log, vector embeddings, user profile injection |
| 🔌 **Modes** | Interview Prep, Study, Productivity, Gaming — one command to set your environment |

---

## 🧠 Dual-Brain AI Architecture

Vortex uses a **resilient, multi-strategy AI pipeline** to guarantee a response — even offline.

```
User Query
    │
    ▼
┌─────────────────────────────────────────┐
│  Strategy 1: google-genai SDK           │
│  ┌─ gemini-2.5-flash (primary)          │
│  ├─ gemini-2.0-flash                    │
│  ├─ gemini-2.0-flash-lite              │
│  ├─ gemini-2.0-flash-001              │
│  └─ gemini-2.0-flash-lite-001         │
│  (Per-model 429 handling: if one model  │
│   is rate-limited, tries the next)      │
└─────────────┬───────────────────────────┘
              │ All models failed?
              ▼
┌─────────────────────────────────────────┐
│  Strategy 2: Direct REST API            │
│  Same model cascade via raw HTTP calls  │
│  (No SDK dependency)                    │
└─────────────┬───────────────────────────┘
              │ REST also failed?
              ▼
┌─────────────────────────────────────────┐
│  Strategy 3: Ollama Local Fallback      │
│  The "Emergency Local Brain"            │
│  (Fully offline, private, zero latency)  │
└─────────────┬───────────────────────────┘
              │
              ▼
         Response ✅
```

Vortex is designed to be **resilient**. If the cloud API goes down, it silently falls back to your local **Ollama** server running the `llama3.2` model. This ensures Vortex never says "I can't reach my brain" as long as your PC is on.

### Smart Features
- **Per-model rate-limit handling**: If `gemini-2.5-flash` hits its free-tier quota, Vortex silently moves to `gemini-2.0-flash`, and so on.
- **REST API fallback**: Even if the `google-genai` SDK breaks or has issues, Vortex can make raw HTTP calls to the Gemini API.
- **User profile injection**: Every prompt is enriched with your name, location, role, and preferences from your stored profile.
- **JSON response parsing**: If the LLM wraps its response in JSON or markdown code fences, Vortex auto-extracts the clean human text.
- **Client caching**: The Gemini client is created once and reused across all calls for optimal performance.

---

## 🎙️ Neural Voice Interface

| Feature | Detail |
|---|---|
| **Wake Word** | Say **"Vortex"** to activate (configurable via `.env`) |
| **Speech-to-Text** | Google Speech Recognition with noise isolation |
| **Text-to-Speech** | Windows SAPI5 via `pyttsx3` with thread-safe audio locking |
| **Sensitivity** | Energy threshold: `80` (hears whispers), dynamic ambient adjustment |
| **Isolation** | 1-second ambient calibration + damping ratio `0.15` + pause threshold `0.8` |

### Voice Flow
```
Idle → Wake Word Detected → Listening... → STT → Orchestrator → TTS → Idle
```

---

## 🖥️ Neural Dashboard UI

A sleek, dark-mode **Tkinter** interface with:

- **Header**: "VORTEX AI" branding with real-time status indicator
- **Status States**: `SYSTEM ONLINE` (teal), `LISTENING...` (pink), `THINKING...` (purple), `READY` (teal)
- **Chat Area**: Scrolling bubble-style conversation view with color-coded senders:
  - 🟢 **You**: Teal (`#03DAC6`)
  - 🟣 **Vortex**: Purple (`#BB86FC`)
- **Input Bar**: Dark text field with `SEND` button and `Enter` key binding
- **System Tray**: Minimizes to tray icon with quit option via `pystray`

---

## ⚡ Real-Time Intelligence

Vortex now has a dedicated **Real-Time Engine** that bridges the gap between static knowledge and live information.

| Feature | Tool | How it works |
|---|---|---|
| 📰 **News** | `realtime.news` | Scrapes the latest headlines from across the globe via DuckDuckGo news. |
| 🏏 **Live Scores** | `realtime.live_score` | Targeted search for live match scores (IPL, FIFA, NBA, etc.). |
| 🌦️ **Weather** | `realtime.weather` | Real-time temperature and forecast for your location. |
| 🕓 **Time/Date** | `realtime.time` | Instant, zero-latency local time in IST. |
| 🛰️ **Grounded Search** | `realtime.grounded` | Gemini 2.5 Flash + **Google Search Grounding** for factual accuracy. |

### Example Queries
- *"Vortex, what's the latest tech news in India?"*
- *"Vortex, show me the live IPL score."*
- *"Vortex, what's the weather today?"*
- *"Vortex, who won the match last night?"*

---

## 🛠️ Deep System Integration

### App Indexing
Vortex uses a custom **PowerShell Engine** (`Get-StartApps | ConvertTo-Json`) to index **100% of your installed applications**, including:
- ✅ Windows Store / UWP apps
- ✅ Desktop shortcuts (`.lnk`)
- ✅ Start Menu programs
- ✅ Built-in system tools (Notepad, Calculator, Paint, CMD, PowerShell)

### Smart App Matching
```
"open chrome"      → Google Chrome       (alias match)
"open whatsapp"    → WhatsApp Desktop    (substring match)
"open terminal"    → PowerShell          (alias match)
"open mail"        → Outlook             (alias match)
"open code"        → Visual Studio Code  (alias match)
```

Matching pipeline: **Exact** → **Substring** → **Cleaned alphanumeric** → **Fuzzy (`difflib`, 60% cutoff)**

### Built-in Aliases
| You Say | Opens |
|---|---|
| `chrome`, `browser` | Google Chrome |
| `mail` | Outlook |
| `terminal` | PowerShell |
| `code` | Visual Studio Code |
| `edge` | Microsoft Edge |

### Volume Control
Uses `pycaw` for direct Windows audio endpoint control:
```
"set volume to 80"  → System volume → 80%
"volume 30"          → System volume → 30%
```

---

## 🧬 Living Memory & Personalization

### User Profile
Vortex has a **hardcoded profile** (can be moved to `config.json`):
```python
name        = "Heerav Amin"
location    = "Mumbai"
role        = "CS student"
weak_areas  = ["DSA recursion", "system design"]
favorite_apps = ["VSCode", "Cursor", "Ollama", "Docker", "PostgreSQL"]
style       = "PEP8 Python, React/Next.js fullstack"
```

This profile is **injected into every LLM prompt**, so Vortex:
- Knows your name and uses it naturally
- Remembers your role and location
- Can tailor study recommendations to your weak areas

### Conversation Memory
- **SQLite-backed**: Every interaction is logged with timestamp, query, result, and mode
- **Vector embeddings**: Bag-of-words hashing into 64-dim float vectors for similarity search
- **Context window**: Last 5-10 turns of conversation are injected into every LLM prompt
- **Learning**: Results are stored with `learn()` after every interaction

### Local Dictionary
A `data/dictionary.json` provides **instant offline answers** for common terms:
```json
{
  "recursion": "Recursion is a programming technique where...",
  "python": "Python is a high-level, interpreted programming language...",
  "dsa": "Data Structures and Algorithms (DSA) are the...",
  "vortex": "Vortex is your personal AI Operating System...",
  "ollama": "Ollama is a tool that allows you to run..."
}
```
Dictionary matches are checked **before** any API call — zero latency.

---

## 🎯 Multi-Step Modes

Vortex can execute **multi-step plans** with a single command:

### Interview Prep Mode
> *"Vortex, prep AI interview"*
1. Sets mode to `interview`
2. Opens browser
3. Opens Google Calendar
4. Opens LeetCode problem set
5. Opens System Design resources on GitHub

### Study Mode
> *"Vortex, study DSA"*
1. Sets mode to `study`
2. Opens LeetCode filtered to your weakest topic (e.g., recursion)

### Productivity Mode
> *"Vortex, productivity mode"*
1. Sets mode to `productivity`
2. Lowers volume to 30%

### Gaming Mode
> *"Vortex, gaming mode"*
1. Sets mode to `gaming`
2. Raises volume to 80%

---

## 👁️ Screen Awareness (OCR)

Vortex can **see your screen** via Tesseract OCR:

- **Screenshot capture**: `pyautogui.screenshot()` saves to `data/last_screenshot.png`
- **OCR extraction**: Tesseract reads all text from the screenshot
- **Error analysis**: Say *"Vortex, what's this error?"* and it reads + analyzes what's on screen
- **Context injection**: Screen text is passed to the planner for context-aware responses

> **Note**: Requires [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) installed. Vortex auto-detects it at common Windows paths.

---

## 🗣️ Command Examples

### 💻 System Control
| Command | Action |
|---|---|
| *"Vortex, open WhatsApp"* | Opens WhatsApp via fuzzy app search |
| *"Vortex, open my terminal"* | Opens PowerShell |
| *"Vortex, set volume to 80%"* | Adjusts system volume |
| *"Vortex, refresh apps"* | Rescans installed applications |

### 🌐 Web & Media
| Command | Action |
|---|---|
| *"Vortex, search for Python tutorials"* | Opens Google search |
| *"Vortex, play some coding music"* | Opens YouTube search |
| *"Vortex, open leetcode.com"* | Opens URL in browser |

### ℹ️ Intelligence & QA
| Command | Action |
|---|---|
| *"Vortex, what is quantum physics?"* | AI-powered answer (Gemini) |
| *"Vortex, define recursion"* | Instant offline answer (dictionary) |
| *"Vortex, what can you do?"* | Lists capabilities |

### 💬 Conversational
| Command | Response Style |
|---|---|
| *"Hey Vortex!"* | Warm, personal greeting (knows your name) |
| *"hwy"* (typo) | Friendly guess: "Did you mean 'hey'?" |
| *"do you know my name?"* | "Of course! You're Heerav Amin from Mumbai" |
| *"thanks"* | Warm acknowledgment |

### 🎯 Multi-Step Modes
| Command | Action |
|---|---|
| *"Vortex, prep AI interview"* | Opens Calendar + LeetCode + System Design |
| *"Vortex, productivity mode"* | Lowers volume, sets focus environment |
| *"Vortex, gaming mode"* | Raises volume to 80% |
| *"Vortex, study DSA"* | Opens LeetCode filtered to your weak areas |

---

## 🏗️ Project Architecture

### Stable Multi-Threaded Design
```
┌──────────────────────────────────────────────────┐
│                   MAIN THREAD                     │
│         Tkinter Neural Dashboard UI               │
│    (100% responsive, never blocked by I/O)        │
└───────────────────────┬──────────────────────────┘
                        │ callbacks
┌───────────────────────▼──────────────────────────┐
│                 WORKER THREAD                     │
│              asyncio Event Loop                   │
│                                                   │
│  ┌─────────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Orchestrator │  │  Voice   │  │   Tools    │  │
│  │  (Planner)  │  │ (STT/TTS)│  │(System/LLM)│  │
│  └─────────────┘  └──────────┘  └────────────┘  │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│                   TRAY THREAD                     │
│          pystray System Tray Icon                 │
└──────────────────────────────────────────────────┘
```

### File Structure
```
vortex/
├── main.py                     # Entry point — thread bootstrap
├── .env                        # API keys & preferences
├── requirements.txt            # Python dependencies
├── deploy.bat                  # PyInstaller build script
│
├── core/
│   ├── __init__.py             # BASE_DIR, DATA_DIR, JSON helpers
│   ├── orchestrator.py         # Central query handler + response pipeline
│   ├── planner.py              # Rule-based query router (system/chat/QA/modes)
│   ├── llm_qa.py               # Gemini + Ollama LLM pipeline with fallbacks
│   ├── memory.py               # SQLite memory, vector embeddings, user profile
│   └── tools.py                # Tool registry (namespace.action routing)
│
├── tools/
│   ├── system.py               # App indexing, launching, volume control
│   ├── browser.py              # Web search, URL opening, YouTube music
│   ├── screen.py               # Screenshot + Tesseract OCR
│   └── plugins/
│       ├── __init__.py          # Plugin exports
│       └── modes.py             # Mode switching (interview, gaming, etc.)
│
├── ui/
│   ├── dashboard.py            # Tkinter Neural Dashboard
│   ├── voice.py                # Wake-word, STT, TTS
│   └── tray.py                 # System tray icon
│
└── data/
    ├── apps.json               # Indexed applications cache
    ├── config.json             # Runtime configuration
    ├── dictionary.json         # Offline QA dictionary
    ├── memory.db               # SQLite interaction history
    └── last_screenshot.png     # Latest screen capture
```

### Query Processing Pipeline
```
User Input (voice or text)
    │
    ▼
┌─────────────────┐
│  Screenshot OCR  │ ← captures screen for context
└────────┬────────┘
         ▼
┌─────────────────┐
│    Planner       │ ← routes query to correct tool
│  (Rule-based)    │
└────────┬────────┘
         ▼
┌─────────────────┐
│  Tool Registry   │ ← executes: system, llm, browser, screen, plugins
└────────┬────────┘
         ▼
┌─────────────────┐
│  JSON Cleaner    │ ← strips JSON/markdown wrappers from LLM output
└────────┬────────┘
         ▼
┌─────────────────┐
│  Memory Learn    │ ← stores interaction in SQLite + vector embedding
└────────┬────────┘
         ▼
   Dashboard + TTS  ← shows clean response + speaks it aloud
```

---

## 🚀 Getting Started

### Prerequisites
| Requirement | Version | Purpose |
|---|---|---|
| Python | 3.12+ | Runtime |
| Windows | 10/11 | OS (PowerShell, SAPI5, COM) |
| Gemini API Key | Free | Primary AI brain |
| [Ollama](https://ollama.com/) | Optional | Local AI fallback |
| [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) | Optional | Screen reading |

### Installation

1. **Clone & Create Virtual Environment**:
    ```powershell
    git clone <your-repo-url>
    cd vortex
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    ```

2. **Install Dependencies**:
    ```powershell
    pip install -r requirements.txt
    ```

3. **Get Your Free Gemini API Key**:
    - Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
    - Sign in with your Google account
    - Click **"Create API Key"** → Select or create a project
    - Copy the key (looks like `AIzaSy...`)

4. **Configure Environment**:
    Create a `.env` file in the root directory:
    ```ini
    # Voice
    VORTEX_WAKE_WORD=Vortex

    # Logging
    LOG_LEVEL=INFO

    # AI Brain Keys
    # Get a free key at https://aistudio.google.com/
    GEMINI_API_KEY=your_gemini_api_key_here
    ```

5. **Run Vortex**:
    ```powershell
    python main.py
    ```

### Run Modes
```powershell
python main.py --mode both      # Voice + Chat (default)
python main.py --mode voice     # Voice only
python main.py --mode chat      # Text chat only
```

### Optional: Setup Ollama (Local Fallback)
```powershell
# Install from https://ollama.com/
ollama pull llama3.2
# Ollama runs on http://localhost:11434 by default
```

### Optional: Build Standalone EXE
```powershell
deploy.bat
# Output: dist/Vortex.exe
# Copy to shell:startup for auto-start on boot
```

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `google-genai` | Modern Gemini API SDK (primary) |
| `google-generativeai` | Legacy Gemini SDK (not used in code, kept for compatibility) |
| `aiohttp` | Async HTTP for Ollama + REST API fallback |
| `python-dotenv` | `.env` file loading |
| `SpeechRecognition` | Google Speech-to-Text |
| `PyAudio` | Microphone capture |
| `pyttsx3` | Windows SAPI5 Text-to-Speech |
| `pycaw` + `comtypes` | Windows audio volume control |
| `psutil` | Process management |
| `pyautogui` | Screenshot capture |
| `pytesseract` + `pillow` | OCR text extraction |
| `selenium` | Browser automation (Chrome) |
| `numpy` | Vector embeddings for memory |
| `pystray` + `pywin32` | System tray icon |
| `wmi` | Windows system info |
| `duckduckgo-search` | Web search fallback |
| `schedule` | Task scheduling |

---

## 🛡️ Safety & Privacy

- **Offline-First**: Vortex can function entirely locally with Ollama — no internet required.
- **No data leaves your machine** unless processed by your configured AI provider (Gemini).
- **Screen captures** are stored locally at `data/last_screenshot.png` and never uploaded.
- **Memory** is stored in a local SQLite database — fully under your control.
- **API keys** are stored in `.env` (never committed to version control).

---

## 🔧 Troubleshooting

| Issue | Solution |
|---|---|
| `429 RESOURCE_EXHAUSTED` | Free-tier quota exhausted. Wait for daily reset or create a new API key. **Note:** Older `gemini-2.0-flash` endpoints may be quota-restricted, which is why Vortex upgraded to `gemini-2.5-flash`. |
| `gemini-1.5-flash not found (404)` | Old models are deprecated for new API keys under v1beta. Vortex now defaults to using `gemini-2.5-flash` to bypass this completely. Update your code pulling the latest repo. |
| `Cannot connect to host 127.0.0.1:11434` | Ollama isn't running. Start it with `ollama serve` or install from [ollama.com](https://ollama.com/) |
| `Tesseract not found` | Install from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) — Vortex auto-detects it |
| `PyAudio install fails` | On Windows: `pip install pipwin && pipwin install pyaudio` |
| Dashboard doesn't start | Ensure `python main.py` runs on the **main thread** — Tkinter requires it |
| Raw JSON in responses | The orchestrator now auto-parses JSON. If you see raw JSON, update to the latest code |

---

## 📝 Changelog

### v2.1 — May 2026 (Latest)
- 🗣️ **Microsoft Edge TTS Integration**: Replaced legacy `pyttsx3` with high-fidelity, natural neural voice (`JennyNeural`) with full barge-in/interrupt support. Configurable via `EDGE_TTS_VOICE` in `.env`.
- 🧠 **Upgraded Local Fallback**: Swapped `llama3.2` for `gemma3:4b` with optimized 45s warm-up timeouts for seamless offline execution.
- 🌐 **Intelligent Website Routing**: Planner V2 now instantly routes known web platforms (YouTube, ChatGPT, Gmail, LeetCode) directly to `browser: open_url` instead of searching for local Windows `.exe` files.
- 💬 **Conversational Follow-Up Handling**: Planner V2 remembers past context to execute follow-up agreements (e.g. "yes", "sure", "ok") seamlessly when Vortex offers to search the web or open an app.
- 🛡️ **Robust Tool Execution**: Added strict parameter validation safety nets across all tools to prevent missing argument `TypeErrors`.

### v2.0 — March 2025
- 🔄 **Migrated to `google-genai` SDK** — deprecated `google.generativeai` removed from active use
- 🧠 **Model cascade**: `gemini-2.5-flash` → `2.0-flash` → `2.0-flash-lite` → REST API → Ollama
- 👤 **User profile injection**: Every prompt now includes your name, role, and preferences
- 🧹 **JSON response cleaning**: Orchestrator auto-strips JSON/markdown wrappers from LLM output

### v1.0 — February 2025
- 🚀 Initial release with Gemini 2.0 Flash + Ollama fallback
- 🎙️ Wake-word voice control
- 🖥️ Neural Dashboard UI
- 🛠️ PowerShell app indexing
- 🧬 SQLite memory system

---

<p align="center">
  Designed with ❤️ by <strong>Heerav Amin</strong> for the next generation of Windows users.
</p>
