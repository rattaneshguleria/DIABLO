"""Factory for building the default Diablo tool registry."""

from __future__ import annotations

import logging
from pathlib import Path

from config import Settings
from tools.base import ConfirmationCallback, Tool
from tools.builtin.calculator import CalculatorTool
from tools.builtin.datetime_tool import DateTimeTool
from tools.builtin.desktop.app_tools import (
    CloseApplicationTool,
    LaunchApplicationTool,
    ListRunningApplicationsTool,
)
from tools.builtin.desktop.audio_tools import GetVolumeTool, SetVolumeTool
from tools.builtin.desktop.file_tools import CreateFolderTool, MoveFileTool, RenameFileTool
from tools.builtin.desktop.input_tools import MouseClickTool, PressHotkeyTool, TypeTextTool
from tools.builtin.desktop.screen_tools import ReadClipboardTool, TakeScreenshotTool
from tools.builtin.file_tools import ListDirectoryTool, ReadFileTool, SearchFilesTool, WriteFileTool
from tools.builtin.system_tools import RunCommandTool, SystemInfoTool
from tools.builtin.web_tools import FetchUrlTool, WebSearchTool
from tools.executor import ToolExecutor
from tools.registry import ToolRegistry

logger = logging.getLogger("diablo.tools.factory")


def _configure_pyautogui() -> None:
    try:
        import pyautogui

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    except ImportError:
        logger.debug("pyautogui not installed; desktop input tools unavailable")


def build_tool_registry(settings: Settings) -> ToolRegistry:
    """Create and populate the default tool registry."""
    registry = ToolRegistry()
    workspace = settings.tool_workspace_dir
    if workspace is not None and not workspace.is_absolute():
        workspace = settings.base_dir / workspace

    tools: list[Tool] = [
        CalculatorTool(),
        DateTimeTool(),
        ReadFileTool(
            workspace=workspace,
            base_dir=settings.base_dir,
            max_bytes=settings.max_file_read_bytes,
        ),
        WriteFileTool(workspace=workspace, base_dir=settings.base_dir),
        ListDirectoryTool(workspace=workspace, base_dir=settings.base_dir),
        SearchFilesTool(workspace=workspace, base_dir=settings.base_dir),
        SystemInfoTool(),
        RunCommandTool(
            allowed_prefixes=settings.allowed_command_prefixes,
            timeout=settings.command_timeout,
            working_dir=workspace or settings.base_dir,
        ),
    ]

    if settings.web_search_enabled:
        tools.extend([WebSearchTool(), FetchUrlTool()])

    if settings.desktop_control_enabled:
        _configure_pyautogui()
        screenshot_dir = settings.screenshot_dir
        if not screenshot_dir.is_absolute():
            screenshot_dir = settings.data_dir / screenshot_dir

        tools.extend(
            [
                LaunchApplicationTool(),
                CloseApplicationTool(),
                ListRunningApplicationsTool(),
                CreateFolderTool(workspace=workspace, base_dir=settings.base_dir),
                MoveFileTool(workspace=workspace, base_dir=settings.base_dir),
                RenameFileTool(workspace=workspace, base_dir=settings.base_dir),
                TakeScreenshotTool(screenshot_dir=screenshot_dir),
                ReadClipboardTool(),
                GetVolumeTool(),
                SetVolumeTool(),
                MouseClickTool(),
                TypeTextTool(),
                PressHotkeyTool(),
            ]
        )

    for tool in tools:
        registry.register(tool)

    return registry


def build_tool_executor(
    settings: Settings,
    *,
    confirm_callback: ConfirmationCallback | None = None,
) -> ToolExecutor:
    """Create a tool executor with audit logging and safety settings."""
    registry = build_tool_registry(settings)
    audit_path = settings.log_dir / "tool_audit.jsonl" if settings.log_dir else None
    require_confirmation = (
        settings.require_confirmation_for_commands
        or settings.require_confirmation_for_desktop_input
    )
    return ToolExecutor(
        registry,
        audit_log_path=audit_path,
        require_confirmation_for_high_risk=require_confirmation,
        confirm_callback=confirm_callback,
    )
