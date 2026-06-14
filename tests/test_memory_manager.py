"""Tests for the memory manager orchestrator."""

from pathlib import Path

import pytest

from config import Settings
from memory.embeddings import EmbeddingProvider
from memory.manager import MemoryManager


class FakeEmbeddingProvider(EmbeddingProvider):
    def embed(self, text: str) -> list[float]:
        return [float(len(text) % 7), 0.5, 0.25]

    def is_available(self) -> bool:
        return True


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        data_dir=tmp_path / "data",
        sqlite_db_path=Path("diablo.db"),
        chroma_persist_dir=Path("chroma"),
        memory_enabled=True,
        semantic_memory_enabled=True,
    )


@pytest.fixture
def memory_manager(settings: Settings) -> MemoryManager:
    return MemoryManager.from_settings(
        settings,
        system_prompt="You are Diablo.",
        embedding_provider=FakeEmbeddingProvider(),
    )


def test_remember_and_list(memory_manager: MemoryManager) -> None:
    memory_manager.remember("fact", "name", "Alex")
    memories = memory_manager.list_memories()
    assert any(item.key == "name" and item.value == "Alex" for item in memories)


def test_build_memory_messages(memory_manager: MemoryManager) -> None:
    memory_manager.remember("preference", "language", "Python")
    messages = memory_manager.build_memory_messages("What language do I use?")
    assert len(messages) == 1
    assert "Python" in messages[0].content


def test_store_exchange_persists_episode(memory_manager: MemoryManager) -> None:
    memory_manager.store_exchange("Hello", "Hi there")
    sessions = memory_manager.list_sessions()
    assert sessions[0].message_count == 2


def test_auto_extract_name(memory_manager: MemoryManager) -> None:
    memory_manager.store_exchange("My name is Alex", "Nice to meet you, Alex.")
    memories = memory_manager.list_memories()
    assert any(item.key == "name" and item.value == "Alex" for item in memories)


def test_clear_session_starts_new_session(memory_manager: MemoryManager) -> None:
    old_session = memory_manager.session_id
    memory_manager.store_exchange("Hello", "Hi")
    new_session = memory_manager.clear_session()
    assert new_session != old_session
