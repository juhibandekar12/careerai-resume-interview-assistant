"""
database/db.py
--------------
SQLite database connection manager and initialization module.
Handles all low-level DB operations for the Career Assistance System.
"""

import sqlite3
import os
import json
import logging
from contextlib import contextmanager

# Path to the SQLite database file
DB_PATH = os.path.join(os.path.dirname(__file__), "career_assist.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row_factory enabled."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row          # access columns by name
    conn.execute("PRAGMA journal_mode=WAL") # better concurrent reads
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    """Context-manager that yields a connection and commits/rolls back automatically."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error("DB error – rolling back: %s", exc)
        raise
    finally:
        conn.close()


def init_db():
    """
    Read schema.sql and execute it against the database.
    Safe to call multiple times (uses CREATE TABLE IF NOT EXISTS).
    """
    if not os.path.exists(SCHEMA_PATH):
        logger.error("schema.sql not found at %s", SCHEMA_PATH)
        return

    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()

    with get_db() as conn:
        conn.executescript(schema_sql)
    logger.info("Database initialised at %s", DB_PATH)


# ──────────────────────────────────────────────────────────────────────────────
# Generic helpers
# ──────────────────────────────────────────────────────────────────────────────

def fetchone(query: str, params: tuple = ()) -> dict | None:
    """Return a single row as a dict, or None."""
    with get_db() as conn:
        cur = conn.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None


def fetchall(query: str, params: tuple = ()) -> list[dict]:
    """Return all matching rows as a list of dicts."""
    with get_db() as conn:
        cur = conn.execute(query, params)
        return [dict(r) for r in cur.fetchall()]


def execute(query: str, params: tuple = ()) -> int:
    """Execute an INSERT/UPDATE/DELETE and return lastrowid."""
    with get_db() as conn:
        cur = conn.execute(query, params)
        return cur.lastrowid


def executemany(query: str, params_list: list[tuple]) -> None:
    """Execute a query for multiple rows."""
    with get_db() as conn:
        conn.executemany(query, params_list)


# ──────────────────────────────────────────────────────────────────────────────
# JSON column helpers
# ──────────────────────────────────────────────────────────────────────────────

def to_json(obj) -> str:
    """Serialize a Python object to a JSON string for DB storage."""
    return json.dumps(obj, ensure_ascii=False)


def from_json(text: str | None):
    """Deserialize a JSON string from the DB; return [] / {} on failure."""
    if not text:
        return []
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return []


if __name__ == "__main__":
    init_db()
    print("DB ready:", DB_PATH)
