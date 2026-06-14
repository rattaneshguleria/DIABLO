"""Safe mathematical expression evaluation."""

from __future__ import annotations

import ast
import operator

from core.exceptions import ToolExecutionError

SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_evaluate(expression: str) -> float:
    """Evaluate a math expression using a restricted AST visitor."""
    cleaned = expression.strip()
    if not cleaned:
        raise ToolExecutionError("Expression cannot be empty")

    try:
        node = ast.parse(cleaned, mode="eval")
    except SyntaxError as exc:
        raise ToolExecutionError("Invalid math expression", details=str(exc)) from exc

    return float(_evaluate_node(node.body))


def _evaluate_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)

    if isinstance(node, ast.UnaryOp) and type(node.op) in SAFE_OPERATORS:
        return SAFE_OPERATORS[type(node.op)](_evaluate_node(node.operand))

    if isinstance(node, ast.BinOp) and type(node.op) in SAFE_OPERATORS:
        return SAFE_OPERATORS[type(node.op)](
            _evaluate_node(node.left),
            _evaluate_node(node.right),
        )

    raise ToolExecutionError("Unsupported expression")
