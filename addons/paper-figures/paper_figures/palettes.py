"""Built-in and user-registered color palettes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

# Okabe-Ito — colorblind-safe (from GNB_artikel/paper_figures.ipynb)
REPUBLIC_PROVINCE_COLORS: dict[str, str] = {
    "Gelderland": "#E69F00",
    "Holland": "#56B4E9",
    "Zeeland": "#009E73",
    "Utrecht": "#F0E442",
    "Friesland": "#0072B2",
    "Overijssel": "#D55E00",
    "Groningen": "#CC79A7",
}

REPUBLIC_PROVINCE_ORDER: list[str] = list(REPUBLIC_PROVINCE_COLORS.keys())

REPUBLIC_PROVINCE_HATCHES: dict[str, str] = {
    "Gelderland": "///",
    "Holland": "\\\\",
    "Zeeland": "|||",
    "Utrecht": "---",
    "Friesland": "+++",
    "Overijssel": "xxx",
    "Groningen": "...",
}

# Back-compat aliases used in notebooks
PROVINCE_COLORS = REPUBLIC_PROVINCE_COLORS
PROVINCE_ORDER = REPUBLIC_PROVINCE_ORDER


@dataclass(frozen=True)
class Palette:
    """Named province (or category) palette for figure styling."""

    name: str
    order: list[str]
    colors: dict[str, str]
    hatches: dict[str, str] = field(default_factory=dict)
    fallback: str = "#888888"

    def color(self, key: str | None) -> str:
        if not key:
            return self.fallback
        return self.colors.get(key, self.fallback)

    def ordered_colors(self) -> list[str]:
        return [self.color(p) for p in self.order]


_REGISTRY: dict[str, Palette] = {}


def _register_builtin_palettes() -> None:
    register_palette(
        Palette(
            name="republic_provinces",
            order=REPUBLIC_PROVINCE_ORDER,
            colors=REPUBLIC_PROVINCE_COLORS,
            hatches=REPUBLIC_PROVINCE_HATCHES,
        )
    )


def register_palette(palette: Palette, *, replace: bool = False) -> None:
    """Register a palette for use via ``apply_style(palette=...)``."""
    if palette.name in _REGISTRY and not replace:
        raise ValueError(f"Palette already registered: {palette.name!r} (pass replace=True)")
    _REGISTRY[palette.name] = palette


def get_palette(name: str) -> Palette:
    if name not in _REGISTRY:
        known = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise KeyError(f"Unknown palette {name!r}. Registered: {known}")
    return _REGISTRY[name]


def list_palettes() -> list[str]:
    return sorted(_REGISTRY)


def palette_from_mapping(
    name: str,
    colors: dict[str, str],
    *,
    order: list[str] | None = None,
    hatches: dict[str, str] | None = None,
    fallback: str = "#888888",
) -> Palette:
    """Build and register a palette from a plain dict (extension hook)."""
    pal = Palette(
        name=name,
        order=order or list(colors.keys()),
        colors=colors,
        hatches=hatches or {},
        fallback=fallback,
    )
    register_palette(pal, replace=True)
    return pal


_register_builtin_palettes()
