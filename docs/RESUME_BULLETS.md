# Resume Bullets & Portfolio Content

## Resume Bullets (ATS-Friendly)
- **Architected a local AI OS Assistant**, engineering an autonomous LLM routing engine (Planner V2) that executes multi-step JSON plans, utilizing a robust proxy-fallback pattern to ensure 100% uptime when offline.
- **Designed a modular Object-Oriented Tool Registry**, securely wrapping 15+ OS integrations (pywin32, pycaw, OCR) and capturing millisecond execution telemetry into a local SQLite database.
- **Built an automated Evaluation Framework**, leveraging PyTest and ChromaDB to continuously benchmark Intent Routing Accuracy and calculate RAG precision (Recall@K).
- **Developed a real-time Analytics Dashboard** using Streamlit and Pandas, visualizing AI tool latency, success rates, and architectural usage trends to drive data-informed system optimizations.
- **Integrated an offline-first RAG pipeline**, utilizing `all-MiniLM-L6-v2` embeddings and ChromaDB to guarantee persistent, privacy-safe semantic memory without relying on cloud APIs.

## Portfolio Description (Short / LinkedIn)
"I built Vortex AI OS—a production-grade desktop assistant that bridges cloud reasoning with offline privacy. The system features a custom LLM routing engine, a robust ChromaDB RAG memory pipeline, and an offline-first Vosk audio loop. To prove its reliability, I engineered a complete telemetry pipeline and Streamlit dashboard that visualizes tool latency and success rates in real-time."

## Portfolio Description (Technical / GitHub)
"Vortex is a hybrid AI ecosystem utilizing dual-planners (LLM + Rule-Based Fallback) to safely execute complex desktop automations. The architecture relies on an event-driven orchestrator, a modular OOP Tool Registry, and SQLite-backed telemetry. The system is heavily instrumented, featuring an automated evaluation framework computing Intent Accuracy and RAG Recall@K metrics, ensuring enterprise-grade stability."

## Interview Talking Points
1. **"How did you ensure the AI wouldn't break?"** -> Talk about the **Proxy Fallback Pattern**. "I knew LLMs hallucinate JSON or go offline, so I built Planner V2 to strictly validate output. If confidence drops below 70%, the orchestrator instantly degrades to my rule-based Planner V1, guaranteeing the user experience never breaks."
2. **"How do you measure success?"** -> Talk about the **Streamlit Dashboard**. "Instead of guessing if my refactor worked, I injected millisecond telemetry tracking into the orchestrator. My dashboard proved that the modular OOP tools were executing successfully compared to the legacy functions."
3. **"How does the memory work?"** -> Talk about **ChromaDB and Privacy**. "I transitioned from basic hash maps to a local ChromaDB instance running `all-MiniLM-L6-v2`. This allows the assistant to perform semantic RAG natively on the user's hardware, meaning private data never leaves the machine."
