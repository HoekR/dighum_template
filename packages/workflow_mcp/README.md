# workflow MCP server

FastMCP server exposing `PLAN.md` progress and `docs/steps/` guides to Cursor agents.

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
- `list_steps()` — files under `docs/steps/`
- `get_step_guide(step_id)` — read `STEP*.md` for one step
- `get_workflow_rules()` — cost-sensitive workflow wisdom (if copied to project)

## Environment

| Variable | Purpose |
|----------|---------|
| `WORKFLOW_PROJECT_ROOT` | Override project root (alternative to `--project-root`) |

## Tests

```bash
cd packages/workflow_mcp && uv run pytest ../../tests/test_workflow_mcp.py -v
```

## Project requirements

Target project must have:

- `PLAN.md` with a progress checklist table at root
- `AGENTS.md` at root
- Step guides in `docs/steps/STEP*.md` (recommended)
