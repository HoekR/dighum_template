# DH project template (client files)

These files are copied into each new project by `scripts/bootstrap.sh`.

Full guide: [docs/NEW_REPO.md](../docs/NEW_REPO.md) in the `dighum_template` repo.

## Setup (after bootstrap)

```bash
uv sync
cp data_manifest.toml.example data_manifest.toml   # if not already created
# edit tier roots and datasets
uv run python -m data_io.check
```

Open with the workspace profile:

```bash
cursor <package-name>.code-workspace
```

## For LLM / Cursor agents

Read **`AGENTS.md`** first — path rules, provenance writes, and the manifest workflow.

Also loaded automatically:

- **`.cursor/rules/project-standards.mdc`** — uv, manifest, pandas conventions
- **`.cursorrules`** — short manifest discipline

## Layout

```
├── AGENTS.md
├── PROJECT_NAME.code-workspace       # renamed at bootstrap
├── .vscode/
├── .cursor/rules/project-standards.mdc
├── .cursorrules
├── data_manifest.toml
├── data_io/                          # copied from dighum_template/packages/data_io
├── llm_archivist/                    # copied from llm-archivist at bootstrap
├── docs/DATA.md
├── PLAN.md
└── scripts/
```
