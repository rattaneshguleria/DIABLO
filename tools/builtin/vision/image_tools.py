"""Vision tools: describe images and screen contents using a multimodal model."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from config import Settings
from llm.vision import VisionClient, build_vision_client
from system.image import encode_image_to_base64
from system.screen import take_screenshot
from tools.base import RiskLevel, Tool, ToolParameter, ToolResult

DEFAULT_IMAGE_PROMPT = "Describe this image in clear, useful detail."
DEFAULT_SCREEN_PROMPT = (
    "Describe what is currently visible on this screen: open windows, "
    "applications, visible text, and anything notable."
)


class DescribeImageTool(Tool):
    name = "describe_image"
    description = (
        "Look at an image file on disk and describe its contents, or answer a "
        "specific question about it."
    )
    risk_level = RiskLevel.LOW
    parameters = [
        ToolParameter(
            name="path",
            type="string",
            description="Path to the image file (png, jpg, jpeg, webp, bmp, gif)",
            required=True,
        ),
        ToolParameter(
            name="question",
            type="string",
            description="Optional specific question to ask about the image",
            required=False,
        ),
    ]

    def __init__(self, *, settings: Settings, vision_client: VisionClient | None = None) -> None:
        self.settings = settings
        self.vision_client = vision_client or build_vision_client(settings)

    def run(self, **kwargs: Any) -> ToolResult:
        raw_path = kwargs.get("path")
        if not raw_path:
            return ToolResult(success=False, output="", error="'path' is required")

        path = Path(str(raw_path)).expanduser()
        if not path.is_absolute():
            path = self.settings.base_dir / path

        question = kwargs.get("question") or DEFAULT_IMAGE_PROMPT

        image_b64 = encode_image_to_base64(
            path, max_dimension=self.settings.vision_max_image_dimension
        )
        description = self.vision_client.describe(str(question), [image_b64])
        return ToolResult(success=True, output=description)


class DescribeScreenTool(Tool):
    name = "describe_screen"
    description = (
        "Take a screenshot of the current screen and describe what is visible, "
        "or answer a specific question about what's on screen."
    )
    risk_level = RiskLevel.LOW
    parameters = [
        ToolParameter(
            name="question",
            type="string",
            description="Optional specific question to ask about the screen",
            required=False,
        ),
    ]

    def __init__(
        self,
        *,
        settings: Settings,
        screenshot_dir: Path,
        vision_client: VisionClient | None = None,
    ) -> None:
        self.settings = settings
        self.screenshot_dir = screenshot_dir
        self.vision_client = vision_client or build_vision_client(settings)

    def run(self, **kwargs: Any) -> ToolResult:
        question = kwargs.get("question") or DEFAULT_SCREEN_PROMPT
        screenshot_path = take_screenshot(self.screenshot_dir)
        image_b64 = encode_image_to_base64(
            screenshot_path, max_dimension=self.settings.vision_max_image_dimension
        )
        description = self.vision_client.describe(str(question), [image_b64])
        return ToolResult(
            success=True,
            output=f"{description}\n\n(Screenshot saved to {screenshot_path})",
        )
