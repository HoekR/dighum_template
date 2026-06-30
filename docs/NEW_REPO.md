# How to start a new DH repo

Step-by-step guide for bootstrapping a historical-data pipeline project with manifest-based paths, provenance, and a Cursor/VS Code profile.

**Prerequisite:** clone these repos under `~/develop/`:

| Repo | Purpose |
|------|---------|
| [dighum_template](../) | Bootstrap script + project template |
| [llm-archivist](../../llm-archivist) | Legacy file inventory / archival scan |

---

## 1. Bootstrap the repo

From `dighum_template`:

```bash
cd ~/develop/dighum_template
./scripts/bootstrap.sh ~/develop/MyNewProject my-new-project
# with optional layers:
./scripts/bootstrap.sh ~/develop/MyNewProject my-new-project --addon rpp --with-wisdom
```

Arguments:

1. **Target directory** — must not exist or must be empty
2. **Python package name** (optional) — defaults to the folder name, lowercased with hyphens

**Options:**

| Flag | Effect |
|------|--------|
| `--addon <name>` | Apply specialized overlay (`rpp`, `trifecta`) — repeatable |
| `--with-wisdom` | Copy portable wisdom topics into `docs/wisdom/` |

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
  ./scripts/bootstrap.sh ~/develop/MyNewProject my-new-project
```

### What you get

| Layer | Files |
|-------|-------|
| **Agent workflow** | `AGENTS.md`, `PLAN.md`, `.cursorrules`, `.cursor/rules/project-standards.mdc` |
| **Editor profile** | `.vscode/settings.json`, `.vscode/extensions.json`, `<package-name>.code-workspace` |
| **Data governance** | `data_manifest.toml`, `data_io/`, `llm_archivist/`, `docs/DATA.md` |
| **Optional: wisdom** | `docs/wisdom/` (with `--with-wisdom`) |
| **Optional: add-ons** | Extra rules/docs under `docs/addons/`, `.cursor/rules/` (with `--addon`) |
| **Scripts** | `scripts/archive_inbox.sh`, `scripts/inventory_inbox.sh` |
| **Tests** | `tests/test_data_io.py`, archivist tests |

---

## 2. Install and validate

```bash
cd ~/develop/MyNewProject
uv sync
```

Edit `data_manifest.toml`:

1. Set tier roots (`hot`, `warm`, `scratch`) for your machine
2. Add `[datasets.*]` entries for inputs and planned outputs
3. Copy `data_manifest.local.toml.example` → `data_manifest.local.toml` for machine-specific overrides (gitignored)

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

This loads Python interpreter (`.venv`), lint/test defaults, file excludes, and recommended extensions.

---

## 4. Customize for your domain

Keep the **generic** template rules; add project-specific guidance in these files:

| File | Customize |
|------|-----------|
| `AGENTS.md` | Domain docs to read, sibling repos, naming conventions |
| `PLAN.md` | Milestones, dataset table, current phase |
| `docs/DATA.md` | Tier layout, canonical sources, phase policy |
| `.cursor/rules/project-standards.mdc` | Domain pipeline rules (append or replace generic sections) |
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

## 5. Document legacy / orphan data

For existing files without `data_io` sidecars (inbox dumps, old exports):

```bash
# Fast — no Ollama (columns, row counts, coverage)
uv run archive-inventory /path/to/scratch/_inbox

# Optional — LLM-rich sidecars (requires Ollama at localhost:11434)
uv run archive-scan /path/to/folder --model qwen2.5-coder:latest
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

Ensure large data, `.venv/`, and `data_manifest.local.toml` stay out of version control (`.gitignore` is preconfigured).

---

## 7. Sync updates from the template

When `data_io` or `llm_archivist` change upstream:

```bash
# From dighum_template maintainers — refresh vendored data_io first:
cd ~/develop/dighum_template && ./scripts/sync_data_io.sh

# Into your project:
rsync -a ~/develop/dighum_template/packages/data_io/ ~/develop/MyNewProject/data_io/
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
