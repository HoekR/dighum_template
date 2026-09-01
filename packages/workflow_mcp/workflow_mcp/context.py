"""Resolve project root for PLAN.md + docs/steps workflow."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_project_root(explicit: Path | str | None = None) -> Path:
    if explicit is not None:
        root = Path(explicit).expanduser().resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"Project root is not a directory: {root}")
        return root

    env_root = os.environ.get("WORKFLOW_PROJECT_ROOT")
    if env_root:
        root = Path(env_root).expanduser().resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"WORKFLOW_PROJECT_ROOT is not a directory: {root}")
        return root

    return _find_project_root(Path.cwd())


def _find_project_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "PLAN.md").is_file() and (candidate / "AGENTS.md").is_file():
            return candidate.resolve()
    raise FileNotFoundError(
        "Could not find project root (need PLAN.md and AGENTS.md in same directory)"
    )
