"""Tests for vision tools (describe_image, describe_screen)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from config import Settings
from core.exceptions import ToolExecutionError
from tools.builtin.vision.image_tools import DescribeImageTool, DescribeScreenTool


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(base_dir=tmp_path, data_dir=tmp_path / "data")


def test_describe_image_requires_path(settings):
    tool = DescribeImageTool(settings=settings, vision_client=MagicMock())
    result = tool.run()
    assert result.success is False
    assert "path" in (result.error or "")


def test_describe_image_returns_description(settings, tmp_path, monkeypatch):
    image_path = tmp_path / "test.png"
    image_path.write_bytes(b"fake-image-bytes")

    mock_client = MagicMock()
    mock_client.describe.return_value = "A red apple on a wooden table."

    monkeypatch.setattr(
        "tools.builtin.vision.image_tools.encode_image_to_base64",
        lambda path, max_dimension=1024: "fakebase64",
    )

    tool = DescribeImageTool(settings=settings, vision_client=mock_client)
    result = tool.run(path=str(image_path))

    assert result.success is True
    assert "apple" in result.output
    mock_client.describe.assert_called_once()


def test_describe_image_uses_custom_question(settings, tmp_path, monkeypatch):
    image_path = tmp_path / "test.png"
    image_path.write_bytes(b"fake-image-bytes")

    mock_client = MagicMock()
    mock_client.describe.return_value = "Yes, there is a cat in the image."

    monkeypatch.setattr(
        "tools.builtin.vision.image_tools.encode_image_to_base64",
        lambda path, max_dimension=1024: "fakebase64",
    )

    tool = DescribeImageTool(settings=settings, vision_client=mock_client)
    result = tool.run(path=str(image_path), question="Is there a cat?")

    assert result.success is True
    called_prompt = mock_client.describe.call_args[0][0]
    assert called_prompt == "Is there a cat?"


def test_describe_image_rejects_path_outside_workspace(settings, tmp_path) -> None:
    outside_image = tmp_path.parent / "outside.png"
    outside_image.write_bytes(b"fake-image-bytes")
    tool = DescribeImageTool(settings=settings, vision_client=MagicMock())

    with pytest.raises(ToolExecutionError, match="outside the permitted workspace"):
        tool.run(path=str(outside_image))


def test_describe_screen_takes_screenshot_and_describes(settings, tmp_path, monkeypatch):
    fake_screenshot = tmp_path / "shot.png"
    fake_screenshot.write_bytes(b"fake-screenshot-bytes")

    monkeypatch.setattr(
        "tools.builtin.vision.image_tools.take_screenshot",
        lambda output_dir, filename=None: fake_screenshot,
    )
    monkeypatch.setattr(
        "tools.builtin.vision.image_tools.encode_image_to_base64",
        lambda path, max_dimension=1024: "fakebase64",
    )

    mock_client = MagicMock()
    mock_client.describe.return_value = "Visual Studio Code is open with a Python file."

    tool = DescribeScreenTool(
        settings=settings,
        screenshot_dir=tmp_path,
        vision_client=mock_client,
    )
    result = tool.run()

    assert result.success is True
    assert "Visual Studio Code" in result.output
    assert str(fake_screenshot) in result.output
