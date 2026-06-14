"""Structured long-term memory stored in SQLite."""

from __future__ import annotations

import logging

from core.exceptions import MemoryError, MemoryStoreError
from database.connection import Database
from memory.models import StoredMemory, utc_now_iso

logger = logging.getLogger("diablo.memory.long_term")


class LongTermMemory:
    """Store and retrieve structured facts and preferences."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def remember(self, category: str, key: str, value: str) -> StoredMemory:
        """Create or update a structured memory entry."""
        cleaned_key = key.strip().lower()
        cleaned_value = value.strip()
        if not cleaned_key or not cleaned_value:
            raise MemoryError("Memory key and value cannot be empty")

        now = utc_now_iso()
        self._db.execute(
            """
            INSERT INTO memories(category, memory_key, value, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(category, memory_key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (category, cleaned_key, cleaned_value, now, now),
        )
        row = self._db.fetchone(
            "SELECT * FROM memories WHERE category = ? AND memory_key = ?",
            (category, cleaned_key),
        )
        if row is None:
            raise MemoryStoreError("Failed to persist memory", details=f"{category}:{cleaned_key}")

        logger.info("Stored long-term memory: %s/%s", category, cleaned_key)
        return self._row_to_memory(row)

    def forget(self, key: str, *, category: str | None = None) -> int:
        """Delete memory entries by key. Returns number of rows removed."""
        cleaned_key = key.strip().lower()
        if not cleaned_key:
            raise MemoryError("Memory key cannot be empty")

        if category:
            rows = self._db.fetchall(
                "SELECT id FROM memories WHERE category = ? AND memory_key = ?",
                (category, cleaned_key),
            )
            self._db.execute(
                "DELETE FROM memories WHERE category = ? AND memory_key = ?",
                (category, cleaned_key),
            )
        else:
            rows = self._db.fetchall(
                "SELECT id FROM memories WHERE memory_key = ?",
                (cleaned_key,),
            )
            self._db.execute(
                "DELETE FROM memories WHERE memory_key = ?",
                (cleaned_key,),
            )

        deleted = len(rows)
        logger.info("Forgot memory key: %s (%d removed)", cleaned_key, deleted)
        return deleted

    def get(self, category: str, key: str) -> StoredMemory | None:
        row = self._db.fetchone(
            "SELECT * FROM memories WHERE category = ? AND memory_key = ?",
            (category, key.strip().lower()),
        )
        return self._row_to_memory(row) if row else None

    def list_by_category(self, category: str) -> list[StoredMemory]:
        rows = self._db.fetchall(
            "SELECT * FROM memories WHERE category = ? ORDER BY updated_at DESC",
            (category,),
        )
        return [self._row_to_memory(row) for row in rows]

    def list_all(self) -> list[StoredMemory]:
        rows = self._db.fetchall(
            "SELECT * FROM memories ORDER BY category, memory_key",
        )
        return [self._row_to_memory(row) for row in rows]

    @staticmethod
    def _row_to_memory(row) -> StoredMemory:
        return StoredMemory(
            id=row["id"],
            category=row["category"],
            key=row["memory_key"],
            value=row["value"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
