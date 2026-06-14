"""Tests for Ollama client."""

from unittest.mock import MagicMock

import httpx
import ollama
import pytest

from core.exceptions import LLMConnectionError, LLMResponseError, ModelNotFoundError
from llm.base import ChatMessage
from llm.ollama_client import OllamaClient


@pytest.fixture
def client() -> OllamaClient:
    return OllamaClient(model="llama3.2")


def test_is_available_true(client: OllamaClient, mocker) -> None:
    mocker.patch.object(client._client, "list", return_value={"models": []})
    assert client.is_available() is True


def test_is_available_false_on_connection_error(client: OllamaClient, mocker) -> None:
    mocker.patch.object(client._client, "list", side_effect=httpx.ConnectError("down"))
    assert client.is_available() is False


def test_list_models(client: OllamaClient, mocker) -> None:
    mocker.patch.object(
        client._client,
        "list",
        return_value={"models": [{"name": "llama3.2:latest"}]},
    )
    assert client.list_models() == ["llama3.2:latest"]


def test_list_models_connection_error(client: OllamaClient, mocker) -> None:
    mocker.patch.object(client._client, "list", side_effect=httpx.ConnectError("down"))
    with pytest.raises(LLMConnectionError):
        client.list_models()


def test_ensure_model_available_success(client: OllamaClient, mocker) -> None:
    mocker.patch.object(client, "list_models", return_value=["llama3.2:latest"])
    client.ensure_model_available()


def test_ensure_model_available_missing(client: OllamaClient, mocker) -> None:
    mocker.patch.object(client, "list_models", return_value=["qwen3:latest"])
    with pytest.raises(ModelNotFoundError):
        client.ensure_model_available()


def test_chat_complete(client: OllamaClient, mocker) -> None:
    mocker.patch.object(
        client._client,
        "chat",
        return_value={
            "model": "llama3.2",
            "message": {"role": "assistant", "content": "Hello"},
        },
    )
    response = client.chat([ChatMessage(role="user", content="Hi")], stream=False)
    assert response.content == "Hello"


def test_chat_empty_response_raises(client: OllamaClient, mocker) -> None:
    mocker.patch.object(
        client._client,
        "chat",
        return_value={"model": "llama3.2", "message": {"role": "assistant", "content": ""}},
    )
    with pytest.raises(LLMResponseError):
        client.chat([ChatMessage(role="user", content="Hi")], stream=False)


def test_chat_model_not_found(client: OllamaClient, mocker) -> None:
    mocker.patch.object(
        client._client,
        "chat",
        side_effect=ollama.ResponseError("model not found"),
    )
    with pytest.raises(ModelNotFoundError):
        client.chat([ChatMessage(role="user", content="Hi")], stream=False)


def test_chat_stream(client: OllamaClient, mocker) -> None:
    chunks = [
        {"message": {"content": "Hel"}},
        {"message": {"content": "lo"}},
    ]
    mocker.patch.object(client._client, "chat", return_value=iter(chunks))
    stream = client.chat([ChatMessage(role="user", content="Hi")], stream=True)
    assert "".join(stream) == "Hello"
