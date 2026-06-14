"""Tests for Diablo agent with memory integration."""

from pathlib import Path

import pytest

from agents.diablo_agent import DIABLO_SYSTEM_PROMPT, DiabloAgent
from config import Settings
from core.exceptions import DiabloError
from llm.base import ChatMessage, LLMResponse
from memory.embeddings import EmbeddingProvider
from memory.manager import MemoryManager


class FakeLLM:
    def __init__(self, available: bool = True) -> None:
        self.available = available
        self.calls: list[list[ChatMessage]] = []

    def chat(self, messages: list[ChatMessage], *, stream: bool = False, tools=None):
        self.calls.append(messages)
        if stream:
            return iter(["Test ", "response"])
        return LLMResponse(content="Test response", model="fake")

    def is_available(self) -> bool:
        return self.available

    def list_models(self) -> list[str]:
        return ["fake-model"]

    def ensure_model_available(self) -> None:
        return None


class FakeEmbeddingProvider(EmbeddingProvider):
    def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    def is_available(self) -> bool:
        return True


@pytest.fixture
def memory_manager(tmp_path: Path) -> MemoryManager:
    settings = Settings(
        data_dir=tmp_path / "data",
        sqlite_db_path=Path("diablo.db"),
        chroma_persist_dir=Path("chroma"),
    )
    return MemoryManager.from_settings(
        settings,
        system_prompt=DIABLO_SYSTEM_PROMPT,
        embedding_provider=FakeEmbeddingProvider(),
    )


def test_startup_check_fails_when_unavailable() -> None:
    agent = DiabloAgent(FakeLLM(available=False))
    with pytest.raises(DiabloError):
        agent.startup_check()


def test_chat_non_streaming() -> None:
    llm = FakeLLM()
    agent = DiabloAgent(llm, stream_responses=False)
    response = agent.chat("Hello")
    assert response == "Test response"
    assert llm.calls
    assert llm.calls[-1][-1].role == "user"
    assert llm.calls[-1][-1].content == "Hello"


def test_chat_streaming() -> None:
    llm = FakeLLM()
    agent = DiabloAgent(llm, stream_responses=True)
    stream = agent.chat("Hello")
    assert "".join(stream) == "Test response"


def test_empty_message_rejected() -> None:
    agent = DiabloAgent(FakeLLM())
    with pytest.raises(DiabloError):
        agent.chat("   ")


def test_reset_conversation_keeps_system_prompt() -> None:
    agent = DiabloAgent(FakeLLM(), stream_responses=False)
    agent.chat("Hello")
    agent.reset_conversation()
    assert agent.message_count == 1
    assert agent.state.messages[0].role == "system"
    assert DIABLO_SYSTEM_PROMPT in agent.state.messages[0].content


def test_chat_injects_memory_context(memory_manager: MemoryManager) -> None:
    memory_manager.remember("fact", "name", "Alex")
    llm = FakeLLM()
    agent = DiabloAgent(llm, memory=memory_manager, stream_responses=False)
    agent.chat("Who am I?")

    assert any("Alex" in message.content for message in llm.calls[-1])


def test_remember_command(memory_manager: MemoryManager) -> None:
    agent = DiabloAgent(FakeLLM(), memory=memory_manager)
    result = agent.remember("Favorite color is blue")
    assert "Remembered" in result
    assert any(item.value == "Favorite color is blue" for item in memory_manager.list_memories())
