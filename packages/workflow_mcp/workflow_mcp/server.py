"""FastMCP server exposing PLAN.md and step guides to agents."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from workflow_mcp.context import resolve_project_root
from workflow_mcp.plan import (
    build_plan_status,
    find_current_step,
    update_plan_notes_in_plan,
    update_step_in_plan,
)
from workflow_mcp.steps import list_step_guides, read_step_guide, read_workflow_rules

_PROJECT_ROOT: Path | None = None


def _root() -> Path:
    return _PROJECT_ROOT or resolve_project_root()


mcp = FastMCP(
    "workflow",
    instructions=(
        "Cost-sensitive step-by-step workflow for DH pipeline projects. "
        "Read PLAN.md progress and plans/steps guides — one step per chat; "
        "never execute the whole plan in one session. "
        "Before retrying the same iterative concern, call get_iteration_advice."
    ),
)


@mcp.tool
def get_plan_status() -> dict[str, Any]:
    """Return parsed PLAN.md progress checklist with completion flags."""
    return build_plan_status(_root())


@mcp.tool
def get_current_step() -> dict[str, Any]:
    """Return the first incomplete step from PLAN.md (or last step if all complete)."""
    return find_current_step(_root())


@mcp.tool
def list_steps() -> list[dict[str, Any]]:
    """List step guide files under plans/steps/ (fallback: docs/steps/)."""
    return list_step_guides(_root())


@mcp.tool
def get_step_guide(step_id: str) -> dict[str, Any]:
    """Read the markdown guide for a step id (e.g. '0', '2', '3a')."""
    return read_step_guide(_root(), step_id)


@mcp.tool
def get_workflow_rules() -> dict[str, Any]:
    """Return cost-sensitive agent workflow rules from docs/wisdom/ if present."""
    return read_workflow_rules(_root())


@mcp.tool
def get_iteration_config() -> dict[str, Any]:
    """
    Return effective plans/iteration.toml (stages, concerns, interlocks, facts).

    Does not modify PLAN.md. Missing config → error payload with copy hint.
    """
    from workflow_mcp.orchestrator import load_iteration_config

    try:
        return {"success": True, "config": load_iteration_config(_root()).to_public_dict()}
    except FileNotFoundError as exc:
        return {"success": False, "error": str(exc)}


@mcp.tool
def get_iteration_advice(concern_id: str, note: str = "") -> dict[str, Any]:
    """
    Advise whether to keep iterating on a named concern (stage gates, budgets, interlocks).

    Verdicts: continue | escalate_upstream | defer | change_success_criteria | ask_human.
    Does not tick PLAN.md. Call before retrying the same concern.
    """
    from workflow_mcp.orchestrator import advise

    try:
        advice = advise(_root(), concern_id, note=note or None)
    except FileNotFoundError as exc:
        return {"success": False, "error": str(exc)}
    payload = advice.to_dict()
    payload["success"] = True
    return payload


@mcp.tool
def record_iteration_attempt(
    concern_id: str,
    outcome: str,
    note: str = "",
) -> dict[str, Any]:
    """
    Append one attempt to plans/iteration_log.jsonl (outcome e.g. no_gain, improved).

    Does not tick PLAN.md. Use after a focused pass so budgets stay accurate.
    """
    from workflow_mcp.orchestrator import record_attempt

    try:
        return record_attempt(_root(), concern_id, outcome=outcome, note=note)
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": str(exc)}


# Optional PLAN write tools (human ticks remain authoritative; prefer human edits).
# Orchestrator tools above never write PLAN.md.
    """
    Update the status of a specific step in PLAN.md (e.g. step_id='2', completed=True).
    Flips [ ] to [x] or vice versa.
    """
    root = _root()
    plan_path = root / "PLAN.md"
    
    if not plan_path.exists():
        return {"success": False, "error": "PLAN.md not found"}

    updated = update_step_in_plan(plan_path, step_id=step_id, completed=completed)
    
    if updated:
        return {"success": True, "message": f"Step {step_id} status updated to completed={completed}."}
    return {"success": False, "error": f"Step {step_id} not found in PLAN.md."}


@mcp.tool
def update_plan_notes(step_id: str, note: str) -> dict[str, Any]:
    """Append or update progress notes for a given step in PLAN.md."""
    root = _root()
    plan_path = root / "PLAN.md"

    if not plan_path.exists():
        return {"success": False, "error": "PLAN.md not found"}

    updated = update_plan_notes_in_plan(plan_path, step_id=step_id, note=note)

    if updated:
        return {"success": True, "message": f"Notes for step {step_id} updated."}
    return {"success": False, "error": f"Step {step_id} not found in PLAN.md."}

@mcp.tool
def mark_step_complete(step_id: str) -> dict[str, Any]:
    """Mark a specific step as complete (change [ ] to [x]) in PLAN.md."""
    root = _root()
    plan_path = root / "PLAN.md"
    
    if not plan_path.exists():
        return {"success": False, "error": "PLAN.md not found."}

    content = plan_path.read_text(encoding="utf-8")
    
    # Find the specific step in the table or list and update the checkbox
    import re
    pattern = rf"(\|-?\s*\[)\s*(\]\s*\|\s*{re.escape(step_id)}\b)"
    
    if re.search(pattern, content):
        new_content = re.sub(pattern, r"\1x\2", content)
        plan_path.write_text(new_content, encoding="utf-8")
        return {"success": True, "message": f"Step {step_id} marked as complete in PLAN.md."}
    
    return {"success": False, "error": f"Step {step_id} not found in PLAN.md."}


def main(argv: list[str] | None = None) -> None:
    global _PROJECT_ROOT

    parser = argparse.ArgumentParser(description="workflow MCP server (stdio)")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root containing PLAN.md, AGENTS.md, and plans/steps/",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "http"],
        default="stdio",
        help="Transport to use (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind when using network transports",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind when using network transports",
    )
    args, _unknown = parser.parse_known_args(argv)

    if args.project_root is not None:
        _PROJECT_ROOT = resolve_project_root(args.project_root)
    else:
        try:
            _PROJECT_ROOT = resolve_project_root()
        except FileNotFoundError:
            _PROJECT_ROOT = None

    # Preserve existing behavior for stdio: call with no args so subprocess usage remains unchanged.
    if getattr(args, "transport", "stdio") == "stdio":
        mcp.run()
    else:
        # forward transport and network args to FastMCP.run
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
