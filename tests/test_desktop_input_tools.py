"""Tests for desktop input tools."""

from tools.builtin.desktop.input_tools import MouseClickTool, PressHotkeyTool, TypeTextTool


def test_mouse_click_requires_confirmation() -> None:
    assert MouseClickTool().requires_confirmation() is True


def test_type_text_requires_confirmation() -> None:
    assert TypeTextTool().requires_confirmation() is True


def test_press_hotkey_blocks_dangerous_keys() -> None:
    import pytest

    from core.exceptions import ToolExecutionError

    tool = PressHotkeyTool()
    with pytest.raises(ToolExecutionError):
        tool.run(keys="ctrl,delete")
