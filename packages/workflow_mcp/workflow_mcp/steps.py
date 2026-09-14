"""Discover and read plans/steps guides (fallback: docs/steps)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

STEP_FILE = re.compile(r"^STEP(\d+[a-z]?)[-_]", re.IGNORECASE)
MAX_GUIDE_BYTES = 48_000


def _step_id_from_filename(name: str) -> str | None:
    match = STEP_FILE.match(name)
    return match.group(1).lower() if match else None


def _steps_dirs(project_root: Path) -> list[Path]:
    """Prefer plans/steps/; fall back to docs/steps/ for older derivatives."""
    preferred = project_root / "plans" / "steps"
    legacy = project_root / "docs" / "steps"
    dirs: list[Path] = []
    if preferred.is_dir():
        dirs.append(preferred)
    if legacy.is_dir() and legacy.resolve() != preferred.resolve():
        dirs.append(legacy)
    return dirs


def list_step_guides(project_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for steps_dir in _steps_dirs(project_root):
        for path in sorted(steps_dir.glob("STEP*.md")):
            step_id = _step_id_from_filename(path.name)
            key = step_id or path.name
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "step_id": step_id,
                    "filename": path.name,
                    "path": str(path.relative_to(project_root)),
                }
            )
    return rows


def _resolve_guide_path(project_root: Path, step_id: str) -> Path | None:
    normalized = step_id.strip().lower()

    from workflow_mcp.plan import load_plan_steps

    for step in load_plan_steps(project_root):
        if step.step_id == normalized:
            candidate = project_root / step.guide_path
            if candidate.is_file():
                return candidate

    for steps_dir in _steps_dirs(project_root):
        for path in sorted(steps_dir.glob("STEP*.md")):
            if _step_id_from_filename(path.name) == normalized:
                return path

    return None


def read_step_guide(project_root: Path, step_id: str) -> dict[str, Any]:
    guide_path = _resolve_guide_path(project_root, step_id)
    if guide_path is None:
        return {
            "step_id": step_id.strip().lower(),
            "found": False,
            "error": (
                f"No guide found for step {step_id!r} under "
                "plans/steps/ (or docs/steps/)"
            ),
            "available_steps": list_step_guides(project_root),
        }

    raw = guide_path.read_bytes()
    truncated = len(raw) > MAX_GUIDE_BYTES
    content = raw[:MAX_GUIDE_BYTES].decode("utf-8", errors="replace")
    if truncated:
        content += "\n\n<!-- truncated: guide exceeded MCP byte cap -->"

    return {
        "step_id": step_id.strip().lower(),
        "found": True,
        "path": str(guide_path.relative_to(project_root)),
        "truncated": truncated,
        "content": content,
    }


def read_workflow_rules(project_root: Path) -> dict[str, Any]:
    candidates = [
        project_root / "docs" / "wisdom" / "cost-sensitive-agent-workflow.md",
        project_root / "docs" / "wisdom" / "topics" / "cost-sensitive-agent-workflow.md",
    ]
    for path in candidates:
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            return {
                "found": True,
                "path": str(path.relative_to(project_root)),
                "content": text,
            }

    return {
        "found": False,
        "path": None,
        "content": (
            "Cost-sensitive workflow (inline fallback):\n"
            "- One step per chat; do not execute the whole plan.\n"
            "- Read plans/steps/STEP*.md for the active step only "
            "(legacy: docs/steps/).\n"
            "- User runs terminal by default; agents edit files and give commands.\n"
            "- Tick progress in PLAN.md; use get_plan_status() at session start.\n"
        ),
    }
