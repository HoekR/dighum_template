"""Walk provenance parent_sources and manifest parent links."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from data_io.manifest import DataManager


def get_provenance_chain(
    manager: DataManager,
    logical_name: str,
    *,
    max_depth: int = 10,
) -> dict[str, Any]:
    from data_io.manifest import DatasetNotFoundError, TierUnavailableError
    from data_io.provenance import read_sidecar

    chain: list[dict[str, Any]] = []
    visited: set[str] = set()
    current = logical_name
    depth = 0

    while current and current not in visited and depth < max_depth:
        visited.add(current)
        depth += 1
        try:
            dataset = manager.dataset(current)
        except DatasetNotFoundError:
            chain.append({"logical_name": current, "error": "not in manifest"})
            break

        entry: dict[str, Any] = {
            "logical_name": current,
            "tier": dataset.tier,
            "phase": dataset.phase,
            "description": dataset.description,
            "manifest_parent": dataset.parent,
        }

        try:
            path = manager.resolve(current)
            entry["resolved_path"] = str(path)
            entry["exists"] = path.exists()
            if path.exists():
                sidecar = read_sidecar(path, phase=dataset.phase)
                entry["sidecar"] = sidecar
                parents: list[str] = []
                if sidecar and sidecar.get("parent_sources"):
                    raw = sidecar["parent_sources"]
                    if isinstance(raw, list):
                        parents = [str(p) for p in raw]
                elif dataset.parent:
                    parents = [dataset.parent]
                entry["parent_sources"] = parents
                current = parents[0] if parents else ""
            else:
                entry["parent_sources"] = [dataset.parent] if dataset.parent else []
                current = dataset.parent or ""
        except TierUnavailableError as exc:
            entry["error"] = str(exc)
            entry["parent_sources"] = [dataset.parent] if dataset.parent else []
            current = dataset.parent or ""

        chain.append(entry)

    return {
        "logical_name": logical_name,
        "chain": chain,
        "truncated": depth >= max_depth,
    }
