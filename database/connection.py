"""SQLite connection management for Diablo."""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from collections.abc import Iterator
from pathlib import Path

from core.exceptions import MemoryStoreError

logger = logging.getLogger("diablo.database.connection")


class Database:
    """Thin wrapper around SQLite with safe connection handling."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Yield a SQLite connection with foreign keys enabled."""
        conn: sqlite3.Connection | None = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        except sqlite3.Error as exc:
            if conn is not None:
                conn.rollback()
            logger.error("Database error: %s", exc)
            raise MemoryStoreError("Database operation failed", details=str(exc)) from exc
        finally:
            if conn is not None:
                conn.close()

    def execute(self, query: str, params: tuple | list = ()) -> None:
        """Execute a write query."""
        with self.connection() as conn:
            conn.execute(query, params)

    def fetchall(self, query: str, params: tuple | list = ()) -> list[sqlite3.Row]:
        """Execute a read query and return all rows."""
        with self.connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def fetchone(self, query: str, params: tuple | list = ()) -> sqlite3.Row | None:
        """Execute a read query and return one row."""
        with self.connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()
