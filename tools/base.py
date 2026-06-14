"""Base types and interfaces for Diablo tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    """Risk classification for tool operations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


ConfirmationCallback = Callable[[str], bool]


@dataclass(slots=True)
class ToolParameter:
    """Schema for a single tool parameter."""

    name: str
    type: str
    description: str
    required: bool = True


@dataclass(slots=True)
class ToolSchema:
    """JSON-schema-compatible tool definition for the LLM."""

    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)

    def to_ollama_tool(self) -> dict[str, Any]:
        """Convert to Ollama's tool definition format."""
        properties: dict[str, Any] = {}
        required: list[str] = []

        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description,
            }
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


@dataclass(slots=True)
class ToolCall:
    """A tool invocation requested by the LLM."""

    name: str
    arguments: dict[str, Any]
    call_id: str | None = None


@dataclass(slots=True)
class ToolResult:
    """Result of executing a tool."""

    success: bool
    output: str
    error: str | None = None
    tool_name: str = ""

    def to_message_content(self) -> str:
        if self.success:
            return self.output
        return f"Error: {self.error or 'Unknown tool error'}"


@dataclass(slots=True)
class ToolAuditEntry:
    """Audit record for a tool execution."""

    tool_name: str
    arguments: dict[str, Any]
    success: bool
    output_preview: str
    timestamp: str


class Tool(ABC):
    """Abstract base class for all Diablo tools."""

    name: str
    description: str
    risk_level: RiskLevel = RiskLevel.LOW
    parameters: list[ToolParameter]

    @abstractmethod
    def run(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with the provided arguments."""

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )

    def requires_confirmation(self) -> bool:
        return self.risk_level == RiskLevel.HIGH
