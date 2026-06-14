"""Built-in file management tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.exceptions import ToolExecutionError
from tools.base import RiskLevel, Tool, ToolParameter, ToolResult
from tools.safety import resolve_safe_path, validate_read_size


class ReadFileTool(Tool):
    name = "read_file"
    description = "Read the contents of a text file."
    risk_level = RiskLevel.MEDIUM
    parameters = [
        ToolParameter(
            name="path",
            type="string",
            description="Path to the file to read",
        ),
    ]

    def __init__(self, *, workspace: Path | None, base_dir: Path, max_bytes: int) -> None:
        self.workspace = workspace
        self.base_dir = base_dir
        self.max_bytes = max_bytes

    def run(self, **kwargs: Any) -> ToolResult:
        path = resolve_safe_path(
            str(kwargs.get("path", "")),
            workspace=self.workspace,
            base_dir=self.base_dir,
        )
        if not path.is_file():
            return ToolResult(success=False, output="", error=f"File not found: {path}")

        validate_read_size(path, self.max_bytes)
        content = path.read_text(encoding="utf-8", errors="replace")
        return ToolResult(success=True, output=content)


class WriteFileTool(Tool):
    name = "write_file"
    description = "Write text content to a file. Creates parent directories if needed."
    risk_level = RiskLevel.MEDIUM
    parameters = [
        ToolParameter(
            name="path",
            type="string",
            description="Path to the file to write",
        ),
        ToolParameter(
            name="content",
            type="string",
            description="Text content to write",
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
        content = str(kwargs.get("content", ""))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return ToolResult(success=True, output=f"Wrote {len(content)} characters to {path}")


class ListDirectoryTool(Tool):
    name = "list_directory"
    description = "List files and folders in a directory."
    risk_level = RiskLevel.LOW
    parameters = [
        ToolParameter(
            name="path",
            type="string",
            description="Directory path to list. Defaults to workspace root.",
            required=False,
        ),
    ]

    def __init__(self, *, workspace: Path | None, base_dir: Path) -> None:
        self.workspace = workspace
        self.base_dir = base_dir

    def run(self, **kwargs: Any) -> ToolResult:
        raw_path = str(kwargs.get("path") or ".")
        path = resolve_safe_path(raw_path, workspace=self.workspace, base_dir=self.base_dir)
        if not path.is_dir():
            return ToolResult(success=False, output="", error=f"Directory not found: {path}")

        entries = sorted(path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
        lines = []
        for entry in entries[:200]:
            kind = "DIR " if entry.is_dir() else "FILE"
            lines.append(f"[{kind}] {entry.name}")
        if len(entries) > 200:
            lines.append(f"... and {len(entries) - 200} more entries")
        return ToolResult(success=True, output="\n".join(lines) if lines else "(empty directory)")


class SearchFilesTool(Tool):
    name = "search_files"
    description = "Search for files by name pattern within a directory tree."
    risk_level = RiskLevel.LOW
    parameters = [
        ToolParameter(
            name="pattern",
            type="string",
            description="Filename pattern to search for, e.g. '*.py' or 'config'",
        ),
        ToolParameter(
            name="path",
            type="string",
            description="Root directory to search in. Defaults to workspace root.",
            required=False,
        ),
        ToolParameter(
            name="max_results",
            type="integer",
            description="Maximum number of results to return",
            required=False,
        ),
    ]

    def __init__(self, *, workspace: Path | None, base_dir: Path) -> None:
        self.workspace = workspace
        self.base_dir = base_dir

    def run(self, **kwargs: Any) -> ToolResult:
        pattern = str(kwargs.get("pattern", "")).strip()
        if not pattern:
            return ToolResult(success=False, output="", error="Pattern cannot be empty")

        raw_path = str(kwargs.get("path") or ".")
        root = resolve_safe_path(raw_path, workspace=self.workspace, base_dir=self.base_dir)
        if not root.is_dir():
            return ToolResult(success=False, output="", error=f"Directory not found: {root}")

        max_results = int(kwargs.get("max_results") or 50)
        matches: list[str] = []
        for entry in root.rglob(pattern):
            matches.append(str(entry))
            if len(matches) >= max_results:
                break

        if not matches:
            return ToolResult(success=True, output="No files found.")
        return ToolResult(success=True, output="\n".join(matches))
