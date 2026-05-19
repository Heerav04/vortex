# Vortex Project Architecture & File Documentation

This document provides a comprehensive overview of every directory and file in the Vortex ecosystem. It explains what each file does, why it exists, and the rationale behind the tools and technologies used. **Do not remove any of these files, as they are essential for the system's modularity, functionality, and stability.**

---

## 1. Root Directory (`/`)
The root directory contains initial prototypes, overarching orchestration scripts, and global configurations.

- **`README.md`**: Contains setup instructions and documentation for the original voice assistant loop. **Why it’s used:** To help new developers quickly understand the prerequisites (like `Ollama` and `PyAudio`) and set up the foundation of the project.
- **`assistant.py`**: The original, monolithic Python script for a Windows-focused voice assistant. **Why it’s used:** It was the foundational testing ground for the STT/TTS loop, proving offline AI interactions worked before modularizing into the robust `vortex/` directory.
- **`apps_index.json`**: An automatically generated index of Windows Start Menu and Desktop shortcuts. **Why it’s used:** Allows the AI to instantly locate and launch applications without performing an expensive, slow OS-wide search every time the user says "Open Chrome."
- **`assistant_history.sqlite3`**: A local database archiving chats and commands. **Why it’s used:** To maintain continuity and short-term memory of past interactions for the baseline assistant.
- **`assistant.log`**: Standard log output for the root applications. **Why it’s used:** Critical for debugging runtime errors and tracking background events.
- **`requirements.txt`**: The global Python dependencies file. **Why it’s used:** Ensures environments can be seamlessly reproduced using `pip install -r requirements.txt`. 
- **`run_vortex_web.bat`**: A batch script to spin up the web servers. **Why it’s used:** Simplifies the developer experience by launching the `vortex-web` backend and UI automatically.
- **`.env.example`**: A template for environment variables. **Why it’s used:** It documents required configuration keys (like API bases) without exposing sensitive data to version control.

---

## 2. Vortex Desktop Application (`/vortex`)
This folder represents the modularized, production-ready desktop client (The "Personal AI OS"). It leverages a dual-brain strategy (Gemini Cloud + Local Ollama).

- **`main.py`**: The primary entry point for the Vortex OS application. **Why it’s used:** It cleanly orchestrates background threads, starts the GUI dashboard, verifying cloud tokens via UI login, and connects the core engine.
- **`build.bat`**: PyInstaller instructions to compile the app. **Why it’s used:** Packages Python code into a standalone `.exe` so end-users can run the app without installing Python.
- **`deploy.bat`**: A script to automate moving the final `.exe` to the web server's download folder. **Why it’s used:** Accelerates the deployment pipeline.
- **`Vortex_Setup.spec`**: The PyInstaller configuration file. **Why it’s used:** Tells the compiler exactly how to bundle UI assets, hide system terminals, and inject dependencies.
- **`vortex.log`**: The unified logging registry for the desktop AI. **Why it’s used:** Critical for tracing the async execution loop and monitoring crashes locally.
- **`vortex_auth.json`**: A tiny secure cache storing the user's web API token. **Why it’s used:** Provides a seamless UX by keeping the user logged into their remote web profile between restarts.
- **`models.txt` / `test_models.json`**: Configuration files tracking available LLMs. **Why it’s used:** Allows developers to hot-swap AI model configurations rapidly.
- **`err_out.txt`, `err_out2.txt`, `err_out3.txt`**: Captured compilation diagnostic streams. **Why it’s used:** Logs from the `build.bat` step, ensuring compiler crash reports are saved and resolvable.

### 2.1 Core (`/vortex/core`)
Handles the "brain" mechanisms.
- **`orchestrator.py`**: The main system conductor. **Why it’s used:** Routes user queries between speech-to-text, LLM engines, and physical tool execution. Separates business logic from the UI.
- **`planner.py`**: The step-by-step reasoning engine. **Why it’s used:** Gives the AI the ability to break complex tasks down before acting, minimizing hallucinations and errors.
- **`llm_qa.py`**: The generation wrapper. **Why it’s used:** Secures a unified API to chat with either local offline models or the Gemini platform.
- **`memory.py`**: Short/long-term context management. **Why it’s used:** Ensures contextual awareness so the user doesn't have to repeat themselves.
- **`tools.py`**: Action dispatcher. **Why it’s used:** Maps LLM "intent" strings (like `open_app`) to real Python execution functions locally.

### 2.2 Tools (`/vortex/tools`)
The actionable skills of the AI.
- **`system.py`**: OS-level tools. **Why it’s used:** Provides features like Windows volume control (`pycaw`) and application launching functions.
- **`browser.py`**: Web automation. **Why it’s used:** Allows the AI to query Google or YouTube, vastly expanding its knowledge base beyond its training cutoff.
- **`screen.py`**: Vision functions. **Why it’s used:** Captures screen context so the system can "see" what the user is working on, enabling advanced visual assistance.
- **`realtime.py`**: Audio/streaming utilities. **Why it’s used:** Required for low-latency interactions.
- **`plugins/modes.py`**: Logic for switching states. **Why it’s used:** Lets the user dynamically swap between voice-only, chat-only, or continuous interaction modes.

### 2.3 User Interface (`/vortex/ui`)
The visual frontend of the desktop app.
- **`dashboard.py`**: The central application window. **Why it’s used:** Displays chat history, AI status, and offers manual input overrides for the user.
- **`login.py`**: The authentication screen. **Why it’s used:** Secures the application and maps the desktop software to a remote web-server profile.
- **`tray.py`**: Windows System Tray integration. **Why it’s used:** Allows Vortex to run silently in the background (notification area) when the user closes the main dashboard.
- **`voice.py`**: Audio visualizers/indicators. **Why it’s used:** Gives visual feedback that the AI model is actively listening or thinking.

### 2.4 Data (`/vortex/data`)
Storage for isolated system states.
- **`apps.json`**: Current machine's app index cache.
- **`config.json`**: User-defined UI preferences and configurations.
- **`dictionary.json`**: Phonetic corrections. **Why it’s used:** Helps the STT engine recognize custom names or heavily accented words.
- **`last_screenshot.png`**: Temporary storage for `screen.py`.
- **`memory.db`**: Local SQLite database storing embeddings or structural memories.
- **`query_logs.json`**: Developer-friendly history of how the `planner.py` parsed intents.

---

## 3. Vortex Web Platform (`/vortex-web`)
The custom cloud architecture serving remote APIs, managing multi-user accounts, and hosting the web interface.

### 3.1 Backend (`/vortex-web/backend`)
- **`main.py`**: The FastAPI server. **Why it’s used:** Serves API endpoints (`/login`, `/signup`, `/chat`) with incredibly high asynchronous performance. Acts as the remote Gemini bridge.
- **`database.py`**: SQLAlchemy connection setup. **Why it’s used:** Abstracts standard SQL syntax, making database modifications scalable and safe.
- **`models.py`**: The ORM mappings (`User`, `UserMemory`, `Message`). **Why it’s used:** Defines exact data structures for the SQLite databases, providing strict schema validations protecting against corrupted data.
- **`auth.py`**: Security logic. **Why it’s used:** Handles bcrypt password hashing and JWT (JSON Web Tokens) to ensure user isolation and platform security.
- **`requirements.txt`**: Web API specific libraries (`fastapi`, `uvicorn`, etc.).
- **`.env`**: Contains backend environment configs (ignored in git). **Why it's used:** Safely stores JWT keys and API keys without revealing them.
- **`vortex_app.db`**: The production DB file tracking all web platform activity, users, and remote memories.

### 3.2 Frontend (`/vortex-web/frontend`)
- **`index.html`**: The public-facing entry point. **Why it’s used:** Communicates what the platform is and provides links to download the Windows executable.
- **`admin.html`**: Secure administrative dashboard. **Why it’s used:** Allows the "host" to approve pending user registrations, track statistics, and maintain strict control over who can utilize the Cloud APIs.

---

## 4. Voice Assistant Components (`/voice-assistant`)
Standalone, robust module specifically intended to execute the offline audio loop.
- **`backend/main.py`**: The local microphone interaction loop runner.
- **`backend/audio_manager.py`**: Micro-stream handler. **Why it’s used:** Manages buffering frames from PyAudio, ensuring low latency and preventing the system from freezing while waiting for mic input.
- **`backend/stt.py`**: Speech-to-Text inference wrapper. **Why it’s used:** Passes the raw audio chunks to the AI model to turn spoken word into raw text.
- **`models/vosk-model/`**: The offline acoustic model files. **Why it’s used:** Provides highly accurate speech recognition without sending audio to Google/Microsoft servers, guaranteeing privacy.