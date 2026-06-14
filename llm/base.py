"""Abstract base classes and shared types for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Literal

from tools.base import ToolCall


Role = Literal["system", "user", "assistant", "tool"]


@dataclass(slots=True)
class ChatMessage:
    """A single message in a conversation."""

    role: Role
    content: str
    tool_calls: list[ToolCall] | None = None
    tool_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_calls:
            payload["tool_calls"] = [
                {
                    "function": {
                        "name": call.name,
                        "arguments": call.arguments,
                    }
                }
                for call in self.tool_calls
            ]
        return payload


@dataclass(slots=True)
class LLMResponse:
    """Normalized response from any LLM provider."""

    content: str
    model: str
    done: bool = True
    tool_calls: list[ToolCall] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """
    Abstract interface for language model providers.

    Phase 1 implements Ollama. Future phases can add OpenAI, Anthropic, etc.
    """

    @abstractmethod
    def chat(
        self,
        messages: list[ChatMessage],
        *,
        stream: bool = False,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse | Iterator[str]:
        """Send messages and receive a response."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check whether the provider is reachable and ready."""

    @abstractmethod
    def list_models(self) -> list[str]:
        """Return available model names."""
