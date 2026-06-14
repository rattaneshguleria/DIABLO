"""Built-in system information and command tools."""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Any

import psutil

from core.exceptions import ToolExecutionError
from tools.base import RiskLevel, Tool, ToolParameter, ToolResult
from tools.safety import is_command_allowed, parse_allowed_prefixes


class SystemInfoTool(Tool):
    name = "get_system_info"
    description = "Get basic system information: OS, CPU, memory, and disk usage."
    risk_level = RiskLevel.LOW
    parameters: list = []

    def run(self, **kwargs: Any) -> ToolResult:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/") if os.name != "nt" else psutil.disk_usage("C:\\")
        lines = [
            f"OS: {platform.system()} {platform.release()} ({platform.version()})",
            f"Machine: {platform.machine()}",
            f"Processor: {platform.processor() or 'unknown'}",
            f"CPU cores: {psutil.cpu_count(logical=True)}",
            f"CPU usage: {psutil.cpu_percent(interval=0.1)}%",
            f"Memory total: {memory.total // (1024 ** 2)} MB",
            f"Memory used: {memory.percent}%",
            f"Disk total: {disk.total // (1024 ** 3)} GB",
            f"Disk used: {disk.percent}%",
        ]
        return ToolResult(success=True, output="\n".join(lines))


class RunCommandTool(Tool):
    name = "run_command"
    description = (
        "Run a safe shell command. Only allowed command prefixes are permitted. "
        "Requires user confirmation before execution."
    )
    risk_level = RiskLevel.HIGH
    parameters = [
        ToolParameter(
            name="command",
            type="string",
            description="Shell command to execute",
        ),
    ]

    def __init__(
        self,
        *,
        allowed_prefixes: str,
        timeout: int,
        working_dir: Path,
    ) -> None:
        self.allowed_prefixes = parse_allowed_prefixes(allowed_prefixes)
        self.timeout = timeout
        self.working_dir = working_dir

    def requires_confirmation(self) -> bool:
        return True

    def run(self, **kwargs: Any) -> ToolResult:
        command = str(kwargs.get("command", "")).strip()
        if not command:
            return ToolResult(success=False, output="", error="Command cannot be empty")

        if not is_command_allowed(command, self.allowed_prefixes):
            return ToolResult(
                success=False,
                output="",
                error=(
                    "Command not allowed. Permitted prefixes: "
                    + ", ".join(self.allowed_prefixes)
                ),
            )

        try:
            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.working_dir,
            )
        except subprocess.TimeoutExpired:
            raise ToolExecutionError(
                "Command timed out",
                details=f"Timeout after {self.timeout} seconds",
            ) from None

        output = (completed.stdout or "") + (completed.stderr or "")
        output = output.strip() or "(no output)"
        status = f"exit_code={completed.returncode}"
        return ToolResult(success=True, output=f"{output}\n\n[{status}]")
