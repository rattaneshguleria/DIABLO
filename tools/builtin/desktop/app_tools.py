"""Desktop application control tools."""

from __future__ import annotations

from typing import Any

from system.apps import close_application, launch_application, list_running_applications
from tools.base import RiskLevel, Tool, ToolParameter, ToolResult


class LaunchApplicationTool(Tool):
    name = "launch_application"
    description = (
        "Launch a desktop application. Supports friendly names: chrome, vscode, spotify, "
        "notepad, explorer, or a full executable path."
    )
    risk_level = RiskLevel.MEDIUM
    parameters = [
        ToolParameter(
            name="app_name",
            type="string",
            description="Application name or executable path",
        ),
        ToolParameter(
            name="arguments",
            type="string",
            description="Optional command-line arguments",
            required=False,
        ),
    ]

    def run(self, **kwargs: Any) -> ToolResult:
        app_name = str(kwargs.get("app_name", ""))
        arguments = str(kwargs.get("arguments", ""))
        launched = launch_application(app_name, arguments=arguments)
        return ToolResult(success=True, output=f"Launched: {launched}")


class CloseApplicationTool(Tool):
    name = "close_application"
    description = (
        "Close a running application by process name, e.g. 'chrome', 'Spotify', or 'notepad'. "
        "Requires user confirmation."
    )
    risk_level = RiskLevel.HIGH
    parameters = [
        ToolParameter(
            name="process_name",
            type="string",
            description="Process name to close, e.g. 'chrome' or 'notepad.exe'",
        ),
        ToolParameter(
            name="force",
            type="boolean",
            description="Force kill the process if graceful close fails",
            required=False,
        ),
    ]

    def requires_confirmation(self) -> bool:
        return True

    def run(self, **kwargs: Any) -> ToolResult:
        process_name = str(kwargs.get("process_name", ""))
        force = bool(kwargs.get("force", False))
        count = close_application(process_name, force=force)
        return ToolResult(success=True, output=f"Closed {count} process(es) matching '{process_name}'")


class ListRunningApplicationsTool(Tool):
    name = "list_running_applications"
    description = "List currently running application process names."
    risk_level = RiskLevel.LOW
    parameters = [
        ToolParameter(
            name="limit",
            type="integer",
            description="Maximum number of process names to return",
            required=False,
        ),
    ]

    def run(self, **kwargs: Any) -> ToolResult:
        limit = int(kwargs.get("limit") or 30)
        apps = list_running_applications(limit=limit)
        if not apps:
            return ToolResult(success=True, output="No processes found.")
        return ToolResult(success=True, output="\n".join(apps))
