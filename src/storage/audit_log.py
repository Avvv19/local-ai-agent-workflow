"""
SQLite audit log.

Every agent event — input received, retry, success, failure, routing decision —
is written here with a timestamp and trace_id. Any result can be reconstructed
from this log without needing LangSmith access.

Schema:
  audit_log(id, trace_id, stage, status, detail, created_at)
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from src.config import settings

_DB_PATH = Path(settings.db_path)


def init_db() -> None:
    """Create audit_log table if it does not exist."""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id    TEXT    NOT NULL,
                stage       TEXT    NOT NULL,
                status      TEXT    NOT NULL,
                detail      TEXT,
                created_at  TEXT    NOT NULL
            )
        """)
        conn.commit()


def log_event(trace_id: str, stage: str, status: str, detail: str = "") -> None:
    """
    Write a single audit event.

    Args:
        trace_id: Unique ID propagated from DocumentInput.
        stage: Which agent or layer produced the event (e.g. "document_agent").
        status: "success" | "retry_N" | "dead_letter" | "routed" | "received"
        detail: Human-readable context string.
    """
    created_at = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute(
            "INSERT INTO audit_log (trace_id, stage, status, detail, created_at) VALUES (?,?,?,?,?)",
            (trace_id, stage, status, detail, created_at),
        )
        conn.commit()


def get_recent(limit: int = 20) -> list[dict]:
    """Return the most recent audit log entries."""
    with sqlite3.connect(_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
