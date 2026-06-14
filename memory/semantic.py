"""Semantic vector memory using ChromaDB."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from core.exceptions import MemoryError, MemoryStoreError
from memory.embeddings import EmbeddingProvider
from memory.models import SemanticMemoryEntry

logger = logging.getLogger("diablo.memory.semantic")

COLLECTION_NAME = "diablo_memories"


class SemanticMemory:
    """Vector store for meaning-based memory retrieval."""

    def __init__(
        self,
        persist_dir: Path,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._embedding_provider = embedding_provider
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def store(
        self,
        text: str,
        *,
        category: str,
        memory_key: str | None = None,
        session_id: str | None = None,
    ) -> str:
        """Store a text memory with its embedding."""
        cleaned = text.strip()
        if not cleaned:
            raise MemoryError("Cannot store empty semantic memory")

        memory_id = str(uuid.uuid4())
        embedding = self._embedding_provider.embed(cleaned)
        metadata = {
            "category": category,
            "memory_key": memory_key or "",
            "session_id": session_id or "",
        }

        try:
            self._collection.add(
                ids=[memory_id],
                documents=[cleaned],
                embeddings=[embedding],
                metadatas=[metadata],
            )
        except Exception as exc:  # noqa: BLE001 - ChromaDB surface errors
            raise MemoryStoreError("Failed to store semantic memory", details=str(exc)) from exc

        logger.info("Stored semantic memory (%s): %s", category, cleaned[:80])
        return memory_id

    def search(self, query: str, *, top_k: int = 5) -> list[SemanticMemoryEntry]:
        """Find memories semantically similar to the query."""
        cleaned = query.strip()
        if not cleaned:
            return []

        if self._collection.count() == 0:
            return []

        embedding = self._embedding_provider.embed(cleaned)
        try:
            results = self._collection.query(
                query_embeddings=[embedding],
                n_results=min(top_k, max(self._collection.count(), 1)),
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:  # noqa: BLE001 - ChromaDB surface errors
            raise MemoryStoreError("Semantic search failed", details=str(exc)) from exc

        entries: list[SemanticMemoryEntry] = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for index, memory_id in enumerate(ids):
            distance = distances[index] if index < len(distances) else 1.0
            score = max(0.0, 1.0 - float(distance))
            metadata = metadatas[index] if index < len(metadatas) else {}
            text = documents[index] if index < len(documents) else ""
            entries.append(
                SemanticMemoryEntry(
                    id=memory_id,
                    text=text,
                    category=str(metadata.get("category", "note")),
                    score=score,
                    metadata={key: str(value) for key, value in metadata.items()},
                )
            )

        return entries

    def delete_by_key(self, memory_key: str) -> None:
        """Delete semantic memories associated with a structured key."""
        cleaned_key = memory_key.strip().lower()
        if not cleaned_key:
            return

        try:
            results = self._collection.get(where={"memory_key": cleaned_key})
            ids = results.get("ids", [])
            if ids:
                self._collection.delete(ids=ids)
        except Exception as exc:  # noqa: BLE001 - ChromaDB surface errors
            logger.warning("Failed to delete semantic memories for key %s: %s", cleaned_key, exc)

    @property
    def count(self) -> int:
        return self._collection.count()
