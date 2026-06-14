"""Tool registration and lookup."""

from __future__ import annotations

import logging

from core.exceptions import ToolNotFoundError
from tools.base import Tool, ToolSchema

logger = logging.getLogger("diablo.tools.registry")


class ToolRegistry:
    """Central registry of available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool
        logger.debug("Registered tool: %s", tool.name)

    def get(self, name: str) -> Tool:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFoundError(f"Tool '{name}' is not registered")
        return tool

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def list_names(self) -> list[str]:
        return sorted(self._tools.keys())

    def schemas(self) -> list[dict]:
        return [tool.get_schema().to_ollama_tool() for tool in self._tools.values()]

    def describe_tools(self) -> list[str]:
        return [f"{tool.name} ({tool.risk_level.value}): {tool.description}" for tool in self._tools.values()]

    def __len__(self) -> int:
        return len(self._tools)
