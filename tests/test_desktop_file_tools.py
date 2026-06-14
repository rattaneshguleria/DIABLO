"""Tests for desktop file tools."""

from pathlib import Path

from tools.builtin.desktop.file_tools import CreateFolderTool, MoveFileTool, RenameFileTool


def test_create_folder(tmp_path: Path) -> None:
    tool = CreateFolderTool(workspace=tmp_path, base_dir=tmp_path)
    result = tool.run(path="new_folder")
    assert result.success
    assert (tmp_path / "new_folder").is_dir()


def test_move_file(tmp_path: Path) -> None:
    source = tmp_path / "a.txt"
    source.write_text("hello", encoding="utf-8")
    tool = MoveFileTool(workspace=tmp_path, base_dir=tmp_path)
    result = tool.run(source="a.txt", destination="moved/a.txt")
    assert result.success
    assert not source.exists()
    assert (tmp_path / "moved" / "a.txt").read_text(encoding="utf-8") == "hello"


def test_rename_file(tmp_path: Path) -> None:
    source = tmp_path / "old.txt"
    source.write_text("data", encoding="utf-8")
    tool = RenameFileTool(workspace=tmp_path, base_dir=tmp_path)
    result = tool.run(path="old.txt", new_name="new.txt")
    assert result.success
    assert (tmp_path / "new.txt").exists()
