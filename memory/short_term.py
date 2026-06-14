"""In-session short-term conversation buffer."""

from __future__ import annotations

from dataclasses import dataclass, field

from llm.base import ChatMessage


@dataclass
class ShortTermMemory:
    """In-memory conversation history for the current session."""

    messages: list[ChatMessage] = field(default_factory=list)
    max_messages: int = 20

    def add(self, message: ChatMessage) -> None:
        """Append a message and trim history if needed."""
        self.messages.append(message)
        self._trim_history()

    def _trim_history(self) -> None:
        """Keep system prompt plus the most recent exchanges."""
        if len(self.messages) <= self.max_messages:
            return

        system_messages = [message for message in self.messages if message.role == "system"]
        non_system = [message for message in self.messages if message.role != "system"]
        keep_count = max(self.max_messages - len(system_messages), 0)
        self.messages = system_messages + non_system[-keep_count:]

    def as_llm_messages(self) -> list[ChatMessage]:
        """Return a copy of messages for LLM calls."""
        return list(self.messages)

    def clear(self, *, keep_system: bool = True) -> None:
        """Clear conversation history."""
        if keep_system:
            self.messages = [message for message in self.messages if message.role == "system"]
        else:
            self.messages.clear()

    def set_system_messages(self, messages: list[ChatMessage]) -> None:
        """Replace system messages while keeping conversation turns."""
        non_system = [message for message in self.messages if message.role != "system"]
        self.messages = list(messages) + non_system

    @property
    def message_count(self) -> int:
        return len(self.messages)
