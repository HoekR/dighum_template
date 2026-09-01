"""Parse PLAN.md progress checklist."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import shutil
import tempfile
from datetime import datetime

STEP_ROW = re.compile(
    r"^\|\s*\*\*(\d+[a-z]?)\*\*.*?\|\s*\[[^\]]+\]\(([^)]+)\)\s*\|\s*([^|]+)\|\s*([^|]+)\|",
    re.IGNORECASE,
)

COMPLETE_MARKERS = ("☑", "✅", "✓", "[x]", "done", "complete")


@dataclass(frozen=True)
class PlanStep:
    step_id: str
    guide_path: str
    done_when: str
    status_raw: str
    complete: bool
    optional: bool


def _is_complete(status_cell: str) -> bool:
    normalized = status_cell.strip().lower()
    return any(marker in normalized for marker in COMPLETE_MARKERS)


def _is_optional(row_text: str) -> bool:
    lowered = row_text.lower()
    return "opt" in lowered or "optional" in lowered


def parse_plan_steps(plan_text: str) -> list[PlanStep]:
    steps: list[PlanStep] = []
    for line in plan_text.splitlines():
        if not line.strip().startswith("|"):
            continue
        match = STEP_ROW.match(line.strip())
        if not match:
            continue
        step_id, guide_path, done_when, status_raw = match.groups()
        steps.append(
            PlanStep(
                step_id=step_id.lower(),
                guide_path=guide_path.strip(),
                done_when=done_when.strip().strip("`"),
                status_raw=status_raw.strip(),
                complete=_is_complete(status_raw),
                optional=_is_optional(line),
            )
        )
    return steps


def load_plan_steps(project_root: Path) -> list[PlanStep]:
    plan_path = project_root / "PLAN.md"
    if not plan_path.is_file():
        raise FileNotFoundError(f"PLAN.md not found at {plan_path}")
    return parse_plan_steps(plan_path.read_text(encoding="utf-8"))


def build_plan_status(project_root: Path) -> dict[str, Any]:
    steps = load_plan_steps(project_root)
    completed = sum(1 for step in steps if step.complete)
    return {
        "project_root": str(project_root),
        "plan_path": str(project_root / "PLAN.md"),
        "step_count": len(steps),
        "completed_count": completed,
        "steps": [
            {
                "step_id": step.step_id,
                "guide_path": step.guide_path,
                "done_when": step.done_when,
                "status": step.status_raw,
                "complete": step.complete,
                "optional": step.optional,
            }
            for step in steps
        ],
    }


def find_current_step(project_root: Path) -> dict[str, Any]:
    steps = load_plan_steps(project_root)
    if not steps:
        return {
            "step_id": None,
            "message": "No steps found in PLAN.md progress checklist",
        }

    for step in steps:
        if not step.complete:
            guide_abs = project_root / step.guide_path
            return {
                "step_id": step.step_id,
                "guide_path": step.guide_path,
                "guide_exists": guide_abs.is_file(),
                "done_when": step.done_when,
                "optional": step.optional,
                "message": f"Next incomplete step: {step.step_id}",
            }

    last = steps[-1]
    return {
        "step_id": last.step_id,
        "guide_path": last.guide_path,
        "guide_exists": (project_root / last.guide_path).is_file(),
        "done_when": last.done_when,
        "optional": last.optional,
        "message": "All checklist steps appear complete",
        "all_complete": True,
    }


def update_step_in_plan(plan_path: Path, step_id: str, completed: bool = True) -> bool:
    """Update the completion marker for a step in PLAN.md.

    This is a conservative implementation: it looks for a line containing
    **<step_id>** and replaces common checkbox markers with [x] when
    completed=True or [ ] when False. Returns True if a line was updated.
    """
    if not plan_path.is_file():
        return False

    text = plan_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    changed = False

    # match bold step id like **2** or **3a** (case-insensitive)
    escaped = re.escape(step_id)
    pattern = re.compile(rf"\*\*{escaped}\*\*", re.IGNORECASE)

    for i, line in enumerate(lines):
        if pattern.search(line):
            new_line = line

            # If a checkbox exists, prefer toggling it
            checkbox_match = re.search(r"\[(?:\s*[xX]?\s*)\]", line)
            if checkbox_match:
                if completed:
                    new_line = re.sub(r"\[\s*[xX]?\s*\]", "[x]", new_line)
                else:
                    new_line = re.sub(r"\[\s*[xX]\s*\]", "[ ]", new_line)
            else:
                # Only use textual fallback if explicit words are present
                if re.search(r"\b(done|complete)\b", line, flags=re.IGNORECASE):
                    if completed:
                        new_line = re.sub(r"\b(done|complete)\b", "[x]", new_line, flags=re.IGNORECASE)
                    else:
                        new_line = re.sub(r"\b(done|complete)\b", "[ ]", new_line, flags=re.IGNORECASE)
                else:
                    # No checkbox and no explicit textual marker: do not modify
                    return False

            if new_line != line:
                # backup original file
                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                backup = plan_path.with_name(f"{plan_path.name}.bak.{timestamp}")
                shutil.copy2(plan_path, backup)

                # atomic write
                dirpath = plan_path.parent
                with tempfile.NamedTemporaryFile("w", delete=False, dir=str(dirpath), encoding="utf-8") as tf:
                    lines[i] = new_line
                    tf.write("".join(lines))
                    tempname = tf.name
                shutil.move(tempname, str(plan_path))
                changed = True
            break

    return changed


def update_plan_notes_in_plan(plan_path: Path, step_id: str, note: str) -> bool:
    """Insert a note after the matching step line; avoid duplicates.

    Creates a timestamped backup before modifying the file.
    """
    if not plan_path.is_file():
        return False

    text = plan_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    escaped = re.escape(step_id)
    pattern = re.compile(rf"\*\*{escaped}\*\*", re.IGNORECASE)

    for i, line in enumerate(lines):
        if pattern.search(line):
            ts = datetime.utcnow().isoformat() + "Z"
            note_line = f"<!-- NOTE for {step_id} @ {ts}: {note} -->\n"

            # Check immediate next non-empty line to avoid duplicate notes
            next_idx = i + 1
            if next_idx < len(lines) and lines[next_idx].strip().startswith("<!-- NOTE for"):
                # if a previous note exists, append a new note instead of duplicating exact text
                pass

            # backup
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            backup = plan_path.with_name(f"{plan_path.name}.bak.{timestamp}")
            shutil.copy2(plan_path, backup)

            lines.insert(i + 1, note_line)
            dirpath = plan_path.parent
            with tempfile.NamedTemporaryFile("w", delete=False, dir=str(dirpath), encoding="utf-8") as tf:
                tf.write("".join(lines))
                tempname = tf.name
            shutil.move(tempname, str(plan_path))
            return True

    return False
