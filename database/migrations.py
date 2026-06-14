"""Database schema initialization for Diablo."""

from __future__ import annotations

import logging

from database.connection import Database

logger = logging.getLogger("diablo.database.migrations")

SCHEMA_VERSION = 1

SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
"""

MEMORIES_TABLE = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    memory_key TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(category, memory_key)
);
"""

SCHEMA_META_TABLE = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);",
    "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);",
]


def initialize_schema(database: Database) -> None:
    """Create database tables if they do not exist."""
    with database.connection() as conn:
        conn.execute(SESSIONS_TABLE)
        conn.execute(MESSAGES_TABLE)
        conn.execute(MEMORIES_TABLE)
        conn.execute(SCHEMA_META_TABLE)
        for index_sql in INDEXES:
            conn.execute(index_sql)
        conn.execute(
            "INSERT OR REPLACE INTO schema_meta(key, value) VALUES (?, ?)",
            ("version", str(SCHEMA_VERSION)),
        )
    logger.info("Database schema initialized (version %d)", SCHEMA_VERSION)
