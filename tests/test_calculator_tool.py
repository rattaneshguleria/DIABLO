"""Tests for calculator and math utilities."""

import pytest

from core.exceptions import ToolExecutionError
from tools.builtin.calculator import CalculatorTool
from tools.builtin.math_utils import safe_evaluate


def test_safe_evaluate_basic() -> None:
    assert safe_evaluate("2 + 3") == 5
    assert safe_evaluate("240 * 0.15") == 36


def test_safe_evaluate_rejects_invalid_expression() -> None:
    with pytest.raises(ToolExecutionError):
        safe_evaluate("__import__('os')")


def test_calculator_tool() -> None:
    tool = CalculatorTool()
    result = tool.run(expression="10 / 4")
    assert result.success
    assert result.output == "2.5"
