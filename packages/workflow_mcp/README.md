# workflow MCP server

FastMCP server exposing `PLAN.md` progress, `plans/steps/` guides, and optional **iteration advice** to Cursor agents.

## Install (once)

```bash
cd packages/workflow_mcp && uv sync
```

## Cursor config

Add to your **project's** `.cursor/mcp.json` (merge with other servers such as `data-io`):

```json
{
  "mcpServers": {
    "workflow": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/path/to/dighum_template/packages/workflow_mcp",
        "workflow-mcp",
        "--project-root", "${workspaceFolder}"
      ]
    }
  }
}
```

Or apply the `workflow-mcp` add-on for `.cursor/mcp.json.example`.

## Optional dependency for derivatives

Server code stays in [dighum_template](https://github.com/HoekR/dighum_template) — not vendored into each project (no replication). Derivatives clone dighum as an optional sibling and point `.cursor/mcp.json` here; the add-on copies only config and docs.

## Tools

- `get_plan_status()` — parsed PLAN.md checklist
- `get_current_step()` — first incomplete step
- `list_steps()` — files under `plans/steps/` (fallback: `docs/steps/`)
- `get_step_guide(step_id)` — read `STEP*.md` for one step
- `get_workflow_rules()` — cost-sensitive workflow wisdom (if copied to project)
- `get_iteration_advice(concern_id)` — stage gates / budgets / interlocks (`plans/iteration.toml`)
- `record_iteration_attempt(concern_id, outcome, note="")` — append `plans/iteration_log.jsonl` only
- `get_iteration_config()` — effective iteration.toml

**Contract:** iteration tools never tick `PLAN.md`. Human progress ticks remain authoritative.

## CLI orchestrator

```bash
uv run --directory packages/workflow_mcp workflow-orchestrator advise \
  --project-root /path/to/project --concern metric_chase

uv run --directory packages/workflow_mcp workflow-orchestrator record \
  --project-root /path/to/project --concern metric_chase \
  --outcome no_gain --note "same metric, no unlock"

uv run --directory packages/workflow_mcp workflow-orchestrator show-config \
  --project-root /path/to/project
```

Example config: [`examples/iteration.toml`](examples/iteration.toml) → copy to project `plans/iteration.toml`.

Wisdom: `wisdom/topics/iteration-decision-framework.md`.
For **which track next** (metric trends), use project `scripts/svz.py review` — see `wisdom/topics/iteration-policy.md`.

## Environment

| Variable | Purpose |
|----------|---------|
| `WORKFLOW_PROJECT_ROOT` | Override project root (alternative to `--project-root`) |

## Tests

```bash
cd packages/workflow_mcp && uv run pytest ../../tests/test_workflow_mcp.py ../../tests/test_iteration_orchestrator.py -v
```

## Project requirements

Target project must have:

- `PLAN.md` with a progress checklist table at root
- `AGENTS.md` at root
- Step guides in `plans/steps/STEP*.md` when multi-step (create on demand; legacy `docs/steps/` still works)
- Optional: `plans/iteration.toml` for iteration advice
