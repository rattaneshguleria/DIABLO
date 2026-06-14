"""Screenshot utilities."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from core.exceptions import ToolExecutionError

logger = logging.getLogger("diablo.system.screen")


def take_screenshot(output_dir: Path, *, filename: str | None = None) -> Path:
    """Capture the primary screen and save a PNG file."""
    try:
        import pyautogui
    except ImportError as exc:
        raise ToolExecutionError(
            "pyautogui is required for screenshots",
            details="pip install pyautogui",
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    if filename:
        target = output_dir / filename
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        target = output_dir / f"screenshot_{stamp}.png"

    if target.suffix.lower() != ".png":
        target = target.with_suffix(".png")

    try:
        image = pyautogui.screenshot()
        image.save(target)
    except Exception as exc:  # noqa: BLE001 - pyautogui guard
        raise ToolExecutionError("Failed to capture screenshot", details=str(exc)) from exc

    logger.info("Screenshot saved to %s", target)
    return target
