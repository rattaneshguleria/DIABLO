"""Tests for episodic memory storage."""

from pathlib import Path

from database.connection import Database
from database.migrations import initialize_schema
from memory.episodic import EpisodicMemory


def test_create_session_and_store_messages(tmp_path: Path) -> None:
    database = Database(tmp_path / "test.db")
    initialize_schema(database)
    episodic = EpisodicMemory(database)

    session_id = episodic.create_session(title="Test session")
    episodic.add_message(session_id, "user", "Hello")
    episodic.add_message(session_id, "assistant", "Hi there")

    messages = episodic.get_session_messages(session_id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].content == "Hi there"

    sessions = episodic.list_sessions()
    assert len(sessions) == 1
    assert sessions[0].message_count == 2
