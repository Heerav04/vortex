# Vortex Evaluation Framework
This directory contains tools and metrics to benchmark the quality of the Vortex AI OS.

### Structure
- `metrics.md`: Core evaluation dimensions.
- `response_rubric.md`: Qualitative scoring guide.
- `rag_eval_set.jsonl`: Deterministic data for memory retrieval tests.
- `run_rag_eval.py`: Script to compute precision/recall for ChromaDB.
- `report.py`: Aggregates PyTest, Telemetry, and RAG stats into a single summary.

### Running Evals
To run the intent/routing unit tests: `pytest ../tests`
To run the RAG evaluation: `python run_rag_eval.py`
To generate a comprehensive report: `python report.py`
