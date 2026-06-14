"""Data models for Diablo's memory system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

MemoryCategory = Literal["preference", "fact", "note", "episode"]


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Return the current UTC timestamp as an ISO-8601 string."""
    return utc_now().isoformat()


@dataclass(slots=True)
class StoredMemory:
    """A structured long-term memory entry."""

    id: int
    category: MemoryCategory
    key: str
    value: str
    created_at: str
    updated_at: str


@dataclass(slots=True)
class SessionInfo:
    """Metadata for a conversation session."""

    id: str
    created_at: str
    updated_at: str
    title: str | None = None
    message_count: int = 0


@dataclass(slots=True)
class EpisodeMessage:
    """A single message stored in episodic memory."""

    id: int
    session_id: str
    role: str
    content: str
    created_at: str


@dataclass(slots=True)
class SemanticMemoryEntry:
    """A vector-indexed memory retrieved from semantic search."""

    id: str
    text: str
    category: str
    score: float
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class MemoryContext:
    """Aggregated memory context for prompt injection."""

    preferences: list[StoredMemory] = field(default_factory=list)
    facts: list[StoredMemory] = field(default_factory=list)
    semantic_hits: list[SemanticMemoryEntry] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.preferences and not self.facts and not self.semantic_hits

    def to_prompt_block(self) -> str:
        """Format retrieved memories as a prompt block for the LLM."""
        if self.is_empty():
            return ""

        sections: list[str] = []

        if self.facts:
            lines = [f"- {item.key}: {item.value}" for item in self.facts]
            sections.append("Known facts about the user:\n" + "\n".join(lines))

        if self.preferences:
            lines = [f"- {item.key}: {item.value}" for item in self.preferences]
            sections.append("User preferences:\n" + "\n".join(lines))

        if self.semantic_hits:
            lines = [f"- {item.text}" for item in self.semantic_hits]
            sections.append("Relevant past context:\n" + "\n".join(lines))

        return (
            "The following information was retrieved from Diablo's persistent memory. "
            "Use it naturally when relevant. Do not mention the memory system unless asked.\n\n"
            + "\n\n".join(sections)
        )
