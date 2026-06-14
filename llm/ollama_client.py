"""Ollama LLM client for local model inference."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from typing import Any

import httpx
import ollama

from core.exceptions import LLMConnectionError, LLMResponseError, ModelNotFoundError
from llm.base import ChatMessage, LLMProvider, LLMResponse
from tools.base import ToolCall

logger = logging.getLogger("diablo.llm.ollama")


class OllamaClient(LLMProvider):
    """Production-ready Ollama client with connection checks and error handling."""

    def __init__(
        self,
        *,
        host: str = "http://localhost:11434",
        model: str = "llama3.2",
        timeout: int = 120,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = ollama.Client(host=self.host, timeout=self.timeout)

    def is_available(self) -> bool:
        """Ping Ollama server."""
        try:
            self._client.list()
            return True
        except (httpx.ConnectError, httpx.TimeoutException, ConnectionError) as exc:
            logger.warning("Ollama unavailable at %s: %s", self.host, exc)
            return False
        except Exception as exc:  # noqa: BLE001 - surface unexpected provider errors
            logger.error("Unexpected error checking Ollama: %s", exc)
            return False

    def list_models(self) -> list[str]:
        """Return installed model names."""
        try:
            response = self._client.list()
            models: list[str] = []
            for item in response.get("models", []):
                name = item.get("name") or item.get("model")
                if name:
                    models.append(name)
            return models
        except (httpx.ConnectError, httpx.TimeoutException, ConnectionError) as exc:
            raise LLMConnectionError(
                "Cannot connect to Ollama",
                details=str(exc),
            ) from exc

    def ensure_model_available(self) -> None:
        """Verify the configured model exists locally."""
        models = self.list_models()
        if not models:
            raise ModelNotFoundError(
                "No models found in Ollama",
                details=f"Pull a model with: ollama pull {self.model}",
            )

        normalized = {m.split(":")[0] for m in models}
        requested = self.model.split(":")[0]
        if requested not in normalized and self.model not in models:
            raise ModelNotFoundError(
                f"Model '{self.model}' is not installed",
                details=(
                    f"Available models: {', '.join(models)}. "
                    f"Install with: ollama pull {self.model}"
                ),
            )

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        stream: bool = False,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse | Iterator[str]:
        payload = [message.to_dict() for message in messages]
        options: dict[str, Any] = {
            "temperature": self.temperature,
            "num_predict": self.max_tokens,
        }

        try:
            if stream:
                if tools:
                    raise LLMResponseError("Streaming is not supported with tools")
                return self._stream_chat(payload, options)
            return self._complete_chat(payload, options, tools=tools)
        except (httpx.ConnectError, httpx.TimeoutException, ConnectionError) as exc:
            raise LLMConnectionError(
                "Lost connection to Ollama during chat",
                details=str(exc),
            ) from exc
        except ollama.ResponseError as exc:
            if "not found" in str(exc).lower():
                raise ModelNotFoundError(
                    f"Model '{self.model}' not found",
                    details=str(exc),
                ) from exc
            raise LLMResponseError("Ollama returned an error", details=str(exc)) from exc

    def _complete_chat(
        self,
        payload: list[dict[str, Any]],
        options: dict[str, Any],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        logger.debug("Sending chat request to model=%s tools=%s", self.model, bool(tools))
        request_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": payload,
            "options": options,
            "stream": False,
        }
        if tools:
            request_kwargs["tools"] = tools

        response = self._client.chat(**request_kwargs)
        content = self._extract_content(response)
        tool_calls = self._extract_tool_calls(response)

        if not content.strip() and not tool_calls:
            raise LLMResponseError("Ollama returned an empty response")

        return LLMResponse(
            content=content,
            model=response.get("model", self.model),
            tool_calls=tool_calls,
            metadata={
                "total_duration": response.get("total_duration"),
                "eval_count": response.get("eval_count"),
            },
        )

    def _stream_chat(
        self,
        payload: list[dict[str, str]],
        options: dict[str, Any],
    ) -> Iterator[str]:
        logger.debug("Streaming chat request to model=%s", self.model)
        stream = self._client.chat(
            model=self.model,
            messages=payload,
            options=options,
            stream=True,
        )

        emitted = False
        for chunk in stream:
            content = self._extract_content(chunk)
            if content:
                emitted = True
                yield content

        if not emitted:
            raise LLMResponseError("Ollama stream ended without content")

    @staticmethod
    def _extract_content(response: dict[str, Any]) -> str:
        message = response.get("message", {})
        return str(message.get("content", ""))

    @staticmethod
    def _extract_tool_calls(response: dict[str, Any]) -> list[ToolCall]:
        message = response.get("message", {})
        raw_calls = message.get("tool_calls") or []
        tool_calls: list[ToolCall] = []

        for item in raw_calls:
            function = item.get("function", {})
            name = function.get("name")
            if not name:
                continue

            arguments = function.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {"raw": arguments}

            if not isinstance(arguments, dict):
                arguments = {"value": arguments}

            tool_calls.append(
                ToolCall(
                    name=str(name),
                    arguments=arguments,
                    call_id=item.get("id"),
                )
            )

        return tool_calls
