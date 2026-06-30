### paper-figures add-on

For publication figures, use **`paper_figures`** (from `figure_style.toml`):

```python
from paper_figures import apply_style
style = apply_style()
```

- Province colors: `style.color(province)` — do not hardcode hex values
- Sizes: `style.figsize(w, h)`, fonts: `style.fontsize(n)`
- Save: `style.save(fig, "stem")` → `figures/<preset>/stem.<ext>`
- Presets: `slide` | `paper` | `print` — set in `figure_style.toml`

See `docs/addons/paper-figures/README.md`.
