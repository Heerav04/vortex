import sqlite3
import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from core import DATA_DIR

TELEMETRY_DB_PATH = DATA_DIR / "telemetry.sqlite3"

class TelemetryLogger:
    """
    Production-grade event logger for analytics and performance metrics.
    Replaces basic query_logs.json with a structured SQLite events table.
    This acts as the foundation for the Dashboard Metrics View.
    """
    def __init__(self, db_path: Path = TELEMETRY_DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    latency_ms REAL,
                    payload TEXT
                )'''
            )
            conn.commit()

    def log_event(self, event_type: str, payload: Dict[str, Any], latency_ms: Optional[float] = None) -> None:
        """
        Log a specific system event (e.g., 'intent_routed', 'tool_execution').
        """
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO events (timestamp, event_type, latency_ms, payload) VALUES (?, ?, ?, ?)",
                    (ts, event_type, latency_ms, json.dumps(payload, ensure_ascii=False))
                )
                conn.commit()
        except Exception as e:
            logging.error(f"Telemetry logging failed: {e}")

# Global singleton for easy import
telemetry = TelemetryLogger()
