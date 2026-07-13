"""FastMCP server exposing data_io manifest registry to agents."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from data_io_mcp.context import activate_project, resolve_project_root
from data_io_mcp.preview import preview_dataset as build_preview
from data_io_mcp.provenance_chain import get_provenance_chain
from data_io_mcp.registry import build_manifest_report, list_datasets as build_list, resolve_dataset_info
from data_io_mcp.suggest import suggest_manifest_entry as build_suggest

_PROJECT_ROOT: Path | None = None


def _manager():
    root = _PROJECT_ROOT or resolve_project_root()
    return activate_project(root)


mcp = FastMCP(
    "data-io",
    instructions=(
        "Manifest-backed data registry for DH pipeline projects. "
        "Use logical dataset names from data_manifest.toml — never hardcode filesystem paths."
    ),
)


@mcp.tool
def check_manifest() -> dict[str, Any]:
    """Verify tier mounts and list all declared datasets with availability status."""
    return build_manifest_report(_manager())


@mcp.tool
def list_datasets(prefix: str | None = None) -> list[dict[str, Any]]:
    """List manifest datasets, optionally filtered by logical_name prefix."""
    return build_list(_manager(), prefix=prefix or None)


@mcp.tool
def resolve_dataset(logical_name: str) -> dict[str, Any]:
    """Resolve a logical dataset name to its filesystem path and availability."""
    return resolve_dataset_info(_manager(), logical_name)


@mcp.tool
def preview_dataset(logical_name: str, limit: int = 10) -> dict[str, Any]:
    """Preview schema and sample rows for a dataset (capped; never returns full wide tables)."""
    return build_preview(_manager(), logical_name, limit=limit)


@mcp.tool
def get_provenance(logical_name: str) -> dict[str, Any]:
    """Read provenance sidecar and walk parent_sources / manifest parent chain."""
    return get_provenance_chain(_manager(), logical_name)


@mcp.tool
def suggest_manifest_entry(
    logical_name: str,
    path: str,
    tier: str = "scratch",
    phase: str = "semi",
    description: str = "",
    parent: str | None = None,
) -> str:
    """Draft a [datasets.*] block for human review before merging into data_manifest.toml."""
    return build_suggest(
        logical_name,
        path,
        tier=tier,
        phase=phase,
        description=description,
        parent=parent,
    )


def main(argv: list[str] | None = None) -> None:
    global _PROJECT_ROOT

    parser = argparse.ArgumentParser(description="data_io MCP server (stdio)")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Python project root containing data_manifest.toml and data_io/",
    )
    args, _unknown = parser.parse_known_args(argv)

    if args.project_root is not None:
        _PROJECT_ROOT = resolve_project_root(args.project_root)
    else:
        try:
            _PROJECT_ROOT = resolve_project_root()
        except FileNotFoundError:
            _PROJECT_ROOT = None

    if _PROJECT_ROOT is not None:
        activate_project(_PROJECT_ROOT)

    mcp.run()


if __name__ == "__main__":
    main()
