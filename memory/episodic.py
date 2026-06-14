"""Episodic conversation memory stored in SQLite."""

from __future__ import annotations

import logging
import uuid

from database.connection import Database
from memory.models import EpisodeMessage, SessionInfo, utc_now_iso

logger = logging.getLogger("diablo.memory.episodic")


class EpisodicMemory:
    """Persist conversation sessions and message timelines."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def create_session(self, *, title: str | None = None) -> str:
        """Create a new conversation session."""
        session_id = str(uuid.uuid4())
        now = utc_now_iso()
        self._db.execute(
            """
            INSERT INTO sessions(id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, title, now, now),
        )
        logger.info("Created episodic session %s", session_id)
        return session_id

    def add_message(self, session_id: str, role: str, content: str) -> EpisodeMessage:
        """Append a message to a session."""
        now = utc_now_iso()
        self._db.execute(
            """
            INSERT INTO messages(session_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, role, content, now),
        )
        self._db.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (now, session_id),
        )
        row = self._db.fetchone(
            """
            SELECT * FROM messages
            WHERE session_id = ? AND created_at = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (session_id, now),
        )
        if row is None:
            raise RuntimeError("Failed to read persisted episodic message")

        return EpisodeMessage(
            id=row["id"],
            session_id=row["session_id"],
            role=row["role"],
            content=row["content"],
            created_at=row["created_at"],
        )

    def get_session_messages(self, session_id: str, *, limit: int = 50) -> list[EpisodeMessage]:
        rows = self._db.fetchall(
            """
            SELECT * FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (session_id, limit),
        )
        return [
            EpisodeMessage(
                id=row["id"],
                session_id=row["session_id"],
                role=row["role"],
                content=row["content"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def list_sessions(self, *, limit: int = 20) -> list[SessionInfo]:
        rows = self._db.fetchall(
            """
            SELECT
                s.id,
                s.title,
                s.created_at,
                s.updated_at,
                COUNT(m.id) AS message_count
            FROM sessions s
            LEFT JOIN messages m ON m.session_id = s.id
            GROUP BY s.id
            ORDER BY s.updated_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [
            SessionInfo(
                id=row["id"],
                title=row["title"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                message_count=row["message_count"],
            )
            for row in rows
        ]

    def touch_session(self, session_id: str) -> None:
        self._db.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (utc_now_iso(), session_id),
        )
