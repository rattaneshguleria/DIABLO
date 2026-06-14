"""Tests for long-term memory storage."""

from pathlib import Path

import pytest

from core.exceptions import MemoryError
from database.connection import Database
from database.migrations import initialize_schema
from memory.long_term import LongTermMemory


@pytest.fixture
def long_term(tmp_path: Path) -> LongTermMemory:
    database = Database(tmp_path / "test.db")
    initialize_schema(database)
    return LongTermMemory(database)


def test_remember_and_get(long_term: LongTermMemory) -> None:
    stored = long_term.remember("fact", "name", "Alex")
    assert stored.key == "name"
    assert stored.value == "Alex"

    fetched = long_term.get("fact", "name")
    assert fetched is not None
    assert fetched.value == "Alex"


def test_remember_updates_existing_value(long_term: LongTermMemory) -> None:
    long_term.remember("preference", "language", "Java")
    updated = long_term.remember("preference", "language", "Python")
    assert updated.value == "Python"
    assert len(long_term.list_by_category("preference")) == 1


def test_forget_memory(long_term: LongTermMemory) -> None:
    long_term.remember("fact", "city", "Delhi")
    deleted = long_term.forget("city")
    assert deleted == 1
    assert long_term.get("fact", "city") is None


def test_empty_memory_rejected(long_term: LongTermMemory) -> None:
    with pytest.raises(MemoryError):
        long_term.remember("fact", " ", "value")
