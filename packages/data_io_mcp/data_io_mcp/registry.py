"""Manifest registry helpers shared by MCP tools."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from data_io.manifest import DataManager


def build_manifest_report(manager: DataManager) -> dict[str, Any]:
    from data_io.manifest import TierUnavailableError

    tier_rows: list[dict[str, Any]] = []
    for name, tier in sorted(manager.tiers.items()):
        tier_rows.append(
            {
                "name": name,
                "root": str(tier.root),
                "mount_check": str(tier.mount_check) if tier.mount_check else None,
                "available": manager.tier_available(name),
            }
        )

    dataset_rows: list[dict[str, Any]] = []
    failures = 0
    for name, dataset in sorted(manager.datasets.items()):
        tier_mounted = manager.tier_available(dataset.tier)
        try:
            resolved = manager.resolve(name)
            path_str = str(resolved)
            ok = tier_mounted and resolved.exists()
        except TierUnavailableError as exc:
            path_str = f"<tier {dataset.tier!r} unavailable>"
            ok = False
            error = str(exc)
        else:
            error = None

        if not ok:
            failures += 1
        row: dict[str, Any] = {
            "name": name,
            "tier": dataset.tier,
            "phase": dataset.phase,
            "path": path_str,
            "description": dataset.description,
            "parent": dataset.parent,
            "available": ok,
        }
        if error:
            row["error"] = error
        dataset_rows.append(row)

    return {
        "manifest_path": str(manager.manifest_path),
        "tiers": tier_rows,
        "datasets": dataset_rows,
        "failure_count": failures,
        "healthy": failures == 0,
    }


def list_datasets(
    manager: DataManager,
    *,
    prefix: str | None = None,
) -> list[dict[str, Any]]:
    from data_io.manifest import TierUnavailableError

    rows: list[dict[str, Any]] = []
    for name, dataset in sorted(manager.datasets.items()):
        if prefix and not name.startswith(prefix):
            continue
        tier_mounted = manager.tier_available(dataset.tier)
        try:
            resolved = manager.resolve(name)
            exists = tier_mounted and resolved.exists()
            path_str = str(resolved)
        except TierUnavailableError:
            exists = False
            path_str = f"<tier {dataset.tier!r} unavailable>"
        rows.append(
            {
                "logical_name": name,
                "tier": dataset.tier,
                "phase": dataset.phase,
                "description": dataset.description,
                "parent": dataset.parent,
                "resolved_path": path_str,
                "exists": exists,
                "tier_available": tier_mounted,
            }
        )
    return rows


def resolve_dataset_info(manager: DataManager, logical_name: str) -> dict[str, Any]:
    from data_io.manifest import TierUnavailableError

    dataset = manager.dataset(logical_name)
    tier_mounted = manager.tier_available(dataset.tier)
    try:
        resolved = manager.resolve(logical_name)
        return {
            "logical_name": logical_name,
            "tier": dataset.tier,
            "phase": dataset.phase,
            "description": dataset.description,
            "parent": dataset.parent,
            "resolved_path": str(resolved),
            "exists": tier_mounted and resolved.exists(),
            "tier_available": tier_mounted,
        }
    except TierUnavailableError as exc:
        return {
            "logical_name": logical_name,
            "tier": dataset.tier,
            "phase": dataset.phase,
            "description": dataset.description,
            "parent": dataset.parent,
            "resolved_path": None,
            "exists": False,
            "tier_available": False,
            "error": str(exc),
        }
