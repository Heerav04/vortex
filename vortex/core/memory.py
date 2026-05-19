import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from . import DATA_DIR, ensure_data_dirs

MEMORY_DB_PATH = DATA_DIR / "memory.db"
CHROMA_DB_PATH = DATA_DIR / "chroma"



@dataclass
class VortexProfile:
    name: str
    location: str
    role: str
    weak_areas: List[str]
    favorite_apps: List[str]
    routine: Dict[str, str]
    style: str


class VortexMemory:
    """
    Simple SQLite + in-memory vector storage.
    Not a full vector DB, but good enough for personalization.
    """

    def __init__(self, db_path: Path = MEMORY_DB_PATH):
        ensure_data_dirs()
        self.db_path = db_path
        self._init_db()
        self._init_chroma()
        self.profile = self._load_or_bootstrap_profile()

    def _init_chroma(self) -> None:
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
            # Prefer sentence-transformers embeddings; gracefully fall back if local
            # torch/transformers stack is incompatible on this machine.
            try:
                self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
            except Exception as emb_error:
                logging.warning(
                    "SentenceTransformer embedding unavailable (%s). "
                    "Falling back to Chroma default embedding.",
                    emb_error,
                )
                self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
            self.collection = self.chroma_client.get_or_create_collection(
                name="vortex_memory", embedding_function=self.emb_fn
            )
            logging.info("ChromaDB Local RAG engine initialized.")
        except Exception as e:
            logging.error(f"Failed to initialize ChromaDB: {e}")
            self.collection = None

    # --- DB setup ---------------------------------------------------------
    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS interactions (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ts_utc TEXT NOT NULL,
                  query TEXT,
                  result_summary TEXT,
                  mode TEXT
                )
                """.strip()
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS vectors (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  interaction_id INTEGER,
                  kind TEXT NOT NULL,
                  dim INTEGER NOT NULL,
                  data BLOB NOT NULL,
                  FOREIGN KEY(interaction_id) REFERENCES interactions(id)
                )
                """.strip()
            )
            conn.commit()

    # --- Profile ----------------------------------------------------------
    def _load_or_bootstrap_profile(self) -> VortexProfile:
        import json
        config_file = DATA_DIR / "config.json"
        prof = {}
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    prof = json.load(f).get("profile", {})
            except Exception:
                pass

        profile = VortexProfile(
            name=prof.get("name", "Heerav Amin"),
            location=prof.get("location", "Mumbai"),
            role=prof.get("role", "CS student"),
            weak_areas=prof.get("weak_areas", ["DSA recursion", "system design"]),
            favorite_apps=prof.get("favorite_apps", ["VSCode", "Cursor", "Ollama", "Docker", "PostgreSQL"]),
            routine=prof.get("routine", {"09:00": "coding", "14:00": "LeetCode"}),
            style=prof.get("style", "PEP8 Python, React/Next.js fullstack"),
        )
        logging.info("Loaded Vortex profile for %s in %s", profile.name, profile.location)
        return profile

    # --- Interaction logging / learning -----------------------------------
    def learn(self, query: str, result_summary: str, mode: str) -> None:
        import datetime as _dt
        from datetime import timezone

        q = (query or "").strip()
        rs = (result_summary or "").strip()
        ts = _dt.datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z"
        
        # 1. Log to SQLite for chronological order
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO interactions (ts_utc, query, result_summary, mode) VALUES (?, ?, ?, ?)",
                (ts, q, rs, mode),
            )
            interaction_id = cur.lastrowid
            conn.commit()

        # 2. Embed into ChromaDB for Semantic Search (Local RAG)
        if hasattr(self, 'collection') and self.collection:
            try:
                doc_text = f"User asked: {q} | Assistant responded: {rs}"
                self.collection.add(
                    documents=[doc_text],
                    metadatas=[{"mode": mode, "timestamp": ts}],
                    ids=[f"interaction_{interaction_id}"]
                )
            except Exception as e:
                logging.error(f"ChromaDB embedding failed: {e}")

    def search(self, query: str, n_results: int = 3) -> List[str]:
        """Retrieve relevant past context based on semantic similarity."""
        if not hasattr(self, 'collection') or not self.collection:
            return []
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            if results and "documents" in results and results["documents"]:
                return results["documents"][0]
            return []
        except Exception as e:
            logging.error(f"ChromaDB search failed: {e}")
            return []

    def recent_interactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT ts_utc, query, result_summary, mode FROM interactions ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
        out: List[Dict[str, Any]] = []
        for ts, q, rs, m in rows:
            out.append({"ts_utc": ts, "query": q, "result_summary": rs, "mode": m})
        return out


__all__ = ["VortexMemory", "VortexProfile", "MEMORY_DB_PATH"]

