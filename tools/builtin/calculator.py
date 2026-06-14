"""Built-in calculator tool."""

from __future__ import annotations

from typing import Any

from tools.base import RiskLevel, Tool, ToolParameter, ToolResult
from tools.builtin.math_utils import safe_evaluate


class CalculatorTool(Tool):
    name = "calculator"
    description = "Evaluate a mathematical expression. Supports +, -, *, /, %, and parentheses."
    risk_level = RiskLevel.LOW
    parameters = [
        ToolParameter(
            name="expression",
            type="string",
            description="Mathematical expression to evaluate, e.g. '240 * 0.15'",
        ),
    ]

    def run(self, **kwargs: Any) -> ToolResult:
        expression = str(kwargs.get("expression", ""))
        result = safe_evaluate(expression)
        if result.is_integer():
            return ToolResult(success=True, output=str(int(result)))
        return ToolResult(success=True, output=str(result))
