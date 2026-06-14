"""Mouse and keyboard control tools."""

from __future__ import annotations

from typing import Any

from core.exceptions import ToolExecutionError
from tools.base import RiskLevel, Tool, ToolParameter, ToolResult


class MouseClickTool(Tool):
    name = "mouse_click"
    description = (
        "Move the mouse to screen coordinates (x, y) and click. "
        "Requires user confirmation."
    )
    risk_level = RiskLevel.HIGH
    parameters = [
        ToolParameter(
            name="x",
            type="integer",
            description="Horizontal screen coordinate",
        ),
        ToolParameter(
            name="y",
            type="integer",
            description="Vertical screen coordinate",
        ),
        ToolParameter(
            name="button",
            type="string",
            description="Mouse button: left, right, or middle",
            required=False,
        ),
        ToolParameter(
            name="clicks",
            type="integer",
            description="Number of clicks (default 1)",
            required=False,
        ),
    ]

    def requires_confirmation(self) -> bool:
        return True

    def run(self, **kwargs: Any) -> ToolResult:
        import pyautogui

        x = int(kwargs.get("x", 0))
        y = int(kwargs.get("y", 0))
        button = str(kwargs.get("button") or "left").lower()
        clicks = int(kwargs.get("clicks") or 1)

        if button not in {"left", "right", "middle"}:
            return ToolResult(success=False, output="", error="Button must be left, right, or middle")

        pyautogui.moveTo(x, y)
        pyautogui.click(x=x, y=y, button=button, clicks=clicks)
        return ToolResult(success=True, output=f"Clicked {button} at ({x}, {y})")


class TypeTextTool(Tool):
    name = "type_text"
    description = "Type text using the keyboard at the current cursor position. Requires user confirmation."
    risk_level = RiskLevel.HIGH
    parameters = [
        ToolParameter(
            name="text",
            type="string",
            description="Text to type",
        ),
        ToolParameter(
            name="interval",
            type="number",
            description="Delay between keystrokes in seconds (default 0.02)",
            required=False,
        ),
    ]

    def requires_confirmation(self) -> bool:
        return True

    def run(self, **kwargs: Any) -> ToolResult:
        import pyautogui

        text = str(kwargs.get("text", ""))
        interval = float(kwargs.get("interval") or 0.02)
        if not text:
            return ToolResult(success=False, output="", error="Text cannot be empty")

        pyautogui.write(text, interval=interval)
        return ToolResult(success=True, output=f"Typed {len(text)} characters")


class PressHotkeyTool(Tool):
    name = "press_hotkey"
    description = (
        "Press a keyboard shortcut, e.g. 'ctrl,c' for copy or 'alt,tab' for app switch. "
        "Requires user confirmation."
    )
    risk_level = RiskLevel.HIGH
    parameters = [
        ToolParameter(
            name="keys",
            type="string",
            description="Comma-separated keys to press together, e.g. 'ctrl,shift,s'",
        ),
    ]

    def requires_confirmation(self) -> bool:
        return True

    def run(self, **kwargs: Any) -> ToolResult:
        import pyautogui

        raw_keys = str(kwargs.get("keys", "")).strip()
        if not raw_keys:
            return ToolResult(success=False, output="", error="Keys cannot be empty")

        keys = [key.strip().lower() for key in raw_keys.split(",") if key.strip()]
        if not keys:
            return ToolResult(success=False, output="", error="Keys cannot be empty")

        blocked = {"win", "windows", "super", "cmd", "delete", "del"}
        if any(key in blocked for key in keys):
            raise ToolExecutionError("This hotkey combination is blocked for safety")

        pyautogui.hotkey(*keys)
        return ToolResult(success=True, output=f"Pressed hotkey: {'+'.join(keys)}")
