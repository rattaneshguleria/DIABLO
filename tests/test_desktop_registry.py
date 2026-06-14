"""Tests for desktop tool registration."""

from config import Settings
from tools.factory import build_tool_registry


def test_desktop_tools_registered_by_default() -> None:
    registry = build_tool_registry(Settings())
    names = registry.list_names()
    assert "launch_application" in names
    assert "take_screenshot" in names
    assert "mouse_click" in names


def test_desktop_tools_disabled() -> None:
    registry = build_tool_registry(Settings(desktop_control_enabled=False))
    names = registry.list_names()
    assert "launch_application" not in names
    assert "calculator" in names
