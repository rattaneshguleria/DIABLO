"""Volume control tools."""

from __future__ import annotations

from typing import Any

from system.volume import get_volume_percent, set_volume_percent
from tools.base import RiskLevel, Tool, ToolParameter, ToolResult


class GetVolumeTool(Tool):
    name = "get_volume"
    description = "Get the current system master volume percentage."
    risk_level = RiskLevel.LOW
    parameters: list = []

    def run(self, **kwargs: Any) -> ToolResult:
        level = get_volume_percent()
        return ToolResult(success=True, output=f"Volume: {level}%")


class SetVolumeTool(Tool):
    name = "set_volume"
    description = "Set the system master volume to a percentage between 0 and 100."
    risk_level = RiskLevel.MEDIUM
    parameters = [
        ToolParameter(
            name="level",
            type="integer",
            description="Target volume percentage (0-100)",
        ),
    ]

    def run(self, **kwargs: Any) -> ToolResult:
        level = int(kwargs.get("level", -1))
        set_volume_percent(level)
        return ToolResult(success=True, output=f"Volume set to {level}%")
