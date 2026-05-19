# Vortex Personal AI OS - Project Features & Context

This document is designed to provide comprehensive context about the **Vortex Personal AI OS**, its underlying motives, and its complete feature set. It is tailored to help AI assistants (such as Perplexity, ChatGPT, or Claude) quickly understand the architectural logic, capabilities, and goals of the codebase.

---

## 🎯 Project Motive & Core Philosophy

**The Goal:** To build a fully integrated, modular "Personal AI Operating System" that lives natively on Windows. 
Unlike typical chatbots that live in a web browser and have no access to the host machine, Vortex is designed to act as a deeply integrated desktop companion. It can "see" the screen, "hear" the user locally, launch local applications, and browse the web autonomously. 

**The Dual-Brain Architecture:** 
To balance privacy, latency, and high intelligence, Vortex employs a "Dual-Brain" strategy:
1. **Local Brain (Privacy & Speed):** Uses local, offline models (like Ollama/llama3.2 and Vosk) to handle basic intents, system controls, and acoustic transcription without sending audio or simple requests to the cloud.
2. **Cloud Brain (Deep Reasoning):** Uses cloud APIs (like Google Gemini) for complex logic, multi-step planning, coding help, and deep knowledge retrieval.

---

## ✨ Core Features & Capabilities

### 1. Advanced Desktop Automation & System Control
Vortex is granted direct access to the Windows operating system to perform tasks as the user would.
- **Smart App Launching:** Automatically indexes Windows Start Menu and Desktop shortcuts upon boot, allowing it to instantly find and launch any installed software (e.g., "Open Google Chrome", "Launch Steam").
- **Hardware Control:** Can manipulate system volume via `pycaw`, check system resources via `psutil`, and interact directly with the OS via `pywin32` and `wmi`.
- **Background Timers & Alarms:** Leverages scheduling to manage offline reminders and alarms.

### 2. Vision & Screen Context
The AI doesn't just read text; it can see what the user is doing.
- **Screen Capture:** Uses `Pillow` to capture the current state of the screen when the user asks contextual questions (e.g., "What is wrong with this code on my screen?").
- **Optical Character Recognition (OCR):** Employs `pytesseract` to read text embedded inside images or non-selectable UI elements on the screen.

### 3. Voice & Real-Time Interaction
A robust, offline-first voice interaction loop.
- **Offline Speech-to-Text (STT):** Utilizes `Vosk` acoustic models for high-fidelity audio transcription that runs entirely offline, guaranteeing microphone privacy.
- **Low-Latency Streaming:** Uses custom `PyAudio` micro-stream handlers to prevent system freezing while buffering voice inputs.
- **Text-to-Speech (TTS):** Uses `pyttsx3` for responsive, offline vocal feedback.

### 4. Autonomous Web Browsing & Search
When local knowledge is insufficient, Vortex can utilize the internet.
- **Web Automation:** Uses `Selenium` to open browsers, navigate pages, and scrape information.
- **Direct YouTube Integration:** Can autonomously search for songs/videos and immediately play the first relevant result.
- **Web Search Engine:** Integrates with tools like DuckDuckGo to pull real-time search results into the LLM context.

### 5. Memory & Context Management
Vortex remembers interactions to create a seamless conversation.
- **Short-term Memory:** Retains current chat history to maintain conversation flow.
- **Long-term Storage:** Uses local SQLite databases (`memory.db`, `assistant_history.sqlite3`) to save preferences, previous intents, and developer-friendly query logs.

### 6. "Planner" Orchestration Logic
Instead of executing the first thought that comes to mind, Vortex features a `planner.py` module.
- Breaks down complex user requests into smaller, executable steps.
- Decides whether a tool (like opening a browser vs taking a screenshot) is required before generating a final answer.

### 7. Integrated Web Platform & User Management
The ecosystem extends beyond the desktop via the `/vortex-web` component.
- **Remote Gateway:** A `FastAPI` backend serves as a secure bridge for API routing.
- **Multi-Tenant System:** Uses `SQLAlchemy` and SQLite to manage distinct user profiles, allowing the desktop app to "log in" to a remote cloud profile.
- **Security:** Fully secured with bcrypt password hashing and JSON Web Tokens (JWT).
- **Admin Dashboard:** A frontend vanilla web interface allowing administrators to manage API usage and approve users.

---

## 🏗 Sub-Module Breakdown Summary

To aid in understanding the file structure:
- `/vortex`: The main Windows desktop application, containing the UI (dashboard, system tray) and Core logic (Planner, Orchestrator, Tools).
- `/vortex-web`: The cloud-hosting backend and frontend website, meant to be deployed on a remote server to act as the central brain's API proxy.
- `/voice-assistant`: The dedicated low-level audio looping mechanics ensuring isolated STT/TTS performance.
- `/`: The root contains monolithic prototypes (`assistant.py`) and global startup scripts.
