"""Custom exceptions for Diablo."""


class DiabloError(Exception):
    """Base exception for all Diablo errors."""

    def __init__(self, message: str, *, details: str | None = None) -> None:
        self.message = message
        self.details = details
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class LLMConnectionError(DiabloError):
    """Raised when Diablo cannot connect to the LLM provider."""


class LLMResponseError(DiabloError):
    """Raised when the LLM returns an invalid or empty response."""


class ModelNotFoundError(DiabloError):
    """Raised when the requested model is not available locally."""


class MemoryError(DiabloError):
    """Raised when a memory operation fails."""


class MemoryStoreError(MemoryError):
    """Raised when reading or writing persistent memory fails."""


class ToolError(DiabloError):
    """Raised when a tool operation fails."""


class ToolNotFoundError(ToolError):
    """Raised when a requested tool does not exist."""


class ToolExecutionError(ToolError):
    """Raised when tool execution is blocked or fails."""
