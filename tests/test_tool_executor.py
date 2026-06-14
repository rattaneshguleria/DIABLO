"""Tests for tool executor."""

from pathlib import Path

from tools.base import ToolCall
from tools.builtin.calculator import CalculatorTool
from tools.executor import ToolExecutor
from tools.registry import ToolRegistry


def test_execute_successful_tool(tmp_path: Path) -> None:
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    executor = ToolExecutor(registry, audit_log_path=tmp_path / "audit.jsonl")

    result = executor.execute(ToolCall(name="calculator", arguments={"expression": "2+2"}))
    assert result.success
    assert result.output == "4"
    assert len(executor.audit_history) == 1


def test_execute_unknown_tool() -> None:
    registry = ToolRegistry()
    executor = ToolExecutor(registry)
    result = executor.execute(ToolCall(name="missing", arguments={}))
    assert not result.success
    assert "not registered" in (result.error or "")


def test_high_risk_tool_requires_confirmation(tmp_path: Path) -> None:
    from tools.builtin.system_tools import RunCommandTool

    registry = ToolRegistry()
    registry.register(
        RunCommandTool(
            allowed_prefixes="echo",
            timeout=5,
            working_dir=tmp_path,
        )
    )
    executor = ToolExecutor(
        registry,
        require_confirmation_for_high_risk=True,
        confirm_callback=lambda _msg: False,
    )
    result = executor.execute(ToolCall(name="run_command", arguments={"command": "echo hi"}))
    assert not result.success
    assert "denied" in (result.error or "").lower()
