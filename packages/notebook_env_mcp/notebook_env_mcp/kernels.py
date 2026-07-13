"""Inspect Jupyter kernels installed on this machine."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


KERNEL_SEARCH_DIRS = (
    Path.home() / "Library" / "Jupyter" / "kernels",
    Path.home() / ".local" / "share" / "jupyter" / "kernels",
    Path.home() / ".ipython" / "kernels",
)


@dataclass(frozen=True)
class KernelSpec:
    name: str
    display_name: str
    python: Path | None
    kernel_json: Path
    alive: bool

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "python": str(self.python) if self.python else None,
            "kernel_json": str(self.kernel_json),
            "alive": self.alive,
        }


def _python_from_argv(argv: list[str]) -> Path | None:
    if not argv:
        return None
    candidate = Path(argv[0]).expanduser()
    return candidate


def _load_kernel(name: str, kernel_json: Path) -> KernelSpec | None:
    try:
        payload = json.loads(kernel_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    argv = payload.get("argv") or []
    python = _python_from_argv(argv)
    alive = bool(python and python.is_file() and os.access(python, os.X_OK))
    return KernelSpec(
        name=name,
        display_name=str(payload.get("display_name") or name),
        python=python,
        kernel_json=kernel_json,
        alive=alive,
    )


def list_kernels() -> list[dict]:
    """List registered Jupyter kernels with alive/dead status."""
    found: dict[str, KernelSpec] = {}

    for base in KERNEL_SEARCH_DIRS:
        if not base.is_dir():
            continue
        for entry in sorted(base.iterdir()):
            if not entry.is_dir():
                continue
            kernel_json = entry / "kernel.json"
            if not kernel_json.is_file():
                continue
            spec = _load_kernel(entry.name, kernel_json)
            if spec is not None:
                found[spec.name] = spec

    rows = [spec.as_dict() for spec in found.values()]
    rows.sort(key=lambda row: row["name"])
    return rows


def match_kernel_for_python(python: Path) -> dict | None:
    """Find a registered kernel whose argv[0] matches *python*."""
    python = python.expanduser().resolve()
    for row in list_kernels():
        if not row["python"]:
            continue
        if Path(row["python"]).resolve() == python:
            return row
    return None


def register_kernel_command(project_root: Path, *, display_name: str | None = None) -> str:
    """Return a shell command to register the project venv as a Jupyter kernel."""
    project_root = project_root.resolve()
    kernel_name = project_root.name.replace(" ", "-").lower()
    name = display_name or project_root.name
    return (
        f'cd "{project_root}" && '
        f'uv sync && uv run python -m ipykernel install --user '
        f'--name "{kernel_name}" --display-name "{name} (uv)"'
    )
