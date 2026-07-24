"""Bounded autonomous task planning for Diablo."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field

from core.exceptions import DiabloError
from llm.base import ChatMessage, LLMProvider, LLMResponse
from tools.executor import ToolExecutor

logger = logging.getLogger("diablo.agents.planner")

PlannerActivityCallback = Callable[[str, str], None]

PLANNER_CONTEXT = """Task execution guidance:
- Break complex requests into the smallest useful tool steps.
- Inspect each tool result before choosing the next step.
- If a tool fails, correct its arguments or choose a safer alternative when possible.
- Stop when the user's request is complete; do not invent extra work.
"""


@dataclass(slots=True)
class PlanExecution:
    """The observable result of one bounded autonomous task."""

    response: str
    completed: bool
    tool_steps: int
    recovery_attempts: int
    failures: list[str] = field(default_factory=list)


class TaskPlanner:
    """Coordinate multi-step tool use while keeping execution bounded."""

    def __init__(
        self,
        llm: LLMProvider,
        tool_executor: ToolExecutor,
        *,
        max_steps: int = 8,
        max_recovery_attempts: int = 2,
        on_activity: PlannerActivityCallback | None = None,
    ) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1")
        if max_recovery_attempts < 0:
            raise ValueError("max_recovery_attempts cannot be negative")
        self.llm = llm
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.max_recovery_attempts = max_recovery_attempts
        self.on_activity = on_activity

    def execute(self, messages: list[ChatMessage]) -> PlanExecution:
        """Run a task until the model finishes or the safety bounds are reached."""
        tools = self.tool_executor.registry.schemas()
        working_messages = [
            ChatMessage(role="system", content=PLANNER_CONTEXT),
            *messages,
        ]
        failures: list[str] = []
        recovery_attempts = 0
        tool_steps = 0

        for _ in range(self.max_steps):
            result = self.llm.chat(working_messages, stream=False, tools=tools)
            if not isinstance(result, LLMResponse):
                raise DiabloError("Expected non-streaming LLM response")

            if not result.tool_calls:
                return PlanExecution(
                    response=result.content,
                    completed=True,
                    tool_steps=tool_steps,
                    recovery_attempts=recovery_attempts,
                    failures=failures,
                )

            tool_steps += 1
            working_messages.append(
                ChatMessage(
                    role="assistant",
                    content=result.content,
                    tool_calls=result.tool_calls,
                )
            )

            step_failed = False
            for call in result.tool_calls:
                self._notify(call.name, "running")
                tool_result = self.tool_executor.execute(call)
                status = "done" if tool_result.success else "failed"
                self._notify(call.name, status)
                working_messages.append(
                    ChatMessage(
                        role="tool",
                        content=tool_result.to_message_content(),
                        tool_name=call.name,
                    )
                )
                if not tool_result.success:
                    step_failed = True
                    failures.append(f"{call.name}: {tool_result.error or 'tool failed'}")

            if step_failed:
                recovery_attempts += 1
                if recovery_attempts > self.max_recovery_attempts:
                    return PlanExecution(
                        response=(
                            "I could not complete the task because a tool failed "
                            "after the recovery limit was reached."
                        ),
                        completed=False,
                        tool_steps=tool_steps,
                        recovery_attempts=recovery_attempts,
                        failures=failures,
                    )
                self._notify("plan", "recovering")

            logger.info(
                "Completed autonomous plan step %d; failures=%d",
                tool_steps,
                len(failures),
            )

        return PlanExecution(
            response=(
                "I reached the maximum number of planning steps for this request. "
                "Please try a simpler task or break it into smaller parts."
            ),
            completed=False,
            tool_steps=tool_steps,
            recovery_attempts=recovery_attempts,
            failures=failures,
        )

    def _notify(self, name: str, status: str) -> None:
        if self.on_activity is not None:
            self.on_activity(name, status)
