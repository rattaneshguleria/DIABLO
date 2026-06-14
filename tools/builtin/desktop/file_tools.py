"""Extended file management tools for desktop control."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from tools.base import RiskLevel, Tool, ToolParameter, ToolResult
from tools.safety import resolve_safe_path


class CreateFolderTool(Tool):
    name = "create_folder"
    description = "Create a new folder (and any parent folders needed)."
    risk_level = RiskLevel.LOW
    parameters = [
        ToolParameter(
            name="path",
            type="string",
            description="Folder path to create",
        ),
    ]

    def __init__(self, *, workspace: Path | None, base_dir: Path) -> None:
        self.workspace = workspace
        self.base_dir = base_dir

    def run(self, **kwargs: Any) -> ToolResult:
        path = resolve_safe_path(
            str(kwargs.get("path", "")),
            workspace=self.workspace,
            base_dir=self.base_dir,
        )
        path.mkdir(parents=True, exist_ok=True)
        return ToolResult(success=True, output=f"Created folder: {path}")


class MoveFileTool(Tool):
    name = "move_file"
    description = "Move or rename a file or folder to a new location."
    risk_level = RiskLevel.MEDIUM
    parameters = [
        ToolParameter(
            name="source",
            type="string",
            description="Source file or folder path",
        ),
        ToolParameter(
            name="destination",
            type="string",
            description="Destination path",
        ),
    ]

    def __init__(self, *, workspace: Path | None, base_dir: Path) -> None:
        self.workspace = workspace
        self.base_dir = base_dir

    def run(self, **kwargs: Any) -> ToolResult:
        source = resolve_safe_path(
            str(kwargs.get("source", "")),
            workspace=self.workspace,
            base_dir=self.base_dir,
        )
        destination = resolve_safe_path(
            str(kwargs.get("destination", "")),
            workspace=self.workspace,
            base_dir=self.base_dir,
        )
        if not source.exists():
            return ToolResult(success=False, output="", error=f"Source not found: {source}")

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        return ToolResult(success=True, output=f"Moved {source} -> {destination}")


class RenameFileTool(Tool):
    name = "rename_file"
    description = "Rename a file or folder in place."
    risk_level = RiskLevel.MEDIUM
    parameters = [
        ToolParameter(
            name="path",
            type="string",
            description="Path to the file or folder to rename",
        ),
        ToolParameter(
            name="new_name",
            type="string",
            description="New filename (not full path)",
        ),
    ]

    def __init__(self, *, workspace: Path | None, base_dir: Path) -> None:
        self.workspace = workspace
        self.base_dir = base_dir

    def run(self, **kwargs: Any) -> ToolResult:
        source = resolve_safe_path(
            str(kwargs.get("path", "")),
            workspace=self.workspace,
            base_dir=self.base_dir,
        )
        new_name = str(kwargs.get("new_name", "")).strip()
        if not new_name:
            return ToolResult(success=False, output="", error="New name cannot be empty")
        if not source.exists():
            return ToolResult(success=False, output="", error=f"Path not found: {source}")

        destination = source.with_name(new_name)
        source.rename(destination)
        return ToolResult(success=True, output=f"Renamed to {destination}")
