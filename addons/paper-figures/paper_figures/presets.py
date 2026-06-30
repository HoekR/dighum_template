"""Built-in style presets (slide / paper / print)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

StylePresetName = str


@dataclass(frozen=True)
class StylePreset:
    """Matplotlib rcParams bundle for a output target."""

    name: str
    matplotlib_style: str
    rcparams: dict[str, Any] = field(default_factory=dict)
    fig_scale: float = 1.0
    save_ext: str = "png"
    save_dpi: int = 150
    dark: bool = False
    cmap_background: str = "#f8f8f8"


_REGISTRY: dict[str, StylePreset] = {}


def register_preset(preset: StylePreset, *, replace: bool = False) -> None:
    if preset.name in _REGISTRY and not replace:
        raise ValueError(f"Preset already registered: {preset.name!r} (pass replace=True)")
    _REGISTRY[preset.name] = preset


def get_preset(name: str) -> StylePreset:
    if name not in _REGISTRY:
        known = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise KeyError(f"Unknown preset {name!r}. Registered: {known}")
    return _REGISTRY[name]


def list_presets() -> list[str]:
    return sorted(_REGISTRY)


def _register_builtin_presets() -> None:
    register_preset(
        StylePreset(
            name="slide",
            matplotlib_style="dark_background",
            dark=True,
            cmap_background="#1a1a1a",
            fig_scale=1.4,
            save_ext="png",
            save_dpi=150,
            rcparams={
                "font.family": "sans-serif",
                "font.size": 14,
                "axes.titlesize": 20,
                "axes.labelsize": 14,
                "xtick.labelsize": 12,
                "ytick.labelsize": 12,
                "axes.facecolor": "#1a1a1a",
                "figure.facecolor": "black",
                "axes.edgecolor": "#888888",
                "grid.color": "#333333",
                "text.color": "white",
                "xtick.color": "white",
                "ytick.color": "white",
                "figure.dpi": 150,
                "savefig.dpi": 150,
                "savefig.bbox": "tight",
                "savefig.facecolor": "black",
            },
        )
    )
    _paper_rc = {
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 10,
        "axes.titlesize": 13,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    }
    register_preset(
        StylePreset(
            name="paper",
            matplotlib_style="seaborn-v0_8-white",
            fig_scale=1.0,
            save_ext="jpg",
            save_dpi=300,
            rcparams=_paper_rc,
        )
    )
    register_preset(
        StylePreset(
            name="print",
            matplotlib_style="seaborn-v0_8-white",
            fig_scale=1.0,
            save_ext="pdf",
            save_dpi=300,
            rcparams={**_paper_rc, "hatch.linewidth": 0.6},
        )
    )


_register_builtin_presets()
