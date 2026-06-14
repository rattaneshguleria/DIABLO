"""Central orchestrator for Diablo's memory system."""

from __future__ import annotations

import logging
from pathlib import Path

from config import Settings
from core.exceptions import MemoryError
from database.connection import Database
from database.migrations import initialize_schema
from llm.base import ChatMessage
from memory.embeddings import EmbeddingProvider, OllamaEmbeddingClient
from memory.episodic import EpisodicMemory
from memory.extractor import extract_memories
from memory.long_term import LongTermMemory
from memory.models import MemoryContext, SessionInfo, StoredMemory, utc_now_iso
from memory.semantic import SemanticMemory
from memory.short_term import ShortTermMemory

logger = logging.getLogger("diablo.memory.manager")


class MemoryManager:
    """
    Coordinates short-term, long-term, episodic, and semantic memory.

  Short-term: current session buffer (RAM)
  Long-term: structured facts/preferences (SQLite)
  Episodic: conversation timeline (SQLite)
  Semantic: meaning-based retrieval (ChromaDB + embeddings)
    """

    def __init__(
        self,
        *,
        database: Database,
        short_term: ShortTermMemory,
        long_term: LongTermMemory,
        episodic: EpisodicMemory,
        semantic: SemanticMemory | None,
        session_id: str,
        retrieval_top_k: int = 5,
        auto_extract_memories: bool = True,
        semantic_enabled: bool = True,
    ) -> None:
        self.database = database
        self.short_term = short_term
        self.long_term = long_term
        self.episodic = episodic
        self.semantic = semantic
        self.session_id = session_id
        self.retrieval_top_k = retrieval_top_k
        self.auto_extract_memories = auto_extract_memories
        self.semantic_enabled = semantic_enabled and semantic is not None

    @classmethod
    def from_settings(
        cls,
        settings: Settings,
        *,
        system_prompt: str,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> MemoryManager:
        """Build a memory manager from application settings."""
        db_path = settings.sqlite_db_path
        if not db_path.is_absolute():
            db_path = settings.data_dir / db_path

        database = Database(db_path)
        initialize_schema(database)

        short_term = ShortTermMemory(max_messages=settings.max_history_messages)
        short_term.add(ChatMessage(role="system", content=system_prompt))

        long_term = LongTermMemory(database)
        episodic = EpisodicMemory(database)
        session_id = episodic.create_session(title=f"Session {utc_now_iso()[:19]}")

        semantic: SemanticMemory | None = None
        semantic_enabled = settings.semantic_memory_enabled

        if semantic_enabled:
            provider = embedding_provider or OllamaEmbeddingClient(
                host=settings.ollama_host,
                model=settings.embedding_model,
                timeout=settings.ollama_timeout,
            )
            chroma_dir = settings.chroma_persist_dir
            if not chroma_dir.is_absolute():
                chroma_dir = settings.data_dir / chroma_dir
            semantic = SemanticMemory(chroma_dir, provider)

        return cls(
            database=database,
            short_term=short_term,
            long_term=long_term,
            episodic=episodic,
            semantic=semantic,
            session_id=session_id,
            retrieval_top_k=settings.memory_retrieval_top_k,
            auto_extract_memories=settings.auto_extract_memories,
            semantic_enabled=semantic_enabled,
        )

    def retrieve_context(self, user_message: str) -> MemoryContext:
        """Gather relevant memories for the current user message."""
        context = MemoryContext(
            facts=self.long_term.list_by_category("fact"),
            preferences=self.long_term.list_by_category("preference"),
        )

        if self.semantic_enabled and self.semantic is not None:
            try:
                context.semantic_hits = self.semantic.search(
                    user_message,
                    top_k=self.retrieval_top_k,
                )
            except Exception as exc:  # noqa: BLE001 - degrade gracefully
                logger.warning("Semantic retrieval failed: %s", exc)

        return context

    def build_memory_messages(self, user_message: str) -> list[ChatMessage]:
        """Return optional system messages derived from retrieved memory."""
        context = self.retrieve_context(user_message)
        prompt_block = context.to_prompt_block()
        if not prompt_block:
            return []
        return [ChatMessage(role="system", content=prompt_block)]

    def remember(self, category: str, key: str, value: str) -> StoredMemory:
        """Store a structured memory across long-term and semantic stores."""
        stored = self.long_term.remember(category, key, value)
        if self.semantic_enabled and self.semantic is not None:
            try:
                self.semantic.store(
                    f"{category}: {stored.key} = {stored.value}",
                    category=category,
                    memory_key=stored.key,
                    session_id=self.session_id,
                )
            except Exception as exc:  # noqa: BLE001 - degrade gracefully
                logger.warning("Semantic store failed for %s/%s: %s", category, key, exc)
        return stored

    def remember_note(self, text: str) -> StoredMemory:
        """Store a free-form note."""
        key = f"note_{len(self.long_term.list_by_category('note')) + 1}"
        return self.remember("note", key, text.strip())

    def forget(self, key: str) -> int:
        """Delete a memory by key from all stores."""
        deleted = self.long_term.forget(key)
        if self.semantic is not None:
            self.semantic.delete_by_key(key)
        return deleted

    def list_memories(self) -> list[StoredMemory]:
        return self.long_term.list_all()

    def list_sessions(self, *, limit: int = 20) -> list[SessionInfo]:
        return self.episodic.list_sessions(limit=limit)

    def store_exchange(self, user_message: str, assistant_message: str) -> None:
        """Persist a completed user/assistant exchange."""
        self.episodic.add_message(self.session_id, "user", user_message)
        self.episodic.add_message(self.session_id, "assistant", assistant_message)

        if self.auto_extract_memories:
            self._auto_extract_and_store(user_message)

        if self.semantic_enabled and self.semantic is not None:
            try:
                self.semantic.store(
                    f"User: {user_message}\nAssistant: {assistant_message}",
                    category="episode",
                    session_id=self.session_id,
                )
            except Exception as exc:  # noqa: BLE001 - degrade gracefully
                logger.warning("Failed to store episodic semantic memory: %s", exc)

    def _auto_extract_and_store(self, user_message: str) -> None:
        for candidate in extract_memories(user_message):
            try:
                self.remember(candidate.category, candidate.key, candidate.value)
                logger.info(
                    "Auto-extracted memory: %s/%s",
                    candidate.category,
                    candidate.key,
                )
            except MemoryError as exc:
                logger.warning("Skipped auto-extracted memory: %s", exc)

    def clear_session(self) -> str:
        """Clear short-term history and start a new episodic session."""
        system_messages = [
            message for message in self.short_term.messages if message.role == "system"
        ]
        self.short_term.messages = system_messages
        self.session_id = self.episodic.create_session(title=f"Session {utc_now_iso()[:19]}")
        logger.info("Started new memory session %s", self.session_id)
        return self.session_id

    def close(self) -> None:
        """Finalize the current session."""
        self.episodic.touch_session(self.session_id)
        logger.info("Memory session %s closed", self.session_id)
