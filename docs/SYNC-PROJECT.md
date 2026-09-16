# Sync updates into derivative projects

Bootstrap runs **once** on an empty directory. To pick up later changes from [dighum_template](https://github.com/HoekR/dighum_template), use **`sync_project.sh`**.

## Quick start

```bash
cd ~/develop/dighum_template

# Preview what would change:
./scripts/sync_project.sh ~/develop/wvo_corr --dry-run --all

# Apply safe, automated updates:
./scripts/sync_project.sh ~/develop/wvo_corr --all
```

Then in the project (when applicable):

```bash
cd ~/develop/wvo_corr
uv run python -m data_io.check   # only after data_io/ exists (post–Step 0 bootstrap)
uv run pytest tests/ -q          # only when tests/ and pyproject.toml exist
```

Pre–Step 0 projects (like `wvo_corr` today) have neither — skip these checks until bootstrap completes Step 0.

## What syncs automatically

| Flag | Action |
|------|--------|
| `--data-io` | `rsync` `dighum_template/packages/data_io/` → project `data_io/` |
| `--wisdom` | Copy portable wisdom topics → `docs/wisdom/` (`copy_wisdom.sh`) |
| `--editor-rules` | Refresh `.cursor/rules/project-standards.mdc` + `.github/copilot-instructions.md` + `CLAUDE.md` |
| `--agents` | Add missing template custom agents under `.github/agents/` (never overwrite local agents) |
| `--state` | Refresh Living Project State helpers (`scripts/svz.py`, dashboard stubs) when missing |
| `--addons` | Re-apply every add-on listed in `docs/addons/APPLIED.md` |
| `--addon NAME` | Re-apply one add-on (repeatable) |
| `--mcp` | `uv sync` MCP packages in dighum_template (`workflow_mcp`, `data_io_mcp`, `notebook_env_mcp`) — not copied into the project |
| `--all` | All of the above |
| `--dry-run` | Print actions only |

## What stays manual

These are project-specific or often customized — **compare and merge by hand** (sync must not clobber them):

| File / area | Why |
|-------------|-----|
| `AGENTS.md` (base) | Domain instructions diverge per repo |
| `AGENTS.md` add-on blocks | Re-apply skips sections that already exist |
| `pyproject.toml` | Extra dependencies per project |
| `data_manifest.toml` | Datasets and tier roots |
| `PLAN.md`, `plans/` | Headlines + on-demand full plans / milestones / steps |
| Domain code, notebooks | Not template files |

To refresh base template files (`template/AGENTS.md`, etc.), diff against `dighum_template/template/` and merge selectively.

## Typical workflows

### After dighum_template changes wisdom or add-on docs

```bash
./scripts/sync_project.sh ~/develop/my-project --wisdom --addons
```

### After `data_io` changes upstream

Maintainers first refresh dighum's vendored copy:

```bash
cd ~/develop/dighum_template && ./scripts/sync_data_io.sh
```

Then into each derivative:

```bash
./scripts/sync_project.sh ~/develop/my-project --data-io
```

### MCP add-ons only

Server code stays in dighum (not vendored). Sync MCP deps + refresh add-on overlay docs:

```bash
./scripts/sync_project.sh ~/develop/my-project --mcp --addon workflow-mcp
```

### With archivist installed

`sync_project.sh` does not sync `llm_archivist/` yet. Manual:

```bash
rsync -a ~/develop/llm-archivist/src/llm_archivist/ ~/develop/my-project/llm_archivist/
```

## Related scripts

| Script | Role |
|--------|------|
| `bootstrap.sh` | Create new project (empty dir only) |
| `apply_addon.sh` | First-time or repeat add-on overlay |
| `copy_wisdom.sh` | Wisdom only (called by `sync_project --wisdom`) |
| `sync_editor_rules.sh` | Editor rules only |
| `sync_data_io.sh` | Refresh `packages/data_io` **in dighum_template** from `republic_ner_matching` |

See also [NEW_REPO.md](NEW_REPO.md) §7 and [addons/README.md](../addons/README.md).
