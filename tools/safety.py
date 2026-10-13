"""Safety checks for tool execution."""

from __future__ import annotations

import os
import re
from pathlib import Path

from core.exceptions import ToolExecutionError
from tools.base import RiskLevel

BLOCKED_PATH_PARTS = {
    "system32",
    "syswow64",
    "windows",
    "program files",
    "programdata",
}

DANGEROUS_COMMAND_PATTERNS = [
    re.compile(r"\brm\b", re.IGNORECASE),
  re.compile(r"\bdel\b", re.IGNORECASE),
  re.compile(r"\brmdir\b", re.IGNORECASE),
  re.compile(r"\bformat\b", re.IGNORECASE),
  re.compile(r"\bshutdown\b", re.IGNORECASE),
  re.compile(r"\brestart\b", re.IGNORECASE),
  re.compile(r"\breg\s", re.IGNORECASE),
  re.compile(r"\bmkfs\b", re.IGNORECASE),
  re.compile(r">\s*/", re.IGNORECASE),
]


def parse_allowed_prefixes(raw: str) -> list[str]:
    """Parse comma-separated command prefixes."""
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def is_command_allowed(command: str, allowed_prefixes: list[str]) -> bool:
    """Return True if the command starts with an allowed prefix."""
    stripped = command.strip()
    if not stripped:
        return False

    first_token = stripped.split()[0].lower()
    if first_token in allowed_prefixes:
        return True

    for pattern in DANGEROUS_COMMAND_PATTERNS:
        if pattern.search(stripped):
            return False

    return any(stripped.lower().startswith(prefix) for prefix in allowed_prefixes)


def resolve_safe_path(
    path: str,
    *,
    workspace: Path | None,
    base_dir: Path,
) -> Path:
    """Resolve a path and ensure it remains inside the permitted workspace.

    Resolving before the containment check makes paths that traverse through an
    existing symlink subject to the same boundary as ordinary ``..`` traversal.
    """
    if not path or not path.strip():
        raise ToolExecutionError("Path cannot be empty")

    root = (workspace or base_dir).expanduser().resolve()
    candidate = Path(path.strip()).expanduser()
    if not candidate.is_absolute():
        candidate = (root / candidate).resolve()
    else:
        candidate = candidate.resolve()

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ToolExecutionError(
            "Path is outside the permitted workspace",
            details=f"Workspace: {root}; requested path: {candidate}",
        ) from exc

    lowered = str(candidate).lower()
    for part in BLOCKED_PATH_PARTS:
        if f"\\{part}\\" in lowered or lowered.endswith(f"\\{part}"):
            raise ToolExecutionError(
                "Access to system directories is blocked",
                details=str(candidate),
            )

    return candidate


def validate_read_size(file_path: Path, max_bytes: int) -> None:
    """Ensure a file is not too large to read."""
    size = file_path.stat().st_size
    if size > max_bytes:
        raise ToolExecutionError(
            f"File too large to read ({size} bytes)",
            details=f"Maximum allowed: {max_bytes} bytes",
        )


def default_confirmation_message(tool_name: str, arguments: dict) -> str:
    """Build a human-readable confirmation prompt."""
    args_text = ", ".join(f"{key}={value!r}" for key, value in arguments.items())
    return f"Diablo wants to run '{tool_name}' with arguments: {args_text}. Allow? [y/N]: "
