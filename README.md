# Vortex Personal AI OS

**Vortex** is a flagship, production-grade hybrid AI assistant tailored for Windows environments. It bridges the gap between cloud-based reasoning (Gemini) and offline privacy (Ollama/Vosk), integrating deep desktop automation, real-time retrieval-augmented generation (RAG), and extensive telemetry tracking into a seamless user experience.

---

## 🚀 Detailed Features & Capabilities

Vortex bridges the gap between high-level language understanding and direct Windows OS execution through a modular, resilient system.

### 🧠 Resilient Dual-Brain Routing Architecture
Vortex is designed to keep you productive even when internet or external API endpoints fail. It employs a multi-strategy routing architecture:
*   **Structured Intent Routing (Planner V2):** Utilizes the `google-genai` SDK to query primary Gemini models (`gemini-2.5-flash` or `gemini-2.0-flash`). It parses natural language queries and desktop context into a validated, structured JSON execution plan defining specific tool namespaces, actions, and arguments.
*   **API Model Cascade & Rate-Limit Fallback:** Dynamically handles rate-limiting (`429 Resource Exhausted`) and quota constraints. If the primary Gemini model fails or is rate-limited, the orchestrator cascades through backup models (`gemini-2.0-flash`, `gemini-2.0-flash-lite`), raw REST HTTP API fallbacks, and local models.
*   **Privacy-First Local Fallback (Ollama):** When fully offline, Vortex shifts processing to a local language model (`gemma3:4b` or `llama3.2`) hosted via Ollama, ensuring offline availability and keeping sensitive system actions private.
*   **Rule-Based Intent Routing (Planner V1):** A high-performance regex-based router that serves as an emergency safety net. If all cloud and local LLMs are unavailable, it handles basic system requests deterministically.
*   **Personalization & User Profile Injection:** Seamlessly injects user profile data (name, academic/professional role, location, weak study areas, favorite coding technologies) into prompt templates for natural, personalized, and context-aware responses.
*   **Zero-API Offline Dictionary:** Utilizes a local definition cache (`data/dictionary.json`) to instantly resolve common computer science terms and definitions without network latency or API consumption.

### 🎙️ Hands-Free voice & High-Fidelity Audio
Designed for smooth, voice-first desktop interactions:
*   **Continuous Wake-Word Detection:** Listens continuously for the wake word *"Vortex"* using PyAudio and Google Speech Recognition, calibrated dynamically to ignore ambient room noise.
*   **Isolated Offline STT (Vosk):** Supports a background, non-blocking offline Vosk audio listener (enabled via `--offline-voice`) that processes voice requests locally without internet.
*   **Neural Text-to-Speech (Edge TTS):** Synthesizes warm, natural, and professional speech using Microsoft Edge's `en-US-JennyNeural` voice stream (replacing robotic, legacy SAPI5 voices).
*   **Barge-In Speech Interruption:** Tracks active speech output using thread-safe locking and `pygame.mixer` to instantly interrupt and silence active speech synthesis the moment a new user input or wake-word is detected.

### 🖥️ Responsive Neural Dashboard UI & System Tray
A lightweight, modern visual interface designed to keep you informed of system status:
*   **Modern Dark Theme:** Engineered using vanilla Tkinter, featuring bubble-style chat streams color-coded with high-contrast palette elements (teal `#03DAC6` for the user, purple `#BB86FC` for Vortex).
*   **Brain State Visualizer:** A dynamic visual header that updates in real-time (`SYSTEM ONLINE`, `LISTENING...`, `THINKING...`, `READY`) based on background async operations.
*   **Non-Blocking Concurrency:** Completely decouples UI redraws on the main thread from long-running async event loops (`asyncio`) and system-call workers, preventing window freezing.
*   **System Tray Companion:** Minimizes cleanly to the taskbar tray using `pystray` and `pywin32` for quick background toggles and clean daemon termination.

### ⚡ Real-Time Intelligence Engine
Keeps Vortex connected to current global information feeds:
*   **Live Web Scraping:** Scrapes headlines, current events, and local information feeds directly using DuckDuckGo News API.
*   **Real-Time Sports & Scores:** Retrieves live sports scores and schedules (such as IPL, Cricket, Football, NBA) via targeted queries.
*   **Dynamic Weather Feed:** Automatically gets live local weather conditions and multi-day forecasting.
*   **Google Search Grounding:** Integrates native search grounding for Gemini endpoints to provide verified, fact-checked answers for live information.

### 🛠️ Deep Windows OS Automation & Registry
Gives the assistant hands-on control over your local environment:
*   **PowerShell App Indexer:** Scans and caches 100% of installed applications, Win32 binaries, Start Menu shortcuts (`.lnk`), and Microsoft Store UWP applications via direct PowerShell `Get-StartApps` serialization to `data/apps.json`.
*   **Fuzzy Search App Matcher:** Uses a multi-layered match search (Exact → Substring → Cleaned alphanumeric → Fuzzy `difflib.SequenceMatcher` at 60% cutoff) to launch target apps instantly, even if spelled incorrectly.
*   **Hardware COM endpoint control:** Integrates `pycaw` to directly set, mute, and adjust master audio volume.
*   **Active Process Control:** Scans and kills background tasks (e.g. Chrome, WhatsApp) via `psutil`.
*   **Explorer & File Operations:** Opens specific directories (Downloads, Documents, Desktop) or recursively searches specific scopes (`filesystem.find_and_open`) to open target documents.

### 🎯 Multi-Step Productivity Modes
Combine multiple desktop actions and workspaces into custom macros:
*   **Interview Prep Mode:** Sets mode to `interview`, opens Google Calendar, LeetCode problemsets, and GitHub System Design docs.
*   **Study Mode:** Automatically reads your weakest topic from your profile (e.g. DSA recursion) and opens LeetCode practice pages.
*   **Productivity Mode:** Enforces a quiet workspace by lowering master volume to 30%.
*   **Gaming Mode:** Sets focus environment and increases volume to 80%.

### 👁️ Screen Awareness (Computer Vision)
Allows Vortex to see what you see:
*   **Silent Desktop Capture:** Takes silent high-resolution screenshot buffers using `pyautogui` saved to `data/last_screenshot.png`.
*   **Tesseract OCR Analysis:** Extracts raw text from screenshots. When you ask *"Vortex, what is this error?"*, it reads the screen, analyzes IDE compile issues or crash traces, and resolves them instantly.

### 🧬 Semantic memory & Observability
*   **ChromaDB Vector Store:** Integrates a local vector database running `all-MiniLM-L6-v2` sentence embeddings for semantic search over past conversation contexts.
*   **SQLite Metric Logs:** Maintains logs of tool latency, success rates, routing confidences, and model sources inside `data/telemetry.sqlite3`.
*   **Streamlit Analytics:** Visualizes system performance in a separate data science dashboard (`dashboard/app.py`).

---

## 📂 Architecture Summary

The Vortex ecosystem is cleanly separated into high-cohesion, low-coupling modules:
1. **Orchestrator:** The central nervous system executing the user intent loop.
2. **Planner:** The reasoning engine parsing user queries into actionable JSON plans.
3. **Tool Registry:** The execution layer wrapping underlying business logic into safe `BaseTool` classes.
4. **Memory:** The local ChromaDB vector store.
5. **Telemetry:** The SQLite event logger capturing millisecond latency and success flags.

*(See `docs/ARCHITECTURE.md` for a comprehensive system diagram.)*

---

## 🛠️ Setup & Installation

### 📋 Prerequisites
Vortex is specifically engineered for **Windows 10/11** systems, leveraging native Windows APIs, PowerShell, and SAPI5/Edge interfaces.
*   **Python:** Version 3.12+ is recommended.
*   **API Keys:** A free Gemini API Key from [Google AI Studio](https://aistudio.google.com/).
*   **Ollama (Optional, for offline fallback):** Install from [Ollama.com](https://ollama.com/) and pull your model of choice:
    ```powershell
    ollama pull llama3.2:1b
    ```
*   **Tesseract OCR (Optional, for screen reading/debugging):** Download the installer from the [Tesseract GitHub Wiki](https://github.com/UB-Mannheim/tesseract/wiki) and install it. Vortex automatically scans standard system paths to detect the engine.

### 📥 Automated Windows Installation

If you are on Windows, you can automate virtual environment creation, package installation, and the launch of the Setup Wizard by double-clicking the root `setup.bat` file, or running it from your terminal:
```powershell
setup.bat
```

### 🌐 Web Installer (For Website Integration)

If you are packaging Vortex as a downloadable Windows App for a website:
1. Provide the lightweight **`vortex_installer.bat`** file as your download target (which you can compile to a standalone `.exe` using any free Bat-to-Exe compiler).
2. Edit `vortex_installer.bat` and ensure `REPO_ZIP_URL` points to your repository's zip link: `https://github.com/Heerav04/Vortex/archive/refs/heads/main.zip`.
3. When a user runs the installer:
   * It creates a secure local installation folder (`%USERPROFILE%\VortexAI`).
   * It downloads your repository code directly from GitHub and extracts it.
   * It automatically runs the environment initializer (`setup.bat`) and launches the onboarding wizard.
   * It creates a clickable **Vortex AI OS** shortcut directly on the user's Desktop for easy subsequent launches.

### 📥 Manual Step-by-Step Installation

If you prefer manual installation:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Heerav04/Vortex.git
    cd Vortex
    ```

2.  **Set Up a Python Virtual Environment:**
    ```powershell
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    ```

3.  **Install Core & Dashboard Dependencies:**
    ```powershell
    pip install -r vortex/requirements.txt
    pip install streamlit pandas plotly
    ```

### ⚙️ Environment Configuration (Automated Wizard)

Vortex now ships with an **automatic, interactive Setup Wizard**. You do **not** need to create or edit the `.env` or `data/config.json` files manually! Simply install the dependencies and run `python main.py`—the wizard will open to guide you through the process.

For manual configuration or reference, a `.env` file can be created in the `vortex/` directory with the following variables:
```ini
# Core AI API Keys
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_PLANNER=gemini-2.0-flash

# Wake Word Settings
VORTEX_WAKE_WORD=vortex

# Offline Fallback Local Models
OLLAMA_MODEL=gemma3:4b
OLLAMA_BASE_URL=http://127.0.0.1:11434

# Features Configuration
ENABLE_PLANNER_V2=true
EDGE_TTS_VOICE=en-US-JennyNeural
LOG_LEVEL=INFO
```

---

## 💻 Running Vortex

### 1. First-Time Start: Interactive Setup & Onboarding Wizard
When you run Vortex for the first time (or when configuration keys are missing), the app launches a multi-step **Onboarding Setup Wizard**:
*   **Step 1: License & Privacy Agreement:** Review the EULA detailing offline data privacy (voice recordings, screen OCR frames, and memories are stored purely locally). Check the acceptance box to proceed.
*   **Step 2: Model & Key Configuration:** Paste your **Gemini API Key** (with a helper link to Google AI Studio to retrieve a free key), choose your local Ollama model fallback (`gemma3:4b`, `llama3.2:1b`, or disable fallback), and customize your system wake word. The wizard automatically writes these configurations into your `.env` file.
*   **Step 3: Personal Profile Context:** Fill in your name, location, profession, weak areas, and favorite tools.
*   Click **Complete Setup**—this saves your profile to `data/config.json` and immediately launches the main dashboard.

### 2. Launching the Assistant
Once setup is complete, running the orchestrator from the `vortex/` directory starts the assistant directly:
```powershell
python main.py
```

#### Run-time Modes:
You can customize how Vortex starts up by using terminal argument flags:
*   **Default Mode (Voice + Chat UI):**
    ```powershell
    python main.py --mode both
    ```
*   **Voice-Only Mode (Zero UI):**
    ```powershell
    python main.py --mode voice
    ```
*   **Chat-Only Mode (Interactive GUI, mic disabled):**
    ```powershell
    python main.py --mode chat
    ```
*   **Local Offline STT Voice Loop:**
    ```powershell
    python main.py --offline-voice
    ```

### 3. Launching the Streamlit Analytics Dashboard
Run this in a separate command window to view real-time latency, routing efficiency, and tool usage logs:
```powershell
cd vortex
python -m streamlit run dashboard/app.py
```

---

## 🎮 How to Use & Interact with Vortex

Once Vortex is running, you can interact with it using your voice, keyboard, or system tray.

### 🎙️ Using Voice Commands
1.  Say the wake word **"Vortex"**.
2.  The status indicator in the UI will change to `LISTENING...`.
3.  Speak your command clearly (e.g., *"Vortex, what is the weather today?"* or *"Vortex, open VS Code"*).
4.  Vortex will process the query, update its status, print the answer, and read it aloud.
5.  **Barge-in Interruption:** If Vortex is speaking a long answer and you want to stop it or give a new command, simply say **"Vortex"** again (or type a query). The speaker output will immediately stop.

### 💬 Using the Chat Dashboard
*   Type your query in the bottom text entry box and press `Enter` or click **Send**.
*   View the conversation scroll back where system messages and answers are displayed.
*   **Minimize to System Tray:** Click the window's close button or tray toggles. Vortex continues running in the background. Right-click the system tray icon in the Windows taskbar task section to restore the dashboard or quit the application.

### ⚙️ Command Formulas & Scenarios

| Intent Category | Say or Type... | What Happens Under the Hood |
| :--- | :--- | :--- |
| **System Control** | *"open WhatsApp"* or *"open Chrome"* | Scans Start Menu apps, matches, and starts it. |
| **System Termination**| *"close Chrome"* or *"kill WhatsApp"* | Searches the process tree for match and kills it. |
| **Audio Volume** | *"set volume to 40%"* or *"volume 80"* | Uses pycaw COM hooks to scale master audio volume. |
| **File Operations** | *"open downloads"* or *"open desktop"* | Directly launches standard explorer paths. |
| **Recursive Finder** | *"open resume.pdf in Desktop"* | Searches Desktop folders recursively to locate and launch the file. |
| **Browser Searches** | *"search for Python recursion tutorials"*| Opens default browser to a Google Search page. |
| **Quick Websites** | *"open youtube.com"* or *"open leetcode"*| Opens targeted web URLs directly. |
| **Music Streaming** | *"play lo-fi music on YouTube"* | Loads a YouTube search result list with lo-fi music. |
| **Screen Reading** | *"what is this error?"* | Captures screen buffer, runs Tesseract OCR, parses error messages, and debugs them using the LLM. |
| **Real-time feeds** | *"what's the latest tech news?"* | Scrapes DuckDuckGo news and reports the headlines. |
| **Personalization** | *"do you know my name?"* | Recalls stored local configuration parameters. |
| **Study Macro** | *"study DSA"* | Reads weak area from profile and opens practice pages. |

---

## 🧪 Testing & Evaluation

Vortex ships with a robust, deterministic evaluation framework testing routing accuracy, tool extraction, and local RAG precision.

**Run Unit & Routing Tests:**
```bash
cd vortex
$env:PYTHONPATH="."  # For Windows PowerShell
pytest tests/
```

**Run RAG & Metric Reports:**
```bash
cd vortex
python evals/run_rag_eval.py
python evals/report.py
```

---

## 🔮 Future Improvements

- Migrate to an entirely local SLM (Small Language Model) for Planner V2 to remove Gemini latency.
- Introduce continuous background screen analysis for contextual intent anticipation.
- Add dynamic RAG document indexing over local `.pdf` and `.docx` files.
#   V o r t e x  
 