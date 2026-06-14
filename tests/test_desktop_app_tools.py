"""Tests for desktop application tools."""

from unittest.mock import MagicMock

from tools.builtin.desktop.app_tools import CloseApplicationTool, LaunchApplicationTool


def test_launch_application_tool(mocker) -> None:
    mock_launch = mocker.patch(
        "tools.builtin.desktop.app_tools.launch_application",
        return_value="notepad.exe",
    )
    tool = LaunchApplicationTool()
    result = tool.run(app_name="notepad")
    assert result.success
    assert "notepad.exe" in result.output
    mock_launch.assert_called_once()


def test_close_application_requires_confirmation() -> None:
    tool = CloseApplicationTool()
    assert tool.requires_confirmation() is True


def test_close_application_tool(mocker) -> None:
    mocker.patch(
        "tools.builtin.desktop.app_tools.close_application",
        return_value=1,
    )
    tool = CloseApplicationTool()
    result = tool.run(process_name="notepad")
    assert result.success
    assert "Closed 1" in result.output
