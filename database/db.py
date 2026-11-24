import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "learning.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def _columns(conn, table):
    return {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                language TEXT NOT NULL,
                code TEXT NOT NULL,
                status TEXT,
                error_name TEXT,
                category TEXT,
                concept TEXT,
                expected_output TEXT,
                actual_output TEXT,
                explanation TEXT,
                solved INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS hints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL,
                level INTEGER NOT NULL,
                hint TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(attempt_id) REFERENCES attempts(id) ON DELETE CASCADE
            )
        """)

        # Backward-compatible migrations for databases created by earlier sprints.
        additions = {
            "retry_count": "INTEGER NOT NULL DEFAULT 0",
            "latest_code": "TEXT",
            "latest_status": "TEXT",
            "latest_retry_solved": "INTEGER NOT NULL DEFAULT 0",
            "resolved_at": "TIMESTAMP",
            "source": "TEXT NOT NULL DEFAULT 'code'",
            "question_key": "TEXT",
            "stdin_input": "TEXT"
        }
        existing = _columns(conn, "attempts")
        for column, definition in additions.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE attempts ADD COLUMN {column} {definition}")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS retry_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                status TEXT,
                error_name TEXT,
                actual_output TEXT,
                expected_output TEXT,
                solved INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(attempt_id) REFERENCES attempts(id) ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_attempts_created
            ON attempts(created_at)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_attempts_concept
            ON attempts(concept)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_retries_attempt
            ON retry_submissions(attempt_id)
        """)
