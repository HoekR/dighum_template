# How to start a new DH repo

Step-by-step guide for bootstrapping a historical-data pipeline project with manifest-based paths, provenance, and a Cursor/VS Code profile.

**Prerequisite:** clone [dighum_template](../) under `~/develop/`.

Optional: clone [llm-archivist](../../llm-archivist) only if you need legacy file inventory (`--with-archivist`).

For **search/browse webapps** (e.g. RAA), use sibling [`dighum_web_template`](../../dighum_web_template) and see [PLAN-raa-modernized.md](../plans/PLAN-raa-modernized.md).

---

## 1. Bootstrap the repo

From `dighum_template`:

```bash
cd ~/develop/dighum_template
./scripts/bootstrap.sh ~/develop/MyNewProject my-new-project
# with optional layers:
./scripts/bootstrap.sh ~/develop/MyNewProject my-new-project --addon rpp --with-wisdom
./scripts/bootstrap.sh ~/develop/MyNewProject my-new-project --with-archivist
```

Arguments:

1. **Target directory** — must not exist or must be empty
2. **Python package name** (optional) — defaults to the folder name, lowercased with hyphens

**Options:**

| Flag | Effect |
|------|--------|
| `--addon <name>` | Apply specialized overlay (`rpp`, `trifecta`) — repeatable |
| `--with-wisdom` | Copy portable wisdom topics into `docs/wisdom/` |
| `--with-archivist` | Copy `llm_archivist` + inbox scripts (requires sibling `llm-archivist` repo) |

```bash
./scripts/bootstrap.sh ~/develop/MyNewProject my-new-project --addon rpp --with-wisdom
./scripts/bootstrap.sh ~/develop/MyNewProject my-new-project --addon trifecta --addon rpp
```

Apply add-ons or wisdom to an **existing** project:

```bash
./scripts/apply_addon.sh ~/develop/MyNewProject rpp
./scripts/copy_wisdom.sh ~/develop/MyNewProject
```

See [addons/README.md](../addons/README.md) and [wisdom/INDEX.md](../wisdom/INDEX.md).

Override archivist source if needed:

```bash
LLM_ARCHIVIST_SRC=~/develop/llm-archivist/src/llm_archivist \
  ./scripts/bootstrap.sh ~/develop/MyNewProject my-new-project --with-archivist
```

### What you get

| Layer | Files |
|-------|-------|
| **Agent workflow** | `AGENTS.md`, `PLAN.md`, `.cursor/rules/`, `.github/copilot-instructions.md` |
| **Editor profile** | `.vscode/settings.json`, `.vscode/extensions.json`, `<package-name>.code-workspace` |
| **Data governance** | `data_manifest.toml`, `data_io/`, `docs/DATA.md` |
| **Workspaces** | `notebooks/` (Jupyter), `output/` (local scratch fallback, gitignored) |
| **Optional: archivist** | `llm_archivist/`, inbox scripts (with `--with-archivist`) |
| **Optional: wisdom** | `docs/wisdom/` (with `--with-wisdom`) |
| **Optional: add-ons** | Extra rules/docs under `docs/addons/`, `.cursor/rules/` (with `--addon`) |
| **Tests** | `tests/test_data_io.py`; archivist tests when `--with-archivist` |

---

## 2. Install and validate

Bootstrap already ran `uv sync` and installed the Jupyter kernel for the new venv.

Edit `data_manifest.toml`:

1. Set tier roots (`hot`, `warm`, `scratch`) for your machine
2. Add `[datasets.*]` entries for inputs and planned outputs
3. Copy `data_manifest.local.toml.example` → `data_manifest.local.toml` for machine-specific overrides (gitignored)

When the scratch drive is unplugged, override the scratch tier locally:

```toml
# data_manifest.local.toml
[tiers.scratch]
root = "./output"
mount_check = ""
```

Validate:

```bash
uv run python -m data_io.check
uv run pytest tests/ -q
```

---

## 3. Open with the workspace profile

Open the generated workspace file in Cursor or VS Code:

```bash
cursor ~/develop/MyNewProject/my-new-project.code-workspace
```

This loads Python interpreter (`.venv`), lint/test defaults, file excludes, Jupyter notebook root (`notebooks/`), and recommended extensions.

---

## 4. Customize for your domain

Keep the **generic** template rules; add project-specific guidance in these files:

| File | Customize |
|------|-----------|
| `AGENTS.md` | Domain docs, sibling repos, naming — **canonical** agent brief for both editors |
| `PLAN.md` | Headlines: milestones checklist, dataset table |
| `plans/` | Empty `milestones/` + `steps/` skeleton; add guides when multi-step |
| `docs/DATA.md` | Tier layout, canonical sources, phase policy |
| `.cursor/rules/` / `.github/copilot-instructions.md` | Keep generic (regenerate from `template/shared/agent-standards.md`) |
| `data_manifest.toml` | All datasets your pipeline reads/writes |

Optional: add domain docs under `docs/` (e.g. `DATA_LINEAGE.md`, `CALCULATIONS_INDEX.md`).

### Example first agent prompt

```
Read AGENTS.md and PLAN.md.
Add [datasets.my_output] to data_manifest.toml.
Implement scripts/extract.py using save_semi_structured.
Run uv run python -m data_io.check when done.
```

---

## 5. Document legacy / orphan data (optional)

Requires `--with-archivist` at bootstrap (or a manual `llm_archivist/` copy).

```bash
# Fast — no Ollama (columns, row counts, coverage)
uv run archive-inventory ./output/_inbox

# Optional — LLM-rich sidecars (requires Ollama at localhost:11434)
uv run archive-scan ./output/_inbox --model qwen2.5-coder:latest
```

Read `INVENTORY.md` at the scan root; register canonical files in `data_manifest.toml`.

**Do not** run archivist tools on files written by `save_semi_structured` / `save_parquet`.

---

## 6. Initialize git

```bash
git init
git add .
git commit -m "Bootstrap DH data manifest project"
```

Ensure large data, `.venv/`, `output/`, and `data_manifest.local.toml` stay out of version control (`.gitignore` is preconfigured).

---

## 7. Sync updates from the template

Bootstrap runs once. For existing projects, use **`sync_project.sh`** — full guide: **[SYNC-PROJECT.md](SYNC-PROJECT.md)**.

```bash
cd ~/develop/dighum_template

# Preview:
./scripts/sync_project.sh ~/develop/MyNewProject --dry-run --all

# Apply safe updates (data_io, wisdom, editor rules, applied add-ons, MCP deps):
./scripts/sync_project.sh ~/develop/MyNewProject --all
```

Then in the project: `uv run python -m data_io.check` and `uv run pytest tests/ -q`.

**Maintainers:** refresh dighum's vendored `data_io` first when upstream changes:

```bash
cd ~/develop/dighum_template && ./scripts/sync_data_io.sh
./scripts/sync_project.sh ~/develop/MyNewProject --data-io
```

**Manual merge** still required for `AGENTS.md` (base), `pyproject.toml`, `data_manifest.toml`, `PLAN.md` / `plans/`, and domain code. MCP server packages stay in dighum_template (optional sibling) — `--mcp` only runs `uv sync` there.

With archivist installed, sync `llm_archivist/` manually:

```bash
rsync -a ~/develop/llm-archivist/src/llm_archivist/ ~/develop/MyNewProject/llm_archivist/
```

---

## Reference repos

| Repo | Notes |
|------|-------|
| [gnb_analysis](../../gnb_analysis) | Full DH profile + RPP domain rules |
| [trifecta-annotation](../../trifecta-annotation) | TRIFECTA pipeline + structured LLM outputs |
| [republic_ner_matching](../../republic_ner_matching) | NER matching; live `data_io` development |

See also [SKELETON.md](SKELETON.md) for the provenance model and LLM workflow details.
