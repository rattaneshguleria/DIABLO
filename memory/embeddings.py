"""Ollama embedding client for semantic memory."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import httpx
import ollama

from core.exceptions import LLMConnectionError, MemoryError

logger = logging.getLogger("diablo.memory.embeddings")


class EmbeddingProvider(ABC):
    """Abstract interface for text embedding providers."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Embed a single text string."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check whether the embedding provider is reachable."""


class OllamaEmbeddingClient(EmbeddingProvider):
    """Generate embeddings using a local Ollama embedding model."""

    def __init__(
        self,
        *,
        host: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        timeout: int = 60,
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client = ollama.Client(host=self.host, timeout=self.timeout)

    def is_available(self) -> bool:
        try:
            self._client.list()
            return True
        except (httpx.ConnectError, httpx.TimeoutException, ConnectionError) as exc:
            logger.warning("Embedding provider unavailable at %s: %s", self.host, exc)
            return False
        except Exception as exc:  # noqa: BLE001 - provider guard
            logger.error("Unexpected embedding availability error: %s", exc)
            return False

    def embed(self, text: str) -> list[float]:
        cleaned = text.strip()
        if not cleaned:
            raise MemoryError("Cannot embed empty text")

        try:
            response = self._client.embeddings(model=self.model, prompt=cleaned)
            embedding = response.get("embedding")
            if not embedding:
                raise MemoryError("Embedding model returned no vector")
            return [float(value) for value in embedding]
        except (httpx.ConnectError, httpx.TimeoutException, ConnectionError) as exc:
            raise LLMConnectionError(
                "Lost connection to Ollama during embedding",
                details=str(exc),
            ) from exc
        except ollama.ResponseError as exc:
            raise MemoryError(
                f"Embedding model '{self.model}' failed",
                details=str(exc),
            ) from exc
