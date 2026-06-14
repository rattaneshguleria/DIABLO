"""Heuristic extraction of memorable facts from user messages."""

from __future__ import annotations

import re
from dataclasses import dataclass

SENSITIVE_KEYWORDS = (
    "password",
    "secret",
    "api key",
    "apikey",
    "token",
    "credential",
    "private key",
)

EXTRACTION_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "fact",
        "name",
        re.compile(
            r"(?:my name is|call me|i am|i'm)\s+([a-zA-Z][a-zA-Z0-9 _.-]{1,40})",
            re.IGNORECASE,
        ),
    ),
    (
        "preference",
        "preference",
        re.compile(
            r"(?:i prefer|i like|i love|i hate|i dislike)\s+(.{2,120})",
            re.IGNORECASE,
        ),
    ),
    (
        "note",
        "note",
        re.compile(
            r"(?:remember that|please remember|don't forget that|do not forget that)\s+(.{2,200})",
            re.IGNORECASE,
        ),
    ),
]


@dataclass(slots=True)
class ExtractedMemory:
    """A memory candidate extracted from natural language."""

    category: str
    key: str
    value: str
    source_text: str


def contains_sensitive_data(text: str) -> bool:
    """Return True if the text likely contains sensitive credentials."""
    lowered = text.lower()
    return any(keyword in lowered for keyword in SENSITIVE_KEYWORDS)


def extract_memories(text: str) -> list[ExtractedMemory]:
    """Extract structured memory candidates from a user message."""
    cleaned = text.strip()
    if not cleaned or contains_sensitive_data(cleaned):
        return []

    extracted: list[ExtractedMemory] = []
    for category, key, pattern in EXTRACTION_PATTERNS:
        match = pattern.search(cleaned)
        if not match:
            continue

        value = match.group(1).strip().rstrip(".")
        if not value:
            continue

        extracted.append(
            ExtractedMemory(
                category=category,
                key=key if category != "preference" else _preference_key(value),
                value=value,
                source_text=cleaned,
            )
        )

    return extracted


def _preference_key(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return normalized[:60] or "preference"
