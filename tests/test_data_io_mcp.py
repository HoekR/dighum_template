"""Tests for data_io_mcp registry, preview, and provenance helpers."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_IO_SRC = REPO_ROOT / "packages" / "data_io"
DATA_IO_MCP_SRC = REPO_ROOT / "packages" / "data_io_mcp"


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    shutil.copytree(DATA_IO_SRC, tmp_path / "data_io")
    manifest = tmp_path / "data_manifest.toml"
    manifest.write_text(
        """
[tiers.hot]
root = "{root}"
mount_check = ""

[tiers.warm]
root = "{warm}"
mount_check = "{warm}"

[tiers.scratch]
root = "{scratch}"
mount_check = "{scratch}"

[datasets.sample_jsonl]
tier = "scratch"
path = "out/sample.jsonl"
phase = "semi"
description = "Test semi-structured output"
parent = "sample_parent"

[datasets.sample_parquet]
tier = "warm"
path = "out/sample.parquet"
phase = "frozen"
description = "Test frozen output"
parent = "sample_parent"

[datasets.sample_json]
tier = "scratch"
path = "out/sample.json"
phase = "semi"
description = "Test JSON output"
parent = ""
""".format(
            root=str(tmp_path / "hot"),
            warm=str(tmp_path / "warm"),
            scratch=str(tmp_path / "scratch"),
        ),
        encoding="utf-8",
    )
    for directory in ("hot", "warm", "scratch"):
        (tmp_path / directory).mkdir()
    (tmp_path / "scratch" / "out").mkdir()
    (tmp_path / "warm" / "out").mkdir()
    return tmp_path


@pytest.fixture
def manager(project_dir: Path):
    sys.path.insert(0, str(project_dir))
    mcp_root = str(DATA_IO_MCP_SRC)
    if mcp_root not in sys.path:
        sys.path.insert(0, mcp_root)
    from data_io_mcp.context import activate_project

    return activate_project(project_dir)


def test_check_manifest(manager) -> None:
    from data_io_mcp.registry import build_manifest_report

    report = build_manifest_report(manager)
    assert report["healthy"] is False
    assert report["failure_count"] >= 1
    assert any(t["name"] == "scratch" for t in report["tiers"])
    names = {d["name"] for d in report["datasets"]}
    assert "sample_jsonl" in names
    assert "sample_parquet" in names


def test_list_datasets_prefix(manager) -> None:
    from data_io_mcp.registry import list_datasets

    all_rows = list_datasets(manager)
    assert len(all_rows) == 3
    filtered = list_datasets(manager, prefix="sample_json")
    assert len(filtered) == 2
    assert all(r["logical_name"].startswith("sample_json") for r in filtered)


def test_resolve_dataset(manager, project_dir: Path) -> None:
    from data_io.jsonl_io import save_semi_structured
    from data_io_mcp.registry import resolve_dataset_info

    save_semi_structured(
        [{"id": 1}],
        logical_name="sample_jsonl",
        script="test_data_io_mcp.py",
    )
    info = resolve_dataset_info(manager, "sample_jsonl")
    assert info["exists"] is True
    assert info["resolved_path"].endswith("sample.jsonl")


def test_preview_jsonl(manager, project_dir: Path) -> None:
    from data_io.jsonl_io import save_semi_structured
    from data_io_mcp.preview import preview_dataset

    save_semi_structured(
        [{"id": 1, "text": "hello"}, {"id": 2, "text": "world"}],
        logical_name="sample_jsonl",
        script="test_data_io_mcp.py",
    )
    preview = preview_dataset(manager, "sample_jsonl", limit=1)
    assert preview["available"] is True
    assert preview["format"] == "jsonl"
    assert preview["record_count"] == 2
    assert len(preview["sample_rows"]) == 1


def test_preview_parquet(manager, project_dir: Path) -> None:
    from data_io.parquet_io import save_parquet
    from data_io_mcp.preview import preview_dataset

    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    save_parquet(df, logical_name="sample_parquet", script="test_data_io_mcp.py")
    preview = preview_dataset(manager, "sample_parquet", limit=2)
    assert preview["available"] is True
    assert preview["format"] == "parquet"
    assert preview["shape"] == [3, 2]
    assert len(preview["sample_rows"]) == 2


def test_preview_json(manager, project_dir: Path) -> None:
    from data_io_mcp.preview import preview_dataset

    path = project_dir / "scratch" / "out" / "sample.json"
    path.write_text(
        json.dumps({"transition_counts": [{"from": "Holland", "to": "Zeeland", "count": 3}]}),
        encoding="utf-8",
    )
    preview = preview_dataset(manager, "sample_json", limit=5)
    assert preview["available"] is True
    assert preview["format"] == "json"
    assert preview["sample_from_key"] == "transition_counts"
    assert len(preview["sample_rows"]) == 1


def test_get_provenance_chain(manager, project_dir: Path) -> None:
    from data_io.jsonl_io import save_semi_structured
    from data_io_mcp.provenance_chain import get_provenance_chain

    save_semi_structured(
        [{"id": 1}],
        logical_name="sample_jsonl",
        parent_sources=["sample_parent"],
        script="test_data_io_mcp.py",
    )
    chain = get_provenance_chain(manager, "sample_jsonl")
    assert chain["logical_name"] == "sample_jsonl"
    assert len(chain["chain"]) >= 1
    first = chain["chain"][0]
    assert first["logical_name"] == "sample_jsonl"
    assert first["sidecar"] is not None
    assert first["sidecar"]["logical_name"] == "sample_jsonl"


def test_suggest_manifest_entry() -> None:
    from data_io_mcp.suggest import suggest_manifest_entry

    snippet = suggest_manifest_entry(
        "my_output",
        "analysis/my_output.jsonl",
        tier="scratch",
        phase="semi",
        description="Exploratory export",
        parent="my_input",
    )
    assert "[datasets.my_output]" in snippet
    assert 'path = "analysis/my_output.jsonl"' in snippet
    assert 'parent = "my_input"' in snippet
    assert "data_io.check" in snippet
