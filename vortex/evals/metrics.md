# Vortex Core Metrics

1. **Intent Routing Accuracy**: Measures if the `VortexPlanner` assigns the correct `tool` and `action` for a given user query. Tested deterministically via PyTest.
2. **Tool-Call Accuracy**: Measures if the assigned tool exists in the `ToolRegistry` and executes without crashing.
3. **Parameter Correctness**: Ensures the parsed parameters (e.g., volume level, app name) match the expected schema.
4. **Failure Handling / Graceful Degradation**: Verifies the system degrades to generic search or LLM chat if a specific action fails.
5. **Retrieval Quality (Local RAG)**: Measures precision@k and recall@k using ChromaDB and sentence-transformers.
6. **Response Quality**: Scored via rubric for groundedness, relevance, completeness, and safety.
7. **Latency Thresholds**: Measured via SQLite telemetry; tools should execute in <500ms, local LLMs <3000ms.
