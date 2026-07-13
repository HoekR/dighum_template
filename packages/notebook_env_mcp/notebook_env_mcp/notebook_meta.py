"""Read and optionally update notebook kernelspec metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_notebook(path: Path) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Notebook not found: {path}")
    if path.suffix != ".ipynb":
        raise ValueError(f"Not a notebook (.ipynb): {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def notebook_kernel_metadata(nb: dict[str, Any]) -> dict[str, Any]:
    metadata = nb.get("metadata") or {}
    kernelspec = metadata.get("kernelspec") or {}
    language_info = metadata.get("language_info") or {}
    return {
        "kernelspec": {
            "name": kernelspec.get("name"),
            "display_name": kernelspec.get("display_name"),
            "language": kernelspec.get("language"),
        },
        "language_info": {
            "name": language_info.get("name"),
            "version": language_info.get("version"),
        },
    }


def inspect_notebook(path: Path) -> dict[str, Any]:
    nb = read_notebook(path)
    return {
        "notebook": str(path.expanduser().resolve()),
        "metadata": notebook_kernel_metadata(nb),
    }


def update_notebook_kernel(
    path: Path,
    *,
    kernel_name: str,
    display_name: str,
    language_version: str | None = None,
) -> dict[str, Any]:
    """Update kernelspec metadata in-place. Returns before/after summary."""
    path = path.expanduser().resolve()
    nb = read_notebook(path)
    before = notebook_kernel_metadata(nb)

    metadata = nb.setdefault("metadata", {})
    kernelspec = metadata.setdefault("kernelspec", {})
    language_info = metadata.setdefault("language_info", {})

    kernelspec["name"] = kernel_name
    kernelspec["display_name"] = display_name
    kernelspec["language"] = kernelspec.get("language") or "python"

    language_info["name"] = language_info.get("name") or "python"
    if language_version:
        language_info["version"] = language_version

    path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "notebook": str(path),
        "before": before,
        "after": notebook_kernel_metadata(nb),
        "updated": True,
    }
