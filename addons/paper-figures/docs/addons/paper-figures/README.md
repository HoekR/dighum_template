# Paper figure styling

Extracted from **`GNB_artikel/paper_figures.ipynb`**. Configure via **`figure_style.toml`** at repo root (copy from `figure_style.example.toml`).

## Usage

```python
from paper_figures import apply_style

style = apply_style()  # preset + palette from figure_style.toml
fig, ax = plt.subplots(figsize=style.figsize(12, 5))
ax.bar(labels, values, color=[style.color(p) for p in provinces])
style.save(fig, "my_figure")
```

## Presets

| Name | Use |
|------|-----|
| `slide` | Presentations — dark background, 150 dpi PNG |
| `paper` | Journal — white, 300 dpi JPG |
| `print` | B&W-safe PDF with province hatches |

## Palette

Default **`republic_provinces`**: Okabe-Ito colors for the seven provinces (Gelderland → Groningen).

Register custom palettes in code or inline in `figure_style.toml` — see addon README in dighum_template.

## Output

Figures save under `figures/<preset>/` by default (e.g. `figures/paper/`).

## Do not

- Hardcode province hex colors in plot scripts — use `style.color(province)`
- Mix ad-hoc `plt.rcParams` with `apply_style()` in the same notebook without resetting
