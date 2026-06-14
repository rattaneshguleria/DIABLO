"""Tests for semantic memory with fake embeddings."""

from pathlib import Path

import pytest

from memory.embeddings import EmbeddingProvider
from memory.semantic import SemanticMemory


class FakeEmbeddingProvider(EmbeddingProvider):
    def embed(self, text: str) -> list[float]:
        lowered = text.lower()
        if "python" in lowered:
            return [1.0, 0.0, 0.0]
        if "java" in lowered:
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]

    def is_available(self) -> bool:
        return True


@pytest.fixture
def semantic_memory(tmp_path: Path) -> SemanticMemory:
    return SemanticMemory(tmp_path / "chroma", FakeEmbeddingProvider())


def test_store_and_search(semantic_memory: SemanticMemory) -> None:
    semantic_memory.store("User prefers Python", category="preference", memory_key="language")
    semantic_memory.store("User likes Java", category="preference", memory_key="java")

    results = semantic_memory.search("Tell me about Python", top_k=1)
    assert len(results) == 1
    assert "Python" in results[0].text


def test_delete_by_key(semantic_memory: SemanticMemory) -> None:
    semantic_memory.store("User prefers Python", category="preference", memory_key="language")
    semantic_memory.delete_by_key("language")
    assert semantic_memory.count == 0
