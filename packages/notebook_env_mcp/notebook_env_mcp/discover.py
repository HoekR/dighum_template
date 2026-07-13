"""Discover project roots, virtualenvs, and pyproject.toml files."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


VENV_DIR_NAMES = (".venv", "venv")
PROJECT_MARKERS = ("pyproject.toml", "uv.lock")


@dataclass(frozen=True)
class VirtualEnv:
    path: Path
    python: Path
    project_root: Path | None
    project_name: str | None
    alive: bool

    def as_dict(self) -> dict:
        return {
            "venv_path": str(self.path),
            "python": str(self.python),
            "project_root": str(self.project_root) if self.project_root else None,
            "project_name": self.project_name,
            "alive": self.alive,
        }


def resolve_scan_root(explicit: Path | str | None = None) -> Path:
    if explicit is not None:
        root = Path(explicit).expanduser().resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"Scan root is not a directory: {root}")
        return root

    env_root = os.environ.get("NOTEBOOK_ENV_SCAN_ROOT")
    if env_root:
        root = Path(env_root).expanduser().resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"NOTEBOOK_ENV_SCAN_ROOT is not a directory: {root}")
        return root

    return Path.cwd().resolve()


def find_project_root(start: Path) -> Path | None:
    """Walk upward from *start* until pyproject.toml or uv.lock is found."""
    current = start.resolve()
    if current.is_file():
        current = current.parent

    for directory in (current, *current.parents):
        if any((directory / marker).is_file() for marker in PROJECT_MARKERS):
            return directory
    return None


def project_name(project_root: Path | None) -> str | None:
    if project_root is None:
        return None
    return project_root.name


def venv_candidates(project_root: Path) -> list[Path]:
    found: list[Path] = []
    for name in VENV_DIR_NAMES:
        candidate = project_root / name
        if candidate.is_dir():
            found.append(candidate)
    return found


def python_for_venv(venv_path: Path) -> Path:
    return venv_path / "bin" / "python"


def build_venv_record(venv_path: Path) -> VirtualEnv:
    venv_path = venv_path.resolve()
    python = python_for_venv(venv_path)
    root = find_project_root(venv_path)
    return VirtualEnv(
        path=venv_path,
        python=python,
        project_root=root,
        project_name=project_name(root),
        alive=python.is_file() and os.access(python, os.X_OK),
    )


def recommend_for_path(target: Path) -> dict:
    """Best-effort venv recommendation for a notebook or script path."""
    target = target.expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(f"Path does not exist: {target}")

    project_root = find_project_root(target)
    candidates: list[VirtualEnv] = []

    if project_root is not None:
        for venv_path in venv_candidates(project_root):
            candidates.append(build_venv_record(venv_path))

    # Also check parent dirs between target and project root for nested layouts.
    if target.is_file():
        walk = target.parent
    else:
        walk = target

    seen: set[Path] = {c.path for c in candidates}
    for directory in walk.parents:
        if project_root is not None and directory == project_root.parent:
            break
        for name in VENV_DIR_NAMES:
            venv_path = directory / name
            if venv_path.is_dir() and venv_path not in seen:
                seen.add(venv_path)
                candidates.append(build_venv_record(venv_path))

    alive = [c for c in candidates if c.alive]
    preferred = alive[0] if alive else (candidates[0] if candidates else None)

    return {
        "target": str(target),
        "project_root": str(project_root) if project_root else None,
        "project_name": project_name(project_root),
        "recommended": preferred.as_dict() if preferred else None,
        "candidates": [c.as_dict() for c in candidates],
    }


def scan_venvs(scan_root: Path, *, max_depth: int = 6) -> list[dict]:
    """Find .venv / venv directories under *scan_root* (bounded depth)."""
    scan_root = scan_root.resolve()
    if not scan_root.is_dir():
        raise FileNotFoundError(f"Scan root is not a directory: {scan_root}")

    results: list[dict] = []
    seen: set[Path] = set()
    root_depth = len(scan_root.parts)

    for dirpath, dirnames, _filenames in os.walk(scan_root):
        current = Path(dirpath)
        depth = len(current.parts) - root_depth
        if depth > max_depth:
            dirnames.clear()
            continue

        # Prune heavy or irrelevant trees.
        dirnames[:] = [
            name
            for name in dirnames
            if name not in {".git", "node_modules", "__pycache__", ".tox", "dist", "build"}
            and not name.startswith(".")
            or name in VENV_DIR_NAMES
        ]

        for name in list(dirnames):
            if name not in VENV_DIR_NAMES:
                continue
            venv_path = current / name
            if venv_path in seen:
                continue
            seen.add(venv_path)
            results.append(build_venv_record(venv_path).as_dict())

    results.sort(key=lambda row: (row["project_name"] or "", row["venv_path"]))
    return results
