"""Vision support: a dedicated Ollama client for multimodal image description."""

from __future__ import annotations

import logging

import httpx
import ollama

from config import Settings
from core.exceptions import LLMConnectionError, LLMResponseError, ModelNotFoundError

logger = logging.getLogger("diablo.llm.vision")


class VisionClient:
    """Minimal client for sending images + a prompt to a multimodal Ollama model."""

    def __init__(
        self,
        *,
        host: str = "http://localhost:11434",
        model: str = "llava",
        timeout: int = 120,
        temperature: float = 0.4,
        max_tokens: int = 1024,
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = ollama.Client(host=self.host, timeout=self.timeout)

    def describe(self, prompt: str, images_b64: list[str]) -> str:
        """Send a prompt plus one or more base64-encoded images, return text."""
        try:
            response = self._client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt, "images": images_b64}],
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                },
                stream=False,
            )
        except (httpx.ConnectError, httpx.TimeoutException, ConnectionError) as exc:
            raise LLMConnectionError(
                "Cannot connect to Ollama for vision request",
                details=str(exc),
            ) from exc
        except ollama.ResponseError as exc:
            if "not found" in str(exc).lower():
                raise ModelNotFoundError(
                    f"Vision model '{self.model}' not found",
                    details=f"Pull it with: ollama pull {self.model}",
                ) from exc
            raise LLMResponseError(
                "Ollama returned an error during vision request",
                details=str(exc),
            ) from exc

        content = str(response.get("message", {}).get("content", ""))
        if not content.strip():
            raise LLMResponseError("Vision model returned an empty response")
        return content


def build_vision_client(settings: Settings) -> VisionClient:
    """Construct a VisionClient from application settings."""
    return VisionClient(
        host=settings.ollama_host,
        model=settings.vision_model,
        timeout=settings.ollama_timeout,
        temperature=settings.vision_temperature,
        max_tokens=settings.vision_max_tokens,
    )
