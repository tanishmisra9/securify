from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path("audit/audit.db")


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                entity_types_seen TEXT NOT NULL,
                security_verdict TEXT NOT NULL,
                pii_in_answer INTEGER NOT NULL,
                injection_attempt INTEGER NOT NULL
            )
            """
        )
        conn.commit()


def log_query(
    query: str,
    entity_types_seen: list[str],
    security_verdict: str,
    pii_in_answer: bool,
    injection_attempt: bool,
) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO audit_log (
                timestamp,
                query,
                entity_types_seen,
                security_verdict,
                pii_in_answer,
                injection_attempt
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                query,
                json.dumps(entity_types_seen),
                security_verdict,
                int(pii_in_answer),
                int(injection_attempt),
            ),
        )
        conn.commit()


def get_all_logs(limit: int | None = None) -> list[tuple]:
    query = "SELECT * FROM audit_log ORDER BY id DESC"
    params: tuple[int, ...] = ()

    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(query, params).fetchall()

    return rows
