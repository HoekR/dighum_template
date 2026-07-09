"""Tests for paper_figures style addon (run from dighum_template root)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ADDON = Path(__file__).resolve().parents[1] / "addons" / "paper-figures"
sys.path.insert(0, str(ADDON))

pytest.importorskip("matplotlib")

from paper_figures import (  # noqa: E402
    apply_style,
    list_palettes,
    list_presets,
    register_palette,
)
from paper_figures.palettes import Palette  # noqa: E402


def test_builtin_presets_and_palettes():
    assert "paper" in list_presets()
    assert "slide" in list_presets()
    assert "print" in list_presets()
    assert "republic_provinces" in list_palettes()


def test_apply_style_paper(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    style = apply_style("paper", output_base=str(tmp_path / "out"))
    assert style.name == "paper"
    assert style.save_ext == "jpg"
    assert style.color("Holland") == "#56B4E9"
    assert style.figsize(10, 5) == (10.0, 5.0)


def test_custom_palette_registration():
    register_palette(
        Palette(name="test_two", order=["A", "B"], colors={"A": "#111111", "B": "#222222"}),
        replace=True,
    )
    style = apply_style("paper", palette="test_two")
    assert style.color("A") == "#111111"
