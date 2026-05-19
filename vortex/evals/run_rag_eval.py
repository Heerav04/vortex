import json
import logging
from pathlib import Path
import sys

# Add parent to path to import core
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from core.memory import VortexMemory

def evaluate_rag():
    print("Initializing ChromaDB for RAG Evaluation...")
    mem = VortexMemory()
    # Bootstrap simple memories for test
    mem.learn("I love using VSCode and Docker.", "User likes VSCode, Cursor, and Docker.", "chat")
    mem.learn("I live in Mumbai right now.", "User location is Mumbai.", "chat")
    mem.learn("My schedule is 9am coding and 2pm leetcode.", "09:00 coding, 14:00 LeetCode.", "chat")

    eval_file = BASE_DIR / "evals" / "rag_eval_set.jsonl"
    
    correct = 0
    total = 0
    
    with open(eval_file, "r") as f:
        for line in f:
            if not line.strip(): continue
            total += 1
            data = json.loads(line)
            query = data["query"]
            expected = data["expected_memory"]
            
            # Retrieve top 1 — returns List[str]
            results = mem.search(query, n_results=1)

            # Flatten the list into a single string for substring/keyword matching
            results_text = " ".join(results).lower() if results else ""
            if results_text and (
                expected.lower() in results_text
                or any(word.lower() in results_text for word in expected.split())
            ):
                correct += 1
                
    print(f"RAG Recall@1: {correct}/{total} ({(correct/total)*100 if total > 0 else 0:.1f}%)")

if __name__ == "__main__":
    evaluate_rag()
