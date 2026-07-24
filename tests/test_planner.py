from llm.base import ChatMessage, LLMResponse
from agents.planner import TaskPlanner
from tools.base import ToolCall
from tools.executor import ToolExecutor
from tools.registry import ToolRegistry


class FakeLLM:
    def __init__(self) -> None:
        self.calls: list[list[ChatMessage]] = []
        self.responses = [
            LLMResponse(
                content="",
                model="fake",
                tool_calls=[ToolCall(name="missing", arguments={})],
            ),
            LLMResponse(content="Task recovered and completed.", model="fake"),
        ]

    def chat(self, messages, *, stream=False, tools=None):
        self.calls.append(messages)
        return self.responses.pop(0)

    def is_available(self) -> bool:
        return True

    def list_models(self) -> list[str]:
        return ["fake"]


def test_planner_recovers_from_failed_tool() -> None:
    llm = FakeLLM()
    planner = TaskPlanner(
        llm,
        ToolExecutor(ToolRegistry()),
        max_steps=3,
        max_recovery_attempts=1,
    )

    execution = planner.execute([ChatMessage(role="user", content="Do the task")])

    assert execution.completed
    assert execution.tool_steps == 1
    assert execution.recovery_attempts == 1
    assert execution.failures == ["missing: Tool 'missing' is not registered"]
    assert llm.calls[1][-1].role == "tool"
    assert "not registered" in llm.calls[1][-1].content


def test_planner_stops_after_recovery_limit() -> None:
    llm = FakeLLM()
    llm.responses = [
        LLMResponse(
            content="",
            model="fake",
            tool_calls=[ToolCall(name="missing", arguments={})],
        ),
        LLMResponse(
            content="",
            model="fake",
            tool_calls=[ToolCall(name="missing", arguments={})],
        ),
    ]
    planner = TaskPlanner(
        llm,
        ToolExecutor(ToolRegistry()),
        max_steps=3,
        max_recovery_attempts=1,
    )

    execution = planner.execute([ChatMessage(role="user", content="Do the task")])

    assert not execution.completed
    assert execution.recovery_attempts == 2
    assert execution.tool_steps == 2
