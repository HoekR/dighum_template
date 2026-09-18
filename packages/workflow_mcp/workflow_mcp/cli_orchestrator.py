"""CLI: workflow-orchestrator advise | record | show-config."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from workflow_mcp.context import resolve_project_root
from workflow_mcp.orchestrator import (
    advise,
    load_iteration_config,
    record_attempt,
)


def _cmd_advise(args: argparse.Namespace) -> int:
    root = Path(args.project_root) if args.project_root else resolve_project_root()
    try:
        advice = advise(root, args.concern, note=args.note)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(advice.to_dict(), indent=2, ensure_ascii=False))
    if advice.svz_hint:
        print(f"\n# optional svz:\n# {advice.svz_hint}", file=sys.stderr)
    return 0


def _cmd_record(args: argparse.Namespace) -> int:
    root = Path(args.project_root) if args.project_root else resolve_project_root()
    try:
        result = record_attempt(
            root,
            args.concern,
            outcome=args.outcome,
            note=args.note or "",
        )
    except Exception as exc:  # noqa: BLE001 — CLI surface
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _cmd_show_config(args: argparse.Namespace) -> int:
    root = Path(args.project_root) if args.project_root else resolve_project_root()
    try:
        cfg = load_iteration_config(root)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(cfg.to_public_dict(), indent=2, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> None:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--project-root",
        default=None,
        help="Project root (default: WORKFLOW_PROJECT_ROOT or walk for PLAN.md)",
    )

    parser = argparse.ArgumentParser(
        prog="workflow-orchestrator",
        description=(
            "Iteration advisor: stage gates, attempt budgets, interlocks. "
            "Does not tick PLAN.md."
        ),
        parents=[parent],
    )
    sub = parser.add_subparsers(dest="command", required=True)

    advise_p = sub.add_parser("advise", help="Verdict for a concern", parents=[parent])
    advise_p.add_argument("--concern", required=True)
    advise_p.add_argument("--note", default=None)
    advise_p.set_defaults(func=_cmd_advise)

    record_p = sub.add_parser(
        "record",
        help="Append attempt to plans/iteration_log.jsonl",
        parents=[parent],
    )
    record_p.add_argument("--concern", required=True)
    record_p.add_argument("--outcome", required=True, help="e.g. no_gain, improved, deferred")
    record_p.add_argument("--note", default="")
    record_p.set_defaults(func=_cmd_record)

    show_p = sub.add_parser(
        "show-config",
        help="Print effective plans/iteration.toml",
        parents=[parent],
    )
    show_p.set_defaults(func=_cmd_show_config)

    args = parser.parse_args(argv)
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
