"""Tests for workflow_mcp plan parsing and step guide helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_MCP_SRC = REPO_ROOT / "packages" / "workflow_mcp"

SAMPLE_PLAN = """\
# Test project

## Progress checklist

| Step | Guide | Done when | Status |
|------|-------|-----------|--------|
| **0** | [STEP0-repo](docs/steps/STEP0-repo.md) | `data_io.check` passes | ☐ |
| **1** | [STEP1-language](docs/steps/STEP1-language.md) | Parquet OK | ☑ |
| **3a** | [STEP3a-phase-a](docs/steps/STEP3a-phase-a-yearly.md) | Ribbon + PPC | ☐ |
| **6** *(opt)* | [STEP6-phase-d](docs/steps/STEP6-phase-d.md) | Gap curves | ☐ |
"""


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    (project / "PLAN.md").write_text(SAMPLE_PLAN, encoding="utf-8")
    steps = project / "docs" / "steps"
    steps.mkdir(parents=True)
    (steps / "STEP0-repo.md").write_text("# Step 0\n", encoding="utf-8")
    (steps / "STEP1-language.md").write_text("# Step 1\n", encoding="utf-8")
    (steps / "STEP3a-phase-a-yearly.md").write_text("# Step 3a\n", encoding="utf-8")
    wisdom = project / "docs" / "wisdom"
    wisdom.mkdir(parents=True)
    (wisdom / "cost-sensitive-agent-workflow.md").write_text("# Workflow rules\n", encoding="utf-8")
    return project


@pytest.fixture
def mcp_path() -> None:
    root = str(WORKFLOW_MCP_SRC)
    if root not in sys.path:
        sys.path.insert(0, root)


def test_parse_plan_steps(mcp_path) -> None:
    from workflow_mcp.plan import parse_plan_steps

    steps = parse_plan_steps(SAMPLE_PLAN)
    assert [s.step_id for s in steps] == ["0", "1", "3a", "6"]
    assert steps[0].complete is False
    assert steps[1].complete is True
    assert steps[3].optional is True


def test_build_plan_status(project_dir: Path, mcp_path) -> None:
    from workflow_mcp.plan import build_plan_status

    status = build_plan_status(project_dir)
    assert status["step_count"] == 4
    assert status["completed_count"] == 1
    assert status["steps"][2]["step_id"] == "3a"


def test_find_current_step(project_dir: Path, mcp_path) -> None:
    from workflow_mcp.plan import find_current_step

    current = find_current_step(project_dir)
    assert current["step_id"] == "0"
    assert current["guide_path"] == "docs/steps/STEP0-repo.md"
    assert current["guide_exists"] is True


def test_list_step_guides(project_dir: Path, mcp_path) -> None:
    from workflow_mcp.steps import list_step_guides

    rows = list_step_guides(project_dir)
    ids = {row["step_id"] for row in rows}
    assert "0" in ids
    assert "3a" in ids


def test_read_step_guide(project_dir: Path, mcp_path) -> None:
    from workflow_mcp.steps import read_step_guide

    guide = read_step_guide(project_dir, "3a")
    assert guide["found"] is True
    assert guide["path"] == "docs/steps/STEP3a-phase-a-yearly.md"
    assert "# Step 3a" in guide["content"]


def test_read_step_guide_missing(project_dir: Path, mcp_path) -> None:
    from workflow_mcp.steps import read_step_guide

    guide = read_step_guide(project_dir, "99")
    assert guide["found"] is False
    assert "available_steps" in guide


def test_read_workflow_rules(project_dir: Path, mcp_path) -> None:
    from workflow_mcp.steps import read_workflow_rules

    rules = read_workflow_rules(project_dir)
    assert rules["found"] is True
    assert rules["path"] == "docs/wisdom/cost-sensitive-agent-workflow.md"


def test_resolve_project_root(project_dir: Path, mcp_path) -> None:
    from workflow_mcp.context import resolve_project_root

    root = resolve_project_root(project_dir)
    assert root == project_dir.resolve()
