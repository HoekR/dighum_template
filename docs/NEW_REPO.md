# How to start a new DH repo

Step-by-step guide for bootstrapping a historical-data pipeline project with manifest-based paths, provenance, and a Cursor/VS Code profile.

**Prerequisite:** clone [dighum_template](../) under `~/develop/`.

Optional: clone [llm-archivist](../../llm-archivist) only if you need legacy file inventory (`--with-archivist`).

For **search/browse webapps** (e.g. RAA), use sibling [`dighum_web_template`](../../dighum_web_template) and see [PLAN-raa-modernized.md](PLAN-raa-modernized.md).

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
| `PLAN.md` | Milestones, dataset table, current phase |
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

When `data_io` changes upstream:

```bash
# From dighum_template maintainers — refresh vendored data_io first:
cd ~/develop/dighum_template && ./scripts/sync_data_io.sh

# Into your project:
rsync -a ~/develop/dighum_template/packages/data_io/ ~/develop/MyNewProject/data_io/
```

With archivist installed, also sync:

```bash
rsync -a ~/develop/llm-archivist/src/llm_archivist/ ~/develop/MyNewProject/llm_archivist/
```

Re-run `uv run python -m data_io.check` and tests after syncing.

To pick up template file changes (AGENTS.md, `.cursor/rules/`, etc.), compare `dighum_template/template/` with your repo and merge manually — bootstrap only runs on empty directories.

---

## Reference repos

| Repo | Notes |
|------|-------|
| [gnb_analysis](../../gnb_analysis) | Full DH profile + RPP domain rules |
| [trifecta-annotation](../../trifecta-annotation) | TRIFECTA pipeline + structured LLM outputs |
| [republic_ner_matching](../../republic_ner_matching) | NER matching; live `data_io` development |

See also [SKELETON.md](SKELETON.md) for the provenance model and LLM workflow details.
