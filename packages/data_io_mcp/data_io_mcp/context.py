"""Resolve project root and construct a fresh DataManager."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data_io.manifest import DataManager


def resolve_project_root(explicit: Path | str | None = None) -> Path:
    if explicit is not None:
        root = Path(explicit).expanduser().resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"Project root is not a directory: {root}")
        return root

    env_root = os.environ.get("DATA_IO_PROJECT_ROOT")
    if env_root:
        root = Path(env_root).expanduser().resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"DATA_IO_PROJECT_ROOT is not a directory: {root}")
        return root

    from data_io.manifest import find_manifest_path

    return find_manifest_path(Path.cwd()).parent


def activate_project(project_root: Path) -> DataManager:
    """Put project on sys.path, chdir, and return a new DataManager."""
    from data_io.manifest import DataManager

    root = project_root.resolve()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    os.chdir(root)

    import data_io.manifest as manifest_module

    manifest_module._default_manager = None  # noqa: SLF001
    return DataManager()
