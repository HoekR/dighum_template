"""FastMCP server for notebook venv / kernel discovery."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from notebook_env_mcp.discover import recommend_for_path, resolve_scan_root, scan_venvs
from notebook_env_mcp.kernels import list_kernels, match_kernel_for_python, register_kernel_command
from notebook_env_mcp.notebook_meta import inspect_notebook, update_notebook_kernel

_SCAN_ROOT: Path | None = None

mcp = FastMCP(
    "notebook-env",
    instructions=(
        "Discover per-project .venv environments and Jupyter kernels for notebooks. "
        "Use recommend_env / inspect_notebook when a notebook kernel is missing or points at a dead conda path."
    ),
)


def _scan_root() -> Path:
    return _SCAN_ROOT or resolve_scan_root()


@mcp.tool
def list_project_venvs(max_depth: int = 6) -> list[dict[str, Any]]:
    """Scan the workspace (or scan root) for .venv / venv directories with alive/dead status."""
    return scan_venvs(_scan_root(), max_depth=max_depth)


@mcp.tool
def list_jupyter_kernels() -> list[dict[str, Any]]:
    """List registered Jupyter kernels and whether their Python binary still exists."""
    return list_kernels()


@mcp.tool
def recommend_env(path: str) -> dict[str, Any]:
    """Recommend a project .venv for a notebook or file by walking up to pyproject.toml."""
    recommendation = recommend_for_path(Path(path))
    recommended = recommendation.get("recommended")
    if recommended and recommended.get("python"):
        kernel = match_kernel_for_python(Path(recommended["python"]))
        recommendation["matching_kernel"] = kernel
        if kernel is None and recommendation.get("project_root"):
            recommendation["register_kernel_command"] = register_kernel_command(
                Path(recommendation["project_root"])
            )
    else:
        recommendation["matching_kernel"] = None
    return recommendation


@mcp.tool
def inspect_notebook_env(notebook_path: str) -> dict[str, Any]:
    """Inspect notebook kernelspec metadata and recommend the correct project venv."""
    path = Path(notebook_path)
    info = inspect_notebook(path)
    recommendation = recommend_for_path(path)
    info["recommendation"] = recommendation

    kernels = list_kernels()
    info["dead_kernels"] = [row for row in kernels if not row["alive"]]
    info["alive_kernels"] = [row for row in kernels if row["alive"]]

    recommended = recommendation.get("recommended")
    if recommended and recommended.get("python"):
        info["matching_kernel"] = match_kernel_for_python(Path(recommended["python"]))
        if info["matching_kernel"] is None and recommendation.get("project_root"):
            info["register_kernel_command"] = register_kernel_command(
                Path(recommendation["project_root"])
            )
    else:
        info["matching_kernel"] = None

    display = (info.get("metadata") or {}).get("kernelspec", {}).get("display_name")
    if display and info.get("matching_kernel"):
        info["display_name_matches_kernel"] = display == info["matching_kernel"]["display_name"]
    else:
        info["display_name_matches_kernel"] = None

    return info


@mcp.tool
def fix_notebook_kernel(notebook_path: str, execute: bool = False) -> dict[str, Any]:
    """Update notebook kernelspec to the recommended registered kernel (dry-run by default)."""
    path = Path(notebook_path)
    recommendation = recommend_for_path(path)
    recommended = recommendation.get("recommended")
    if not recommended or not recommended.get("alive"):
        return {
            "updated": False,
            "error": "No alive .venv found for this notebook",
            "recommendation": recommendation,
        }

    python = Path(recommended["python"])
    kernel = match_kernel_for_python(python)
    if kernel is None:
        project_root = recommendation.get("project_root")
        return {
            "updated": False,
            "error": "No Jupyter kernel registered for the recommended .venv",
            "register_kernel_command": register_kernel_command(Path(project_root))
            if project_root
            else None,
            "recommendation": recommendation,
        }

    if not execute:
        return {
            "updated": False,
            "dry_run": True,
            "would_set": {
                "kernel_name": kernel["name"],
                "display_name": kernel["display_name"],
            },
            "recommendation": recommendation,
        }

    version = _python_version(python)
    return update_notebook_kernel(
        path,
        kernel_name=kernel["name"],
        display_name=kernel["display_name"],
        language_version=version,
    )


def _python_version(python: Path) -> str | None:
    try:
        out = subprocess.check_output(
            [str(python), "-c", "import platform; print(platform.python_version())"],
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    return out.strip() or None


def main(argv: list[str] | None = None) -> None:
    global _SCAN_ROOT

    parser = argparse.ArgumentParser(description="notebook-env MCP server (stdio)")
    parser.add_argument(
        "--scan-root",
        type=Path,
        default=None,
        help="Root directory to scan for .venv trees (default: cwd or NOTEBOOK_ENV_SCAN_ROOT)",
    )
    args, _unknown = parser.parse_known_args(argv)

    if args.scan_root is not None:
        _SCAN_ROOT = resolve_scan_root(args.scan_root)
    else:
        try:
            _SCAN_ROOT = resolve_scan_root()
        except FileNotFoundError:
            _SCAN_ROOT = Path.cwd().resolve()

    mcp.run()


if __name__ == "__main__":
    main(sys.argv[1:])
