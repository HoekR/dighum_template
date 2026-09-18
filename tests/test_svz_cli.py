from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SVZ_SCRIPT = REPO_ROOT / "template" / "scripts" / "svz.py"


def seed_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    shutil.copytree(REPO_ROOT / "template" / "docs", project / "docs")
    shutil.copytree(REPO_ROOT / "template" / "scripts", project / "scripts")
    return project


def run_svz(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(project / "scripts" / "svz.py"), *args],
        cwd=project,
        check=True,
        text=True,
        capture_output=True,
    )


def test_status_and_doctor(tmp_path: Path) -> None:
    project = seed_project(tmp_path)
    doctor = run_svz(project, "doctor")
    status = run_svz(project, "status")

    assert "SvZ state looks valid" in doctor.stdout
    assert "Project: PROJECT_NAME" in status.stdout
    assert "S0: Project setup" in status.stdout


def test_update_metric_and_render(tmp_path: Path) -> None:
    project = seed_project(tmp_path)

    run_svz(project, "update", "S1", "inprogress", "--title", "Diagnostics", "--notes", "D1 running")
    run_svz(project, "metric", "S1", "containment_mean", "0.295", "--label", "Mean containment")
    run_svz(project, "render")

    state = json.loads((project / "docs" / "state.json").read_text(encoding="utf-8"))
    rendered = (project / "docs" / "STATE.md").read_text(encoding="utf-8")

    assert any(task["id"] == "S1" and task["status"] == "inprogress" for task in state["tasks"])
    assert state["metrics"][0]["value"] == "0.295"
    assert "S1: Diagnostics" in rendered
    assert "Mean containment" in rendered


def test_decision_append(tmp_path: Path) -> None:
    project = seed_project(tmp_path)

    run_svz(
        project,
        "decision",
        "Boundary tolerance",
        "--context",
        "Boundaries may drift locally.",
        "--decision",
        "Use tolerance t=2.",
        "--reason",
        "Exact boundaries are too strict for line-level HTR.",
    )

    decisions = (project / "docs" / "DECISIONS.md").read_text(encoding="utf-8")
    assert "Boundary tolerance" in decisions
    assert "Use tolerance t=2." in decisions


def test_metric_history_and_review(tmp_path: Path) -> None:
    project = seed_project(tmp_path)
    run_svz(project, "update", "S1", "inprogress", "--title", "Diagnostics")
    run_svz(project, "metric", "S1", "f1", "0.50", "--label", "F1")
    # Second day: bump date by writing history directly then recording again is hard;
    # record twice same day overwrites — so seed a prior history point.
    state_path = project / "docs" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    for metric_entry in state["metrics"]:
        if metric_entry.get("name") == "f1":
            metric_entry["history"] = [
                {"date": "2026-01-01", "value": "0.50"},
                {"date": "2026-01-02", "value": "0.60"},
            ]
            metric_entry["value"] = "0.60"
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    review = run_svz(project, "review")
    assert "Active tracks needing a decision" in review.stdout
    assert "S1" in review.stdout
    assert "improving" in review.stdout

    # Stagnant flag
    state = json.loads(state_path.read_text(encoding="utf-8"))
    for metric_entry in state["metrics"]:
        if metric_entry.get("name") == "f1":
            metric_entry["history"] = [
                {"date": "2026-01-01", "value": "0.60"},
                {"date": "2026-01-02", "value": "0.601"},
            ]
            metric_entry["value"] = "0.601"
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    review2 = run_svz(project, "review")
    assert "stagnant" in review2.stdout
    assert "cutoff candidate" in review2.stdout


def test_metric_appends_history(tmp_path: Path) -> None:
    project = seed_project(tmp_path)
    run_svz(project, "metric", "S0", "acc", "0.1", "--label", "Acc")
    state = json.loads((project / "docs" / "state.json").read_text(encoding="utf-8"))
    assert len(state["metrics"][0]["history"]) == 1
    run_svz(project, "metric", "S0", "acc", "0.2")
    state = json.loads((project / "docs" / "state.json").read_text(encoding="utf-8"))
    # Same calendar day → overwrite last point
    assert len(state["metrics"][0]["history"]) == 1
    assert state["metrics"][0]["value"] == "0.2"
