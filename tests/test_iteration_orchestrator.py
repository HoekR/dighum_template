"""Tests for iteration orchestrator (gates, budgets, interlocks)."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_MCP_SRC = REPO_ROOT / "packages" / "workflow_mcp"
EXAMPLE_TOML = WORKFLOW_MCP_SRC / "examples" / "iteration.toml"

MINIMAL_TOML = """\
[meta]
version = 1

[facts]
ready = true

[[stages]]
id = "upstream"
done = true
done_when = "base ready"
requires_facts = []
requires_stages = []

[[stages]]
id = "downstream"
done = false
done_when = "calibrated"
requires_facts = ["ready"]
requires_stages = ["upstream"]

[[concerns]]
id = "metric_loop"
stage = "downstream"
max_attempts = 2
escalate_to = "change_success_criteria"

[[concerns]]
id = "partner_a"
stage = "upstream"
max_attempts = 3
escalate_to = "ask_human"
reopen = true

[[concerns]]
id = "partner_b"
stage = "upstream"
max_attempts = 3
escalate_to = "ask_human"
reopen = true

[[interlocks]]
a = "partner_a"
b = "partner_b"
blocking = true
"""


@pytest.fixture
def mcp_path() -> None:
    root = str(WORKFLOW_MCP_SRC)
    if root not in sys.path:
        sys.path.insert(0, root)


@pytest.fixture
def iter_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    (project / "PLAN.md").write_text("# Plan\n", encoding="utf-8")
    plans = project / "plans"
    plans.mkdir()
    (plans / "iteration.toml").write_text(MINIMAL_TOML, encoding="utf-8")
    return project


def test_load_example_toml(mcp_path) -> None:
    from workflow_mcp.orchestrator import load_iteration_config

    # Load via temp project that copies the example
    root = Path(WORKFLOW_MCP_SRC).parent  # unused; load from example path via copy
    # Direct parse: write example into tmp
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp)
        (proj / "plans").mkdir()
        shutil.copy(EXAMPLE_TOML, proj / "plans" / "iteration.toml")
        cfg = load_iteration_config(proj)
        assert "metric_chase" in cfg.concerns
        assert cfg.facts.get("inputs_registered") is True


def test_advise_continue(iter_project: Path, mcp_path) -> None:
    from workflow_mcp.orchestrator import Verdict, advise

    advice = advise(iter_project, "metric_loop")
    assert advice.verdict == Verdict.CONTINUE.value
    assert advice.attempts_used == 0


def test_advise_escalate_missing_fact(iter_project: Path, mcp_path) -> None:
    from workflow_mcp.orchestrator import Verdict, advise, load_iteration_config

    path = iter_project / "plans" / "iteration.toml"
    path.write_text(MINIMAL_TOML.replace("ready = true", "ready = false"), encoding="utf-8")
    advice = advise(iter_project, "metric_loop")
    assert advice.verdict == Verdict.ESCALATE_UPSTREAM.value
    assert any(b.startswith("fact:") for b in advice.blocked_by)


def test_advise_budget_exhausted(iter_project: Path, mcp_path) -> None:
    from workflow_mcp.orchestrator import Verdict, advise, record_attempt

    record_attempt(iter_project, "metric_loop", outcome="no_gain")
    record_attempt(iter_project, "metric_loop", outcome="no_gain")
    advice = advise(iter_project, "metric_loop")
    assert advice.verdict == Verdict.CHANGE_SUCCESS_CRITERIA.value
    assert advice.attempts_used == 2


def test_advise_defer_blocking_interlock(iter_project: Path, mcp_path) -> None:
    from workflow_mcp.orchestrator import Verdict, advise

    advice = advise(iter_project, "partner_a")
    assert advice.verdict == Verdict.DEFER.value
    assert any(x["partner"] == "partner_b" for x in advice.open_interlocks)


def test_record_does_not_create_plan_ticks(iter_project: Path, mcp_path) -> None:
    from workflow_mcp.orchestrator import record_attempt

    plan_before = (iter_project / "PLAN.md").read_text(encoding="utf-8")
    record_attempt(iter_project, "metric_loop", outcome="improved", note="ok")
    plan_after = (iter_project / "PLAN.md").read_text(encoding="utf-8")
    assert plan_before == plan_after
    log = iter_project / "plans" / "iteration_log.jsonl"
    assert log.is_file()
    assert "metric_loop" in log.read_text(encoding="utf-8")


def test_unknown_concern(iter_project: Path, mcp_path) -> None:
    from workflow_mcp.orchestrator import Verdict, advise

    advice = advise(iter_project, "nope")
    assert advice.verdict == Verdict.ASK_HUMAN.value
