# Paper figures add-on

Configurable matplotlib styling extracted from **`GNB_artikel/paper_figures.ipynb`**.

## Adds to your project

| Path | Purpose |
|------|---------|
| `paper_figures/` | Python package (`apply_style`, palettes, presets) |
| `figure_style.example.toml` | Copy → `figure_style.toml` at repo root |
| `.cursor/rules/paper-figures-standards.mdc` | Agent guidance for plots |

## Dependencies

Merge into `pyproject.toml`:

```toml
dependencies = [
    "matplotlib>=3.8",
]
```

Optional: `seaborn` (presets use `seaborn-v0_8-white` style sheet).

Register package in `[tool.setuptools.packages.find]`:

```toml
include = [..., "paper_figures"]
```

## Quick use

```python
from paper_figures import apply_style

style = apply_style()  # reads ./figure_style.toml if present
fig, ax = plt.subplots(figsize=style.figsize(12, 5))
colors = [style.color(p) for p in df["province"]]
style.save(fig, "deputy_attendance_bars")
print(style.summary())
```

## Configuration

Project root **`figure_style.toml`** overrides bundled defaults:

```toml
[preset]
name = "paper"   # slide | paper | print

[palette]
name = "republic_provinces"

[output]
base = "figures"
```

### Inline custom palette

```toml
[palette]
register_as = "my_study"
order = ["A", "B", "C"]
colors = { A = "#E69F00", B = "#56B4E9", C = "#009E73" }
```

### Local overrides (gitignored)

```toml
[[extensions]]
path = "figure_style.local.toml"
```

## Extending in code

```python
from paper_figures import register_palette, register_preset
from paper_figures.palettes import Palette
from paper_figures.presets import StylePreset

register_palette(Palette(name="admiralties", order=[...], colors={...}))
register_preset(StylePreset(name="poster", matplotlib_style="...", ...))
style = apply_style(preset="poster", palette="admiralties")
```

## Presets

| Preset | Background | DPI | Format | Notes |
|--------|------------|-----|--------|-------|
| `slide` | dark | 150 | png | Large fonts, `FIG_SCALE=1.4` |
| `paper` | white | 300 | jpg | Journal submission default |
| `print` | white | 300 | pdf | Province hatches for B&W |

## Source

`~/GNB_artikel/paper_figures.ipynb` — maintain styling here in `dighum_template`, not in the legacy notebook.
