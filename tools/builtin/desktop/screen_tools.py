"""Screen capture and clipboard tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from system.clipboard import read_clipboard
from system.screen import take_screenshot
from tools.base import RiskLevel, Tool, ToolParameter, ToolResult


class TakeScreenshotTool(Tool):
    name = "take_screenshot"
    description = "Capture the current screen and save it as a PNG image."
    risk_level = RiskLevel.LOW
    parameters = [
        ToolParameter(
            name="filename",
            type="string",
            description="Optional output filename (saved under data/screenshots/)",
            required=False,
        ),
    ]

    def __init__(self, *, screenshot_dir: Path) -> None:
        self.screenshot_dir = screenshot_dir

    def run(self, **kwargs: Any) -> ToolResult:
        filename = kwargs.get("filename")
        path = take_screenshot(
            self.screenshot_dir,
            filename=str(filename) if filename else None,
        )
        return ToolResult(success=True, output=f"Screenshot saved to {path}")


class ReadClipboardTool(Tool):
    name = "read_clipboard"
    description = "Read the current text contents of the Windows clipboard."
    risk_level = RiskLevel.MEDIUM
    parameters: list = []

    def run(self, **kwargs: Any) -> ToolResult:
        content = read_clipboard()
        if not content:
            return ToolResult(success=True, output="(clipboard is empty or contains non-text data)")
        return ToolResult(success=True, output=content)
