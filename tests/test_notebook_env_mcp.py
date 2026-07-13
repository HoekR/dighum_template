"""Tests for notebook_env_mcp discovery and metadata helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from notebook_env_mcp.discover import find_project_root, recommend_for_path, scan_venvs
from notebook_env_mcp.kernels import register_kernel_command
from notebook_env_mcp.notebook_meta import inspect_notebook, update_notebook_kernel


@pytest.fixture
def mini_project(tmp_path: Path) -> Path:
    project = tmp_path / "demo-project"
    project.mkdir()
    (project / "pyproject.toml").write_text("[project]\nname = 'demo'\n")
    venv = project / ".venv" / "bin"
    venv.mkdir(parents=True)
    python = venv / "python"
    python.write_text("#!/bin/sh\n")
    python.chmod(0o755)

    notebooks = project / "notebooks"
    notebooks.mkdir()
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "old-conda",
                "language": "python",
                "name": "python3",
            }
        },
        "cells": [],
    }
    (notebooks / "test.ipynb").write_text(json.dumps(nb))
    return project


def test_find_project_root(mini_project: Path) -> None:
    nb = mini_project / "notebooks" / "test.ipynb"
    assert find_project_root(nb) == mini_project


def test_recommend_for_path(mini_project: Path) -> None:
    nb = mini_project / "notebooks" / "test.ipynb"
    result = recommend_for_path(nb)
    assert result["project_name"] == "demo-project"
    assert result["recommended"]["alive"] is True
    assert result["recommended"]["venv_path"].endswith(".venv")


def test_scan_venvs(mini_project: Path) -> None:
    rows = scan_venvs(mini_project)
    assert len(rows) == 1
    assert rows[0]["project_name"] == "demo-project"


def test_register_kernel_command(mini_project: Path) -> None:
    cmd = register_kernel_command(mini_project)
    assert "uv sync" in cmd
    assert "ipykernel install" in cmd
    assert "demo-project" in cmd


def test_update_notebook_kernel(mini_project: Path) -> None:
    nb_path = mini_project / "notebooks" / "test.ipynb"
    before = inspect_notebook(nb_path)
    assert before["metadata"]["kernelspec"]["display_name"] == "old-conda"

    result = update_notebook_kernel(
        nb_path,
        kernel_name="demo-project",
        display_name="demo-project (uv)",
        language_version="3.12.0",
    )
    assert result["updated"] is True
    after = inspect_notebook(nb_path)
    assert after["metadata"]["kernelspec"]["display_name"] == "demo-project (uv)"
