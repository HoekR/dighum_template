# dighum_template

Template repository for bootstrapping **digital humanities data pipeline** projects with:

- manifest-based data paths (`data_manifest.toml` + `data_io`)
- provenance sidecars on all pipeline writes
- optional legacy file inventory (`llm_archivist` via `--with-archivist`)
- Living Project State (`docs/state.json`, `docs/STATE.md`, `docs/DECISIONS.md`, dashboard notebooks, `scripts/svz.py`)
- Cursor/VS Code workspace profile (`.vscode/`, `.code-workspace`, `.cursor/rules/`, `.github/copilot-instructions.md`)
- plan-step executor custom agent (`.github/agents/plan-step-executor.agent.md`) for one bounded workflow step per chat
- **`wisdom/`** — accumulated cross-project lessons (grows over time)
- **`addons/`** — optional specialized overlays (RPP, TRIFECTA, …)

**This repo is not a pipeline itself** — it is the source you copy from when starting a new project.

## Quick start (new project)

```bash
cd ~/develop/dighum_template
./scripts/bootstrap.sh ~/develop/MyNewProject my-new-project
# optional layers:
./scripts/bootstrap.sh ~/develop/MyNewProject my-new-project --addon rpp --with-wisdom
./scripts/bootstrap.sh ~/develop/MyNewProject my-new-project --with-archivist   # needs llm-archivist sibling
```

Full guide: **[docs/NEW_REPO.md](docs/NEW_REPO.md)**

## Repository layout

```
dighum_template/
├── docs/NEW_REPO.md          # how to start a new repo
├── docs/SKELETON.md          # provenance model + LLM workflow
├── docs/SYNC-PROJECT.md      # sync updates into derivatives
├── plans/                    # maintainer plans (not copied into projects)
├── wisdom/                   # accumulated wisdom (topics + journal)
│   ├── INDEX.md
│   └── topics/
├── addons/                   # optional domain overlays (rpp, trifecta, paper-figures, …)
│   ├── rpp/
│   └── trifecta/
├── scripts/
│   ├── bootstrap.sh          # create a new project
│   ├── sync_project.sh       # sync updates into existing derivative
│   ├── update_project.sh     # add/update Living Project State in a derivative
│   ├── apply_addon.sh        # add overlay to existing project
│   ├── copy_wisdom.sh        # copy portable wisdom topics
│   ├── sync_editor_rules.sh  # Cursor + Copilot rules from shared source
│   └── sync_data_io.sh       # refresh packages/data_io (maintainers)
├── packages/
│   ├── data_io/              # vendored into each project
│   ├── data_io_mcp/          # Cursor MCP (stays in dighum)
│   ├── workflow_mcp/         # PLAN.md + plans/steps MCP
│   └── notebook_env_mcp/
├── template/                 # base files copied into each new project
│   ├── README.md             # PROJECT_NAME substituted at bootstrap
│   ├── PLAN.md               # headlines only
│   ├── plans/                # empty milestones/ + steps/ (fill on demand)
│   ├── 00_project_dashboard.ipynb
│   ├── tasks/                # reusable task overview notebooks
│   └── shared/               # not copied; source for editor rules
└── tests/
```

## Wisdom and add-ons

| Layer | Purpose | When |
|-------|---------|------|
| **`wisdom/topics/`** | Durable rules that transfer across repos | Read anytime; `--with-wisdom` at bootstrap |
| **`wisdom/journal/`** | Dated discoveries and session notes | Append as you learn |
| **`addons/<name>/`** | Domain-specific rules, docs, cursor rules | `--addon` at bootstrap or `apply_addon.sh` later |
| **`scripts/sync_project.sh`** | Push template updates into existing derivatives | After dighum changes — [docs/SYNC-PROJECT.md](docs/SYNC-PROJECT.md) |

Catalog: [addons/README.md](addons/README.md) · Index: [wisdom/INDEX.md](wisdom/INDEX.md)

## Maintaining the template

`data_io` is developed in `republic_ner_matching`; refresh the vendored copy:

```bash
./scripts/sync_data_io.sh
```

**Push updates into derivative projects:** [docs/SYNC-PROJECT.md](docs/SYNC-PROJECT.md)

```bash
./scripts/sync_project.sh ~/develop/my-project --all
./scripts/sync_project.sh ~/develop/my-project --agents
./scripts/update_project.sh ~/develop/my-project --dry-run
```

New projects include the plan-step executor automatically. The `--agents` form
adds missing template custom agents to an existing project without overwriting
local agent customizations.

After editing `template/`, `wisdom/`, or `addons/`, test:

```bash
TMP=$(mktemp -d)
./scripts/bootstrap.sh "$TMP/test" test-project --addon rpp --with-wisdom
test ! -e "$TMP/test/README.md.template"
test ! -e "$TMP/test/shared"
test -f "$TMP/test/.github/copilot-instructions.md"
test -f "$TMP/test/.github/agents/plan-step-executor.agent.md"
```

## Reference projects

| Project | Notes |
|---------|-------|
| [gnb_analysis](../gnb_analysis) | RPP pipeline — use `--addon rpp` as starting point |
| [trifecta-annotation](../trifecta-annotation) | TRIFECTA — use `--addon trifecta` |
| [republic_ner_matching](../republic_ner_matching) | NER matching; `data_io` development source |

## Deprecated path

Bootstrap via `republic_ner_matching/scripts/bootstrap_dh_project.sh` forwards to this repo when present.
