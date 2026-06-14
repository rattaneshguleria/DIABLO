"""Known application paths and process management on Windows."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

import psutil

from core.exceptions import ToolExecutionError

logger = logging.getLogger("diablo.system.apps")

KNOWN_APPS: dict[str, list[str]] = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
    "vscode": [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft VS Code\Code.exe"),
    ],
    "spotify": [
        os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
    ],
    "notepad": ["notepad.exe"],
    "explorer": ["explorer.exe"],
}


def resolve_app_executable(app_name: str) -> str:
    """Resolve a friendly app name or path to an executable."""
    cleaned = app_name.strip().strip('"')
    if not cleaned:
        raise ToolExecutionError("Application name cannot be empty")

    candidate = Path(cleaned).expanduser()
    if candidate.exists():
        return str(candidate)

    key = cleaned.lower().replace(" ", "")
    aliases = {
        "googlechrome": "chrome",
        "visualstudiocode": "vscode",
        "code": "vscode",
    }
    lookup = aliases.get(key, key)

    if lookup in KNOWN_APPS:
        for path in KNOWN_APPS[lookup]:
            if Path(path).exists():
                return path
        # Fall back to bare name for PATH resolution (e.g. notepad)
        return Path(KNOWN_APPS[lookup][0]).name

    if lookup.endswith(".exe"):
        return lookup

    return cleaned


def launch_application(app_name: str, *, arguments: str = "") -> str:
    """Launch an application by friendly name or full path."""
    executable = resolve_app_executable(app_name)
    command = [executable]
    if arguments.strip():
        command.extend(arguments.split())

    try:
        subprocess.Popen(command)  # noqa: S603 - user-directed desktop control
    except FileNotFoundError as exc:
        raise ToolExecutionError(
            f"Application not found: {app_name}",
            details=str(exc),
        ) from exc
    except OSError as exc:
        raise ToolExecutionError(
            f"Failed to launch application: {app_name}",
            details=str(exc),
        ) from exc

    logger.info("Launched application: %s", executable)
    return executable


def list_running_applications(*, limit: int = 30) -> list[str]:
    """Return a list of running process names."""
    names: list[str] = []
    seen: set[str] = set()

    for process in psutil.process_iter(["name"]):
        name = process.info.get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
        if len(names) >= limit:
            break

    return sorted(names, key=str.lower)


def close_application(process_name: str, *, force: bool = False) -> int:
    """Close processes matching the given name. Returns number terminated."""
    target = process_name.strip().lower()
    if not target:
        raise ToolExecutionError("Process name cannot be empty")
    if not target.endswith(".exe"):
        target_key = target
    else:
        target_key = target[:-4]

    terminated = 0
    for process in psutil.process_iter(["name", "pid"]):
        name = (process.info.get("name") or "").lower()
        if not name:
            continue
        name_key = name[:-4] if name.endswith(".exe") else name
        if name_key != target_key and name != target:
            continue

        try:
            if force:
                process.kill()
            else:
                process.terminate()
            process.wait(timeout=3)
            terminated += 1
        except (psutil.Error, OSError) as exc:
            logger.warning("Failed to close pid=%s: %s", process.info.get("pid"), exc)

    if terminated == 0:
        raise ToolExecutionError(f"No running process found matching '{process_name}'")

    logger.info("Closed %d process(es) for %s", terminated, process_name)
    return terminated
