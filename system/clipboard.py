"""Clipboard utilities."""

from __future__ import annotations

import logging

from core.exceptions import ToolExecutionError

logger = logging.getLogger("diablo.system.clipboard")


def read_clipboard() -> str:
    """Read text from the Windows clipboard."""
    try:
        import win32clipboard  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ToolExecutionError(
            "pywin32 is required for clipboard access",
            details="pip install pywin32",
        ) from exc

    try:
        win32clipboard.OpenClipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                return str(data)
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                return str(data)
            return ""
        finally:
            win32clipboard.CloseClipboard()
    except Exception as exc:  # noqa: BLE001 - clipboard API guard
        raise ToolExecutionError("Failed to read clipboard", details=str(exc)) from exc
