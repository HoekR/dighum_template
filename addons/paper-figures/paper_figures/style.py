"""Apply presets and palettes to matplotlib; save figures consistently."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from paper_figures.config import resolve_config
from paper_figures.palettes import Palette, get_palette, palette_from_mapping
from paper_figures.presets import StylePreset, get_preset

if TYPE_CHECKING:
    from matplotlib.figure import Figure


def _make_cmap(color: str, name: str, *, background: str) -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list(name, [background, color])


@dataclass
class FigureStyle:
    """Active figure style context (returned by ``apply_style``)."""

    name: str
    palette: Palette
    fig_scale: float
    save_ext: str
    save_dpi: int
    output_dir: str
    province_cmaps: dict[str, LinearSegmentedColormap] = field(default_factory=dict)
    use_hatches: bool = False

    @property
    def province_colors(self) -> dict[str, str]:
        return self.palette.colors

    @property
    def province_order(self) -> list[str]:
        return self.palette.order

    @property
    def province_hatches(self) -> dict[str, str]:
        return self.palette.hatches if self.use_hatches else {}

    def figsize(self, width: float, height: float) -> tuple[float, float]:
        return (width * self.fig_scale, height * self.fig_scale)

    def fontsize(self, size: float) -> float:
        return size * self.fig_scale

    def color(self, province: str | None) -> str:
        return self.palette.color(province)

    def save(self, fig: Figure, stem: str, *, subdir: str = "") -> Path:
        out = Path(self.output_dir)
        if subdir:
            out = out / subdir
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{stem}.{self.save_ext}"
        fig.savefig(path, dpi=self.save_dpi, bbox_inches="tight")
        return path

    def summary(self) -> str:
        lines = [
            f"Style: {self.name}  |  Scale: {self.fig_scale}  |  "
            f"DPI: {self.save_dpi}  |  Output: {self.output_dir}/",
            f"Palette: {self.palette.name} ({len(self.palette.order)} keys)",
        ]
        for p in self.palette.order:
            lines.append(f"  {p:12s}  {self.palette.color(p)}")
        return "\n".join(lines)


def _preset_from_config(cfg: dict[str, Any]) -> StylePreset:
    preset_cfg = cfg.get("preset", {})
    name = preset_cfg.get("name", "paper")
    base = get_preset(name)
    overrides = {k: v for k, v in preset_cfg.items() if k != "name"}
    if not overrides:
        return base
    rc = dict(base.rcparams)
    rc.update(overrides.get("rcparams", {}))
    return StylePreset(
        name=base.name,
        matplotlib_style=overrides.get("matplotlib_style", base.matplotlib_style),
        rcparams=rc,
        fig_scale=float(overrides.get("fig_scale", base.fig_scale)),
        save_ext=str(overrides.get("save_ext", base.save_ext)),
        save_dpi=int(overrides.get("save_dpi", base.save_dpi)),
        dark=bool(overrides.get("dark", base.dark)),
        cmap_background=str(overrides.get("cmap_background", base.cmap_background)),
    )


def _palette_from_config(cfg: dict[str, Any]) -> Palette:
    pal_cfg = cfg.get("palette", {})
    name = pal_cfg.get("name", "republic_provinces")
    if "colors" in pal_cfg:
        custom_name = pal_cfg.get("register_as", f"{name}_custom")
        return palette_from_mapping(
            custom_name,
            {str(k): str(v) for k, v in pal_cfg["colors"].items()},
            order=[str(x) for x in pal_cfg.get("order", list(pal_cfg["colors"]))],
            hatches={str(k): str(v) for k, v in pal_cfg.get("hatches", {}).items()},
            fallback=str(pal_cfg.get("fallback", "#888888")),
        )
    return get_palette(name)


def apply_style(
    preset: str | None = None,
    *,
    palette: str | None = None,
    output_base: str | None = None,
    config_path: str | Path | None = None,
    extra_config_paths: list[str | Path] | None = None,
) -> FigureStyle:
    """Apply matplotlib style; return a ``FigureStyle`` context.

    Resolution order:
    1. Bundled ``defaults.toml``
    2. ``config_path`` (default: ``./figure_style.toml`` in cwd if present)
    3. ``extra_config_paths``
    4. Explicit ``preset`` / ``palette`` / ``output_base`` arguments (win over file)
    """
    if config_path is None:
        cwd_cfg = Path("figure_style.toml")
        config_path = cwd_cfg if cwd_cfg.is_file() else None

    cfg = resolve_config(config_path=config_path, extra_paths=extra_config_paths)

    if preset:
        cfg = {**cfg, "preset": {**cfg.get("preset", {}), "name": preset}}
    if palette:
        cfg = {**cfg, "palette": {**cfg.get("palette", {}), "name": palette}}

    preset_obj = _preset_from_config(cfg)
    palette_obj = _palette_from_config(cfg)

    out_cfg = cfg.get("output", {})
    base = output_base or out_cfg.get("base", "figures")
    subdir = out_cfg.get("subdir", preset_obj.name)
    output_dir = str(Path(base) / subdir) if subdir else base

    plt.style.use(preset_obj.matplotlib_style)
    mpl.rcParams.update(preset_obj.rcparams)

    bg = preset_obj.cmap_background
    cmaps = {
        p: _make_cmap(c, p.replace(" ", "_"), background=bg)
        for p, c in palette_obj.colors.items()
    }

    use_hatches = preset_obj.name == "print" and bool(palette_obj.hatches)

    os.makedirs(output_dir, exist_ok=True)

    ctx = FigureStyle(
        name=preset_obj.name,
        palette=palette_obj,
        fig_scale=preset_obj.fig_scale,
        save_ext=preset_obj.save_ext,
        save_dpi=preset_obj.save_dpi,
        output_dir=output_dir,
        province_cmaps=cmaps,
        use_hatches=use_hatches,
    )
    return ctx


def province_color(province: str | None, *, palette: str = "republic_provinces") -> str:
    """Lookup without applying global rcParams."""
    return get_palette(palette).color(province)
