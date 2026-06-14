"""Tests for tool registry."""

from tools.base import RiskLevel, Tool, ToolParameter, ToolResult
from tools.registry import ToolRegistry


class EchoTool(Tool):
    name = "echo"
    description = "Echo text"
    risk_level = RiskLevel.LOW
    parameters = [
        ToolParameter(name="text", type="string", description="Text to echo"),
    ]

    def run(self, **kwargs):
        return ToolResult(success=True, output=str(kwargs.get("text", "")))


def test_register_and_get_tool() -> None:
    registry = ToolRegistry()
    tool = EchoTool()
    registry.register(tool)
    assert registry.get("echo") is tool


def test_schemas_include_registered_tool() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())
    schemas = registry.schemas()
    assert schemas[0]["function"]["name"] == "echo"
