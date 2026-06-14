"""Built-in date and time tool."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from tools.base import RiskLevel, Tool, ToolParameter, ToolResult


class DateTimeTool(Tool):
    name = "get_current_time"
    description = "Get the current date and time, optionally in a specific timezone."
    risk_level = RiskLevel.LOW
    parameters = [
        ToolParameter(
            name="timezone",
            type="string",
            description="IANA timezone name, e.g. 'UTC' or 'Asia/Kolkata'. Defaults to local time.",
            required=False,
        ),
    ]

    def run(self, **kwargs: Any) -> ToolResult:
        timezone_name = kwargs.get("timezone")
        if timezone_name:
            try:
                now = datetime.now(ZoneInfo(str(timezone_name)))
            except Exception as exc:  # noqa: BLE001 - invalid timezone names
                return ToolResult(success=False, output="", error=f"Invalid timezone: {exc}")
        else:
            now = datetime.now().astimezone()

        formatted = now.strftime("%A, %B %d, %Y %H:%M:%S %Z")
        return ToolResult(success=True, output=formatted)
