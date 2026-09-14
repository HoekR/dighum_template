# PROJECT_NAME

DH data pipeline with manifest-based paths (`data_manifest.toml` + `data_io`).

## Setup

```bash
# Bootstrap already ran `uv sync` and installed the Jupyter kernel.
# Re-run `uv sync` if you later change dependencies.
# edit data_manifest.toml — tier roots and [datasets.*]
# optional when scratch drive is unplugged:
cp data_manifest.local.toml.example data_manifest.local.toml
# Data registry view (manifest-declared datasets + on-disk status)
uv run python -m data_io.check
```

Open the workspace profile in Cursor or VS Code:

```bash
cursor PROJECT_NAME.code-workspace
# or: code PROJECT_NAME.code-workspace
```

## Layout

| Path | Role |
|------|------|
| `AGENTS.md` | Agent instructions (Cursor and VS Code Copilot) |
| `PLAN.md` | Headlines checklist and dataset table (create `plans/` on demand) |
| `docs/DATA.md` | Tiers, phases, manifest workflow |
| `data_manifest.toml` | Tier roots and registered datasets |
| `notebooks/` | Jupyter workspace (explore phase) |
| `output/` | Local scratch-tier fallback (gitignored; see `output/README.md`) |
| `data_io/` | Manifest I/O and provenance helpers |

## Agents (Cursor / VS Code)

Read **`AGENTS.md`** first. The same standards load from:

- Cursor: `.cursor/rules/project-standards.mdc`
- VS Code Copilot: `.github/copilot-instructions.md`
