from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT = REPO_ROOT / "template" / ".github" / "agents" / "plan-step-executor.agent.md"
SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync_project.sh"


def run_sync(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(SYNC_SCRIPT), str(project), "--agents", *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def test_agent_frontmatter_and_template_inclusion() -> None:
    content = AGENT.read_text(encoding="utf-8")

    assert content.startswith("---\n")
    frontmatter, _ = content[4:].split("\n---\n", 1)
    assert "description:" in frontmatter
    assert "tools: [read, edit, search, execute]" in frontmatter
    assert "user-invocable: true" in frontmatter
    assert (REPO_ROOT / "template" / ".github" / "agents" / AGENT.name).is_file()


def test_agents_sync_copies_missing_agent(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    run_sync(project)

    copied = project / ".github" / "agents" / AGENT.name
    assert copied.read_text(encoding="utf-8") == AGENT.read_text(encoding="utf-8")


def test_agents_sync_preserves_existing_agent_and_writes_new_copy(tmp_path: Path) -> None:
    project = tmp_path / "project"
    destination = project / ".github" / "agents" / AGENT.name
    destination.parent.mkdir(parents=True)
    destination.write_text("local customization\n", encoding="utf-8")

    result = run_sync(project)

    assert destination.read_text(encoding="utf-8") == "local customization\n"
    assert destination.with_name(f"{AGENT.name}.new").read_text(encoding="utf-8") == AGENT.read_text(encoding="utf-8")
    assert "kept existing" in result.stdout


def test_bootstrap_template_copy_would_include_agent(tmp_path: Path) -> None:
    target = tmp_path / "project"
    shutil.copytree(REPO_ROOT / "template", target)

    assert (target / ".github" / "agents" / AGENT.name).is_file()
