"""Image encoding utilities for vision tools."""

from __future__ import annotations

import base64
import io
import logging
from pathlib import Path

from core.exceptions import ToolExecutionError

logger = logging.getLogger("diablo.system.image")

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


def encode_image_to_base64(path: Path, *, max_dimension: int = 1024) -> str:
    """Load an image, resize it if needed, and return base64-encoded JPEG bytes."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise ToolExecutionError(
            "Pillow is required for image processing",
            details="pip install Pillow",
        ) from exc

    if not path.exists():
        raise ToolExecutionError(f"Image not found: {path}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ToolExecutionError(
            f"Unsupported image type: {path.suffix}",
            details=f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    try:
        with Image.open(path) as image:
            image = image.convert("RGB")
            width, height = image.size
            largest_side = max(width, height)
            if largest_side > max_dimension:
                scale = max_dimension / largest_side
                new_size = (int(width * scale), int(height * scale))
                image = image.resize(new_size)

            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=85)
            encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as exc:  # noqa: BLE001 - Pillow guard
        raise ToolExecutionError("Failed to process image", details=str(exc)) from exc

    logger.debug("Encoded image %s (%d bytes base64)", path, len(encoded))
    return encoded
