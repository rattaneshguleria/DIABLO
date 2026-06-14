"""Tests for application management utilities."""

from pathlib import Path

import pytest

from core.exceptions import ToolExecutionError
from system.apps import resolve_app_executable


def test_resolve_notepad() -> None:
    path = resolve_app_executable("notepad")
    assert path.lower().endswith("notepad.exe")


def test_resolve_existing_path(tmp_path: Path) -> None:
    exe = tmp_path / "custom.exe"
    exe.write_text("fake", encoding="utf-8")
    assert resolve_app_executable(str(exe)) == str(exe)


def test_resolve_unknown_without_path() -> None:
    with pytest.raises(ToolExecutionError):
        resolve_app_executable("   ")
