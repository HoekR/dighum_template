#!/usr/bin/env python3
"""Manage the lightweight project state dashboard (SvZ).

The machine source of truth is docs/state.json. docs/STATE.md is rendered from
that file so AI agents and humans can read a compact, visual dashboard.

Claims (docs/claims.jsonl) hold research conclusions in a tiny schema.
``svz.py gate`` is the bookkeeping gatekeeper: no active claim with question +
consequence → refuse to continue (agents must patch claims first).

`review` supports the continue/switch/stop discipline in
docs/wisdom/iteration-policy.md (or the project's copy): it classifies each
track's latest recorded metric delta (improving / stagnant / regressing) so a
session can start by asking "which track has the clearest next gain" instead of
resuming whatever was last open.

Compose with workflow-mcp iteration orchestrator (plans/iteration.toml) for
within-track polish gates — see wisdom iteration-decision-framework and
claims-and-eval-gate.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


STATE_JSON = Path("docs/state.json")
STATE_MD = Path("docs/STATE.md")
DECISIONS_MD = Path("docs/DECISIONS.md")
CLAIMS_JSONL = Path("docs/claims.jsonl")
EVIDENCE_ROOT = Path("docs/evidence")
MANUAL_MARKER = "<!-- Manual notes below this line are preserved by scripts/svz.py render. -->"
VALID_STATUSES = {"todo", "inprogress", "done", "blocked"}
VALID_CLAIM_STATUSES = {
    "open",
    "deferred",
    "answered",
    "dead_for_this_q",
    "retracted",
}
CLOSED_CLAIM_STATUSES = {"deferred", "answered", "dead_for_this_q", "retracted"}
VALID_DESIGNS = {"observational", "controlled"}
MAX_ACTIVE_CLAIMS = 4
# Consequence should name a counterfactual / baseline (lint).
CONSEQUENCE_COMPARE_RE = re.compile(
    r"\b(vs\.?|versus|compared\s+to|relative\s+to|against|baseline|instead\s+of|"
    r"rather\s+than|over\s+running|vs\s+discarding)\b",
    re.I,
)
DEFAULT_TREND_THRESHOLD = 0.03


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def today_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def load_state() -> dict[str, Any]:
    if not STATE_JSON.exists():
        raise SystemExit(f"Missing {STATE_JSON}. Run from the project root or create state.json first.")
    return json.loads(STATE_JSON.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    state["last_updated"] = now_stamp()
    STATE_JSON.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_claims() -> dict[str, dict[str, Any]]:
    """Return claim id → latest record (jsonl rewritten as upserted map)."""
    if not CLAIMS_JSONL.exists():
        return {}
    out: dict[str, dict[str, Any]] = {}
    for line_no, line in enumerate(CLAIMS_JSONL.read_text(encoding="utf-8").splitlines(), start=1):
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        try:
            row = json.loads(text)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON on {CLAIMS_JSONL}:{line_no}: {exc}") from exc
        claim_id = str(row.get("id") or "").strip()
        if not claim_id:
            raise SystemExit(f"Missing claim id on {CLAIMS_JSONL}:{line_no}")
        out[claim_id] = row
    return out


def save_claims(claims: dict[str, dict[str, Any]]) -> None:
    CLAIMS_JSONL.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(claims[key], ensure_ascii=False, sort_keys=True)
        for key in sorted(claims)
    ]
    CLAIMS_JSONL.write_text(("\n".join(lines) + ("\n" if lines else "")), encoding="utf-8")


def active_claim_ids(state: dict[str, Any]) -> list[str]:
    """Prefer active_claim_ids; migrate legacy active_claim_id."""
    raw = state.get("active_claim_ids")
    if isinstance(raw, list):
        ids = [str(x).strip() for x in raw if str(x).strip()]
        # de-dupe preserve order
        seen: set[str] = set()
        out: list[str] = []
        for claim_id in ids:
            if claim_id not in seen:
                seen.add(claim_id)
                out.append(claim_id)
        return out
    legacy = str(state.get("active_claim_id") or "").strip()
    return [legacy] if legacy else []


def set_active_claim_ids(state: dict[str, Any], ids: list[str]) -> None:
    cleaned: list[str] = []
    seen: set[str] = set()
    for claim_id in ids:
        text = str(claim_id).strip()
        if text and text not in seen:
            seen.add(text)
            cleaned.append(text)
    if len(cleaned) > MAX_ACTIVE_CLAIMS:
        raise SystemExit(
            f"At most {MAX_ACTIVE_CLAIMS} active claims (got {len(cleaned)}). "
            "Deactivate one first: svz.py claim deactivate <id>"
        )
    state["active_claim_ids"] = cleaned
    # Keep legacy field in sync for older readers
    state["active_claim_id"] = cleaned[0] if cleaned else None


def consequence_has_comparison(text: str) -> bool:
    return bool(CONSEQUENCE_COMPARE_RE.search(str(text or "")))


def evidence_path_ok(path_text: str) -> bool:
    """Tier-1 evidence must be a repo-relative existing file (not only a string)."""
    raw = str(path_text or "").strip()
    if not raw:
        return False
    path = Path(raw)
    if path.is_absolute():
        return False
    if ".." in path.parts:
        return False
    return path.is_file()


def check_evidence_data(entries: Any) -> tuple[list[str], list[str]]:
    """Return (hard_problems, notices). Tier-2: soft-skip when drive unmounted."""
    problems: list[str] = []
    notices: list[str] = []
    if entries in (None, "", []):
        return problems, notices
    if not isinstance(entries, list):
        problems.append("evidence_data must be a list of {logical, sha256}")
        return problems, notices
    try:
        from data_io.manifest import ManifestManager  # noqa: PLC0415
    except ImportError:
        notices.append(
            "evidence_data present but data_io unavailable — skipped tier-2 hash checks"
        )
        return problems, notices
    try:
        manager = ManifestManager()
    except Exception as exc:  # noqa: BLE001 — soft path
        notices.append(f"evidence_data: could not load manifest ({exc}); skipped")
        return problems, notices
    for i, row in enumerate(entries):
        if not isinstance(row, dict):
            problems.append(f"evidence_data[{i}] must be an object")
            continue
        logical = str(row.get("logical") or "").strip()
        expected = str(row.get("sha256") or "").strip().lower()
        if not logical or not expected:
            problems.append(f"evidence_data[{i}] needs logical and sha256")
            continue
        if logical not in manager.datasets:
            problems.append(f"evidence_data[{i}] unknown logical name {logical!r}")
            continue
        dataset = manager.datasets[logical]
        if not manager.tier_available(dataset.tier):
            notices.append(
                f"evidence_data {logical!r}: tier {dataset.tier!r} unmounted — hash check skipped"
            )
            continue
        try:
            path = manager.resolve(logical)
        except Exception as exc:  # noqa: BLE001
            problems.append(f"evidence_data {logical!r}: resolve failed ({exc})")
            continue
        if not path.is_file():
            problems.append(f"evidence_data {logical!r}: missing file {path}")
            continue
        import hashlib

        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected:
            problems.append(
                f"evidence_data {logical!r}: sha256 mismatch "
                f"(expected {expected[:12]}…, got {digest[:12]}…)"
            )
    return problems, notices


def validate_claim_record(
    claim: dict[str, Any],
    *,
    require_closed_evidence: bool,
    lint_consequence: bool = True,
) -> tuple[list[str], list[str]]:
    """Return (problems, notices)."""
    problems: list[str] = []
    notices: list[str] = []
    claim_id = str(claim.get("id") or "").strip()
    if not claim_id:
        problems.append("claim missing id")
    status = str(claim.get("status") or "").strip()
    if status not in VALID_CLAIM_STATUSES:
        problems.append(f"claim {claim_id!r} has invalid status {status!r}")
    if not str(claim.get("question") or "").strip():
        problems.append(f"claim {claim_id!r} missing question")
    consequence = str(claim.get("consequence") or "").strip()
    if not consequence:
        problems.append(f"claim {claim_id!r} missing consequence")
    elif lint_consequence and not consequence_has_comparison(consequence):
        problems.append(
            f"claim {claim_id!r} consequence must name a comparison/baseline "
            "(e.g. 'vs. running everything', 'vs. discarding the bucket')"
        )
    design = claim.get("design")
    if design not in (None, ""):
        if str(design) not in VALID_DESIGNS:
            problems.append(
                f"claim {claim_id!r} design must be observational|controlled "
                f"(got {design!r})"
            )
    if require_closed_evidence and status in CLOSED_CLAIM_STATUSES:
        evidence = str(claim.get("evidence") or "").strip()
        if not evidence:
            problems.append(
                f"claim {claim_id!r} status {status} requires evidence path "
                f"under {EVIDENCE_ROOT}/"
            )
        elif not evidence_path_ok(evidence):
            problems.append(
                f"claim {claim_id!r} evidence {evidence!r} must be an existing "
                "repo-relative file (tier-1 committed summary)"
            )
        else:
            # Prefer docs/evidence/<id>/…
            path = Path(evidence)
            if EVIDENCE_ROOT.parts[0] not in path.parts and not str(path).startswith(
                str(EVIDENCE_ROOT)
            ):
                notices.append(
                    f"claim {claim_id!r}: evidence outside {EVIDENCE_ROOT}/ "
                    "(allowed but prefer docs/evidence/<claim_id>/)"
                )
        data_problems, data_notices = check_evidence_data(claim.get("evidence_data"))
        problems.extend(data_problems)
        notices.extend(data_notices)
    return problems, notices


def gate_check(
    state: dict[str, Any] | None = None,
) -> tuple[bool, list[str], list[str], list[dict[str, Any]]]:
    """Return (ok, problems, notices, active_claims)."""
    state = state if state is not None else load_state()
    claims = load_claims()
    ids = active_claim_ids(state)
    notices: list[str] = []
    if not ids:
        return (
            False,
            [
                "No active claims. Open one: "
                "uv run python scripts/svz.py claim open <id> "
                '--question "..." --consequence "vs. …"'
            ],
            notices,
            [],
        )
    if len(ids) > MAX_ACTIVE_CLAIMS:
        return (
            False,
            [f"Too many active claims ({len(ids)} > {MAX_ACTIVE_CLAIMS})"],
            notices,
            [],
        )
    problems: list[str] = []
    active_rows: list[dict[str, Any]] = []
    for claim_id in ids:
        claim = claims.get(claim_id)
        if claim is None:
            problems.append(f"active claim {claim_id!r} not in {CLAIMS_JSONL}")
            continue
        row_problems, row_notices = validate_claim_record(
            claim, require_closed_evidence=True
        )
        problems.extend(row_problems)
        notices.extend(row_notices)
        active_rows.append(claim)
    return (not problems and bool(active_rows), problems, notices, active_rows)


def task_symbol(status: str) -> str:
    return {"done": "x", "inprogress": "/", "blocked": "!"}.get(status, " ")


def mermaid_class(status: str) -> str:
    return status if status in VALID_STATUSES else "todo"


def mermaid_id(task_id: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_]", "_", task_id)
    return clean if clean and clean[0].isalpha() else f"T_{clean}"


def find_task(state: dict[str, Any], task_id: str) -> dict[str, Any] | None:
    for task in state.get("tasks", []):
        if task.get("id") == task_id:
            return task
    return None


def parse_number(value: Any) -> float | None:
    """Best-effort numeric read of a metric value: '0.576', '70.7%', '9/21'."""
    text = str(value).strip()
    if not text:
        return None
    fraction = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*/\s*(-?\d+(?:\.\d+)?)", text)
    if fraction:
        numerator, denominator = (float(part) for part in fraction.groups())
        return numerator / denominator if denominator else None
    is_percent = text.endswith("%")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    number = float(match.group())
    return number / 100 if is_percent else number


def classify_trend(history: list[dict[str, Any]], threshold: float) -> tuple[str, float | None]:
    """Compare the two most recent numeric history points.

    Returns (verdict, delta) where verdict is one of:
    "improving", "stagnant", "regressing", "insufficient-history".
    Direction is read literally (higher = improving) — invert the metric's own
    value at recording time (e.g. record 1 - other_bucket_pct) if lower is better.
    """
    numeric_points = [parse_number(point.get("value")) for point in history]
    numeric_points = [value for value in numeric_points if value is not None]
    if len(numeric_points) < 2:
        return "insufficient-history", None
    previous, latest = numeric_points[-2], numeric_points[-1]
    delta = latest - previous
    relative = delta / abs(previous) if previous else (None if delta == 0 else delta)
    if relative is None:
        verdict = "stagnant"
    elif relative > threshold:
        verdict = "improving"
    elif relative < -threshold:
        verdict = "regressing"
    else:
        verdict = "stagnant"
    return verdict, delta


def preserved_notes() -> str:
    if not STATE_MD.exists():
        return "## Notes\n\n"
    content = STATE_MD.read_text(encoding="utf-8")
    if MANUAL_MARKER not in content:
        return "## Notes\n\n"
    return content.split(MANUAL_MARKER, 1)[1].lstrip()


def render_active_claim_section(state: dict[str, Any]) -> list[str]:
    lines = ["## Active Claim", ""]
    active_id = str(state.get("active_claim_id") or "").strip()
    if not active_id:
        lines.extend(
            [
                "_No active claim._ Run "
                "`uv run python scripts/svz.py claim open <id> --question \"...\" "
                "--consequence \"...\"` then `svz.py gate`.",
                "",
            ]
        )
        return lines
    claims = load_claims()
    claim = claims.get(active_id)
    if claim is None:
        lines.extend(
            [
                f"**Broken pointer:** `active_claim_id={active_id}` missing from `{CLAIMS_JSONL}`.",
                "",
            ]
        )
        return lines
    lines.extend(
        [
            f"- **id:** `{claim.get('id')}`",
            f"- **status:** `{claim.get('status')}`",
            f"- **question:** {claim.get('question')}",
            f"- **consequence:** {claim.get('consequence')}",
        ]
    )
    if claim.get("evidence"):
        lines.append(f"- **evidence:** `{claim.get('evidence')}`")
    if claim.get("supersedes"):
        lines.append(f"- **supersedes:** `{claim.get('supersedes')}`")
    if claim.get("interpretation_id"):
        lines.append(f"- **interpretation_id:** `{claim.get('interpretation_id')}`")
    lines.append("")
    return lines


def render_markdown(state: dict[str, Any]) -> str:
    tasks = state.get("tasks", [])
    metrics = state.get("metrics", [])
    blockers = state.get("blockers", [])
    dependencies = state.get("dependencies", [])
    next_actions = state.get("next_actions", [])
    last_updated = state.get("last_updated") or "not set"

    lines: list[str] = [
        "# Current Project State (SvZ)",
        "",
        f"Last updated: {last_updated}",
        "",
        "```mermaid",
        "flowchart TD",
        "    classDef done fill:#2e7d32,stroke:#1b5e20,color:#fff,stroke-width:2px;",
        "    classDef inprogress fill:#f57c00,stroke:#e65100,color:#fff,stroke-width:2px;",
        "    classDef todo fill:#424242,stroke:#212121,color:#ddd,stroke-width:1px,stroke-dasharray: 5 5;",
        "    classDef blocked fill:#c62828,stroke:#b71c1c,color:#fff,stroke-width:2px;",
        "",
    ]
    for task in tasks:
        node_id = mermaid_id(str(task.get("id", "task")))
        label = f"{task.get('id', '')}: {task.get('title', '')}".replace('"', "'")
        lines.append(f"    {node_id}[\"{label}\"] :::{mermaid_class(str(task.get('status', 'todo')))}")
    if dependencies:
        for dependency in dependencies:
            source = mermaid_id(str(dependency.get("from", "")))
            target = mermaid_id(str(dependency.get("to", "")))
            if source and target:
                lines.append(f"    {source} --> {target}")
    else:
        for first, second in zip(tasks, tasks[1:]):
            lines.append(f"    {mermaid_id(str(first.get('id', '')))} --> {mermaid_id(str(second.get('id', '')))}")
    lines.extend(["```", "", "## Overall Progress", ""])

    if tasks:
        for task in tasks:
            status = str(task.get("status", "todo"))
            task_line = f"- [{task_symbol(status)}] {task.get('id')}: {task.get('title')}"
            if task.get("notes"):
                task_line += f" — {task['notes']}"
            lines.append(task_line)
    else:
        lines.append("No tasks recorded yet.")

    lines.extend(["", "## Active Focus", "", str(state.get("active_focus") or "No active focus recorded."), ""])
    lines.extend(render_active_claim_section(state))
    lines.extend(["## Key Intermediate Results & Metrics", ""])
    if metrics:
        for metric_entry in metrics:
            value = metric_entry.get("value", "")
            label = metric_entry.get("label") or metric_entry.get("name") or "metric"
            scope = metric_entry.get("scope")
            prefix = f"{scope} — " if scope else ""
            verdict, delta = classify_trend(metric_entry.get("history", []), DEFAULT_TREND_THRESHOLD)
            trend = f" ({verdict}, Δ{delta:+.3f})" if delta is not None else ""
            lines.append(f"- **{prefix}{label}:** {value}{trend}")
    else:
        lines.append("No metrics recorded yet.")

    lines.extend(["", "## Blockers / Open Questions", ""])
    if blockers:
        lines.extend(f"- [ ] {item}" for item in blockers)
    else:
        lines.append("No blockers recorded.")

    lines.extend(["", "## Next Actions", ""])
    if next_actions:
        lines.extend(f"- {item}" for item in next_actions)
    else:
        lines.append("No next actions recorded.")

    lines.extend(["", MANUAL_MARKER, preserved_notes().rstrip(), ""])
    return "\n".join(lines)


def render(_: argparse.Namespace) -> None:
    state = load_state()
    STATE_MD.write_text(render_markdown(state), encoding="utf-8")
    print(f"Rendered {STATE_MD} from {STATE_JSON}")


def status(_: argparse.Namespace) -> None:
    state = load_state()
    print(f"Project: {state.get('project', 'unknown')}")
    print(f"Last updated: {state.get('last_updated') or 'not set'}")
    print(f"Active focus: {state.get('active_focus') or 'none'}")
    print(f"Active claim: {state.get('active_claim_id') or 'none'}")
    print("\nTasks:")
    for task in state.get("tasks", []):
        print(f"  [{task_symbol(str(task.get('status', 'todo')))}] {task.get('id')}: {task.get('title')}")
    if state.get("metrics"):
        print("\nMetrics:")
        for metric_entry in state["metrics"]:
            scope = f"{metric_entry.get('scope')}: " if metric_entry.get("scope") else ""
            print(f"  - {scope}{metric_entry.get('label') or metric_entry.get('name')}: {metric_entry.get('value')}")


def update(args: argparse.Namespace) -> None:
    if args.status not in VALID_STATUSES:
        raise SystemExit(f"Status must be one of: {', '.join(sorted(VALID_STATUSES))}")
    state = load_state()
    task = find_task(state, args.task_id)
    if task is None:
        task = {"id": args.task_id, "title": args.title or args.task_id, "status": args.status, "notes": ""}
        state.setdefault("tasks", []).append(task)
    else:
        task["status"] = args.status
        if args.title:
            task["title"] = args.title
    if args.notes is not None:
        task["notes"] = args.notes
    save_state(state)
    STATE_MD.write_text(render_markdown(state), encoding="utf-8")
    print(f"Set {args.task_id} to {args.status}")


def focus(args: argparse.Namespace) -> None:
    state = load_state()
    state["active_focus"] = args.text
    save_state(state)
    STATE_MD.write_text(render_markdown(state), encoding="utf-8")
    print("Updated active focus")


def metric(args: argparse.Namespace) -> None:
    """Record a metric value; append to history (same day overwrites last point)."""
    state = load_state()
    today = today_date()
    metrics = state.setdefault("metrics", [])
    for existing in metrics:
        if existing.get("scope") == args.scope and existing.get("name") == args.name:
            history = existing.setdefault("history", [])
            if history and history[-1].get("date") == today:
                history[-1]["value"] = args.value
            else:
                history.append({"date": today, "value": args.value})
            existing["value"] = args.value
            if args.label:
                existing["label"] = args.label
            break
    else:
        metrics.append(
            {
                "scope": args.scope,
                "name": args.name,
                "label": args.label or args.name,
                "value": args.value,
                "history": [{"date": today, "value": args.value}],
            }
        )
    save_state(state)
    STATE_MD.write_text(render_markdown(state), encoding="utf-8")
    print(f"Recorded metric {args.name}={args.value}")


def decision(args: argparse.Namespace) -> None:
    DECISIONS_MD.parent.mkdir(parents=True, exist_ok=True)
    if not DECISIONS_MD.exists():
        DECISIONS_MD.write_text("# Decision Log\n\n", encoding="utf-8")
    entry = (
        f"\n## {datetime.now().strftime('%Y-%m-%d')}: {args.title}\n\n"
        f"- **Context:** {args.context}\n"
        f"- **Decision:** {args.decision}\n"
        f"- **Reason:** {args.reason}\n"
    )
    with DECISIONS_MD.open("a", encoding="utf-8") as handle:
        handle.write(entry)
    print(f"Appended decision to {DECISIONS_MD}")


def query(args: argparse.Namespace) -> None:
    state = load_state()
    haystack = json.dumps(state, ensure_ascii=False, indent=2).lower()
    if args.term.lower() not in haystack:
        print(f"No matches for {args.term!r}")
        return
    print(json.dumps(state, ensure_ascii=False, indent=2))


def review(args: argparse.Namespace) -> None:
    state = load_state()
    threshold = args.threshold
    by_scope: dict[str, list[dict[str, Any]]] = {}
    for metric_entry in state.get("metrics", []):
        by_scope.setdefault(str(metric_entry.get("scope")), []).append(metric_entry)

    active, pending, closed = [], [], []
    for task in state.get("tasks", []):
        bucket = {"inprogress": active, "todo": pending}.get(str(task.get("status", "todo")), closed)
        bucket.append(task)

    print("== Active tracks needing a decision ==")
    if not active:
        print("  (none marked inprogress)")
    for task in active:
        print(f"- {task.get('id')}: {task.get('title')}")
        task_metrics = by_scope.get(str(task.get("id")), [])
        if not task_metrics:
            print("    no metric recorded — run `svz.py metric ...` before judging this track")
            continue
        for metric_entry in task_metrics:
            verdict, delta = classify_trend(metric_entry.get("history", []), threshold)
            delta_str = f"{delta:+.3f}" if delta is not None else "n/a"
            flag = "  <- cutoff candidate" if verdict == "stagnant" else ""
            print(f"    {metric_entry.get('label')}: {metric_entry.get('value')} (Δ {delta_str}, {verdict}){flag}")

    print("\n== Not started ==")
    if not pending:
        print("  (none)")
    for task in pending:
        note = f" — {task['notes']}" if task.get("notes") else ""
        print(f"- {task.get('id')}: {task.get('title')}{note}")

    print("\n== Closed (done / blocked) ==")
    if not closed:
        print("  (none)")
    for task in closed:
        note = f" — {task['notes']}" if task.get("notes") else ""
        print(f"- [{task.get('status')}] {task.get('id')}: {task.get('title')}{note}")

    print(
        "\nSee docs/wisdom/iteration-policy.md and claims-and-eval-gate.md before "
        "switching tracks or recording a cutoff (`svz.py decision ...` / `claim close`). "
        "Within a track, use workflow-orchestrator advise if plans/iteration.toml exists. "
        "Run `svz.py gate` before continuing work."
    )


def doctor(_: argparse.Namespace) -> None:
    state = load_state()
    problems: list[str] = []
    task_ids = [task.get("id") for task in state.get("tasks", [])]
    if len(task_ids) != len(set(task_ids)):
        problems.append("Duplicate task ids in docs/state.json")
    for task in state.get("tasks", []):
        if task.get("status") not in VALID_STATUSES:
            problems.append(f"Invalid status for {task.get('id')}: {task.get('status')}")
    task_id_set = {str(task_id) for task_id in task_ids}
    for metric_entry in state.get("metrics", []):
        scope = str(metric_entry.get("scope"))
        if scope not in task_id_set and not any(scope.startswith(f"{task_id}-") for task_id in task_id_set):
            problems.append(
                f"Metric {metric_entry.get('name')!r} has scope {metric_entry.get('scope')!r} "
                "that does not match any task id (or <task_id>-<subid> pattern)"
            )

    claims = load_claims()
    for claim in claims.values():
        problems.extend(validate_claim_record(claim, require_closed_evidence=True))
    active_id = str(state.get("active_claim_id") or "").strip()
    if active_id and active_id not in claims:
        problems.append(f"active_claim_id={active_id!r} missing from {CLAIMS_JSONL}")

    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        raise SystemExit(1)
    print("SvZ state looks valid")
    ok, gate_problems, _ = gate_check(state)
    if ok:
        print("Claims gate: PASS")
    else:
        print("Claims gate: FAIL (informational — use `svz.py gate` to enforce)")
        for problem in gate_problems:
            print(f"  - {problem}")


def gate(_: argparse.Namespace) -> None:
    ok, problems, claim = gate_check()
    if not ok:
        print("Claims gate: FAIL", file=sys.stderr)
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        raise SystemExit(1)
    assert claim is not None
    print("Claims gate: PASS")
    print(f"  id: {claim.get('id')}")
    print(f"  status: {claim.get('status')}")
    print(f"  question: {claim.get('question')}")
    print(f"  consequence: {claim.get('consequence')}")


def claim_open(args: argparse.Namespace) -> None:
    claim_id = str(args.claim_id).strip()
    if not claim_id:
        raise SystemExit("claim id required")
    claims = load_claims()
    if claim_id in claims and not args.force:
        raise SystemExit(f"Claim {claim_id!r} already exists (pass --force to replace)")
    claim = {
        "id": claim_id,
        "question": args.question,
        "status": "open",
        "evidence": args.evidence or "",
        "consequence": args.consequence,
        "supersedes": args.supersedes or None,
        "interpretation_id": args.interpretation_id or None,
        "updated": today_date(),
    }
    problems = validate_claim_record(claim, require_closed_evidence=False)
    if problems:
        raise SystemExit("; ".join(problems))
    claims[claim_id] = claim
    save_claims(claims)
    state = load_state()
    state["active_claim_id"] = claim_id
    if args.sync_focus:
        state["active_focus"] = args.question
    save_state(state)
    STATE_MD.write_text(render_markdown(state), encoding="utf-8")
    print(f"Opened claim {claim_id} and set active_claim_id")


def claim_close(args: argparse.Namespace) -> None:
    status = args.status
    if status not in CLOSED_CLAIM_STATUSES:
        raise SystemExit(
            f"close status must be one of: {', '.join(sorted(CLOSED_CLAIM_STATUSES))}"
        )
    state = load_state()
    claims = load_claims()
    claim_id = str(args.claim_id or state.get("active_claim_id") or "").strip()
    if not claim_id:
        raise SystemExit("No claim id and no active_claim_id")
    claim = claims.get(claim_id)
    if claim is None:
        raise SystemExit(f"Unknown claim {claim_id!r}")
    claim["status"] = status
    claim["evidence"] = args.evidence
    if args.consequence:
        claim["consequence"] = args.consequence
    claim["updated"] = today_date()
    problems = validate_claim_record(claim, require_closed_evidence=True)
    if problems:
        raise SystemExit("; ".join(problems))
    claims[claim_id] = claim
    save_claims(claims)
    if args.clear_active or args.park:
        state["active_claim_id"] = None
    save_state(state)
    STATE_MD.write_text(render_markdown(state), encoding="utf-8")
    print(f"Closed claim {claim_id} as {status}")
    if state.get("active_claim_id") is None:
        print("active_claim_id cleared — gate will FAIL until a new claim is opened")


def claim_show(args: argparse.Namespace) -> None:
    state = load_state()
    claims = load_claims()
    claim_id = str(args.claim_id or state.get("active_claim_id") or "").strip()
    if not claim_id:
        raise SystemExit("No claim id and no active_claim_id")
    claim = claims.get(claim_id)
    if claim is None:
        raise SystemExit(f"Unknown claim {claim_id!r}")
    print(json.dumps(claim, indent=2, ensure_ascii=False))


def claim_list(_: argparse.Namespace) -> None:
    claims = load_claims()
    if not claims:
        print("(no claims)")
        return
    state = load_state()
    active = str(state.get("active_claim_id") or "")
    for claim_id, claim in sorted(claims.items()):
        mark = "*" if claim_id == active else " "
        print(
            f"{mark} {claim_id}  [{claim.get('status')}]  "
            f"{claim.get('question')}"
        )


def claim_activate(args: argparse.Namespace) -> None:
    claims = load_claims()
    claim_id = str(args.claim_id).strip()
    if claim_id not in claims:
        raise SystemExit(f"Unknown claim {claim_id!r}")
    state = load_state()
    state["active_claim_id"] = claim_id
    if args.sync_focus:
        state["active_focus"] = claims[claim_id].get("question") or state.get("active_focus")
    save_state(state)
    STATE_MD.write_text(render_markdown(state), encoding="utf-8")
    print(f"Active claim set to {claim_id}")


def claim_clear_active(_: argparse.Namespace) -> None:
    state = load_state()
    state["active_claim_id"] = None
    save_state(state)
    STATE_MD.write_text(render_markdown(state), encoding="utf-8")
    print("Cleared active_claim_id (gate will FAIL)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage docs/state.json and render docs/STATE.md.")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Print a compact state summary").set_defaults(func=status)
    subparsers.add_parser("render", help="Render docs/STATE.md from docs/state.json").set_defaults(func=render)
    subparsers.add_parser("doctor", help="Validate docs/state.json (+ claims schema)").set_defaults(func=doctor)
    subparsers.add_parser(
        "gate",
        help="Bookkeeping gatekeeper: require active claim with question+consequence",
    ).set_defaults(func=gate)

    update_parser = subparsers.add_parser("update", help="Set or create a task status")
    update_parser.add_argument("task_id")
    update_parser.add_argument("status", choices=sorted(VALID_STATUSES))
    update_parser.add_argument("--title")
    update_parser.add_argument("--notes")
    update_parser.set_defaults(func=update)

    focus_parser = subparsers.add_parser("focus", help="Set the active focus text")
    focus_parser.add_argument("text")
    focus_parser.set_defaults(func=focus)

    metric_parser = subparsers.add_parser(
        "metric",
        help="Record or update a metric (appends to its history)",
    )
    metric_parser.add_argument("scope", help="Task id this metric belongs to")
    metric_parser.add_argument("name")
    metric_parser.add_argument("value")
    metric_parser.add_argument("--label")
    metric_parser.set_defaults(func=metric)

    decision_parser = subparsers.add_parser("decision", help="Append a decision log entry")
    decision_parser.add_argument("title")
    decision_parser.add_argument("--context", required=True)
    decision_parser.add_argument("--decision", required=True)
    decision_parser.add_argument("--reason", required=True)
    decision_parser.set_defaults(func=decision)

    query_parser = subparsers.add_parser("query", help="Print state JSON if a term appears in it")
    query_parser.add_argument("term")
    query_parser.set_defaults(func=query)

    review_parser = subparsers.add_parser(
        "review",
        help="Classify each track's latest metric trend (continue/switch/stop aid)",
    )
    review_parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_TREND_THRESHOLD,
        help=(
            f"Relative delta magnitude below which a metric counts as stagnant "
            f"(default {DEFAULT_TREND_THRESHOLD})"
        ),
    )
    review_parser.set_defaults(func=review)

    claim_parser = subparsers.add_parser("claim", help="Manage docs/claims.jsonl research claims")
    claim_sub = claim_parser.add_subparsers(dest="claim_command", required=True)

    open_p = claim_sub.add_parser("open", help="Create/upsert a claim and set it active")
    open_p.add_argument("claim_id")
    open_p.add_argument("--question", required=True)
    open_p.add_argument("--consequence", required=True)
    open_p.add_argument("--evidence", default="")
    open_p.add_argument("--supersedes", default="")
    open_p.add_argument("--interpretation-id", dest="interpretation_id", default="")
    open_p.add_argument("--force", action="store_true")
    open_p.add_argument(
        "--sync-focus",
        action="store_true",
        help="Also set active_focus to the claim question",
    )
    open_p.set_defaults(func=claim_open)

    close_p = claim_sub.add_parser("close", help="Close a claim (answered/deferred/dead_for_this_q)")
    close_p.add_argument("claim_id", nargs="?", default="")
    close_p.add_argument(
        "--status",
        required=True,
        choices=sorted(CLOSED_CLAIM_STATUSES),
    )
    close_p.add_argument("--evidence", required=True)
    close_p.add_argument("--consequence", default="")
    close_p.add_argument(
        "--clear-active",
        "--park",
        dest="clear_active",
        action="store_true",
        help="Clear active_claim_id after close (gate fails until next open)",
    )
    close_p.set_defaults(func=claim_close, park=False)

    show_p = claim_sub.add_parser("show", help="Print one claim as JSON")
    show_p.add_argument("claim_id", nargs="?", default="")
    show_p.set_defaults(func=claim_show)

    list_p = claim_sub.add_parser("list", help="List claims (* = active)")
    list_p.set_defaults(func=claim_list)

    act_p = claim_sub.add_parser("activate", help="Set active_claim_id to an existing claim")
    act_p.add_argument("claim_id")
    act_p.add_argument("--sync-focus", action="store_true")
    act_p.set_defaults(func=claim_activate)

    clear_p = claim_sub.add_parser("clear-active", help="Clear active_claim_id (park)")
    clear_p.set_defaults(func=claim_clear_active)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        args = parser.parse_args(["status"])
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
