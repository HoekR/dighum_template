"""Configurable matplotlib styles for DH paper figures."""

from paper_figures.config import load_config, merge_config
from paper_figures.palettes import (
    PROVINCE_COLORS,
    PROVINCE_ORDER,
    get_palette,
    list_palettes,
    register_palette,
)
from paper_figures.presets import list_presets, register_preset
from paper_figures.style import FigureStyle, apply_style, province_color

__all__ = [
    "FigureStyle",
    "PROVINCE_COLORS",
    "PROVINCE_ORDER",
    "apply_style",
    "get_palette",
    "list_palettes",
    "list_presets",
    "load_config",
    "merge_config",
    "province_color",
    "register_palette",
    "register_preset",
]
