"""Regression tests for filesystem safety boundaries."""

from pathlib import Path

import pytest

from core.exceptions import ToolExecutionError
from tools.safety import resolve_safe_path


def test_resolve_safe_path_allows_paths_inside_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    resolved = resolve_safe_path(
        "nested/file.txt",
        workspace=workspace,
        base_dir=tmp_path,
    )

    assert resolved == (workspace / "nested" / "file.txt").resolve()


@pytest.mark.parametrize("requested_path", ["../outside.txt", "{outside}"])
def test_resolve_safe_path_rejects_workspace_escape(
    tmp_path: Path,
    requested_path: str,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("private", encoding="utf-8")
    path = requested_path.format(outside=outside)

    with pytest.raises(ToolExecutionError, match="outside the permitted workspace"):
        resolve_safe_path(path, workspace=workspace, base_dir=tmp_path)


def test_resolve_safe_path_rejects_symlink_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    outside_dir = tmp_path / "outside"
    workspace.mkdir()
    outside_dir.mkdir()
    (outside_dir / "private.txt").write_text("private", encoding="utf-8")
    link = workspace / "linked"

    try:
        link.symlink_to(outside_dir, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Creating directory symlinks is unavailable: {exc}")

    with pytest.raises(ToolExecutionError, match="outside the permitted workspace"):
        resolve_safe_path("linked/private.txt", workspace=workspace, base_dir=tmp_path)
