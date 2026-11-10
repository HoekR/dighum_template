# Add-ons

Optional **specialized overlays** copied on top of the base template — domain rules, extra docs, cursor rules, manifest snippets.

## Available add-ons

| Add-on | Purpose | Apply |
|--------|---------|-------|
| **`rpp`** | Relative Proportional Presence (Republic delegate attendance) | `--addon rpp` |
| **`paper-figures`** | Matplotlib slide/paper/print styles (GNB article palette) | `--addon paper-figures` |
| **`trifecta`** | TRIFECTA structured LLM frame annotation | `--addon trifecta` |
| **`data-io-mcp`** | Cursor MCP for `data_io` manifest registry + previews | `apply_addon.sh` |
| **`workflow-mcp`** | Cursor MCP for `PLAN.md` progress + `plans/steps/` guides | `apply_addon.sh` |
| **`_template`** | Scaffold for authoring a new add-on | (maintainers only) |

List installed add-ons in the target project: `docs/addons/APPLIED.md` (created on apply).

## MCP add-ons and dighum_template

**`data-io-mcp`** and **`workflow-mcp`** do not copy server code into derivatives. They require an optional sibling clone of [dighum_template](https://github.com/HoekR/dighum_template) (`packages/data_io_mcp/`, `packages/workflow_mcp/`). The add-on overlay copies only `.cursor/mcp.json` stub, docs, and an `AGENTS.md` snippet — no replication of shared tooling. Pipeline runtime (`data_io/`, etc.) is still vendored at bootstrap. Skip MCP add-ons if you do not use Cursor MCP.

**Refresh add-on docs** after dighum changes: `./scripts/sync_project.sh <project> --addons` or `--addon workflow-mcp` — see [docs/SYNC-PROJECT.md](../docs/SYNC-PROJECT.md).

## At bootstrap

```bash
./scripts/bootstrap.sh ~/develop/MyProject my-project --addon rpp --with-wisdom
./scripts/bootstrap.sh ~/develop/MyProject my-project --addon trifecta --addon rpp
```

## On an existing project

```bash
./scripts/apply_addon.sh ~/develop/MyProject rpp
./scripts/apply_addon.sh ~/develop/MyProject trifecta
```

## Add-on layout

Each add-on is a folder under `addons/<name>/`:

```
addons/rpp/
├── addon.toml              # metadata (name, title, copy globs)
├── README.md               # human description (this add-on's docs)
├── AGENTS.append.md        # appended to project AGENTS.md
├── .cursor/rules/          # extra Cursor rules (also summarized in AGENTS.md for VS Code)
└── docs/addons/rpp/        # optional domain docs copied into project
```

### Authoring a new add-on

1. Copy `addons/_template/` → `addons/my-addon/`
2. Edit `addon.toml`, `README.md`, rules, and docs
3. Test: `./scripts/apply_addon.sh $(mktemp -d)/test my-addon` after a dry bootstrap
4. Register in this README table

Keep add-ons **orthogonal** — they should merge cleanly in any combination. Put shared rules in `wisdom/topics/` instead.
