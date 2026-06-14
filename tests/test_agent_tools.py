"""Tests for agent tool-calling loop."""

import pytest

from agents.diablo_agent import DiabloAgent
from llm.base import LLMResponse
from tools.base import ToolCall
from tools.builtin.calculator import CalculatorTool
from tools.executor import ToolExecutor
from tools.registry import ToolRegistry


class ToolAwareFakeLLM:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def chat(self, messages, *, stream=False, tools=None):
        self.calls.append({"messages": messages, "tools": tools})
        if stream:
            raise AssertionError("streaming not expected in tool tests")

        if len(self.calls) == 1:
            return LLMResponse(
                content="",
                model="fake",
                tool_calls=[ToolCall(name="calculator", arguments={"expression": "6*7"})],
            )
        return LLMResponse(content="The answer is 42.", model="fake")

    def is_available(self) -> bool:
        return True

    def list_models(self) -> list[str]:
        return ["fake"]


def build_executor() -> ToolExecutor:
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    return ToolExecutor(registry)


def test_agent_runs_tool_loop() -> None:
    agent = DiabloAgent(
        ToolAwareFakeLLM(),
        tool_executor=build_executor(),
        tools_enabled=True,
        stream_responses=False,
    )
    response = agent.chat("What is 6 times 7?")
    assert response == "The answer is 42."
    assert len(agent.state.messages) >= 3


def test_list_tools() -> None:
    agent = DiabloAgent(
        ToolAwareFakeLLM(),
        tool_executor=build_executor(),
        tools_enabled=True,
    )
    tools = agent.list_tools()
    assert any("calculator" in item for item in tools)
