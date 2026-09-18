### workflow-mcp

Optional Cursor MCP server for cost-sensitive step workflow. Prefer MCP over reading whole `PLAN.md` / all step files:

- `get_plan_status()` — parsed checklist from `PLAN.md`
- `get_current_step()` — first incomplete step
- `list_steps()` — `plans/steps/STEP*.md` index (fallback: `docs/steps/`)
- `get_step_guide(step_id)` — one step guide only (e.g. `3a`)
- `get_workflow_rules()` — `docs/wisdom/cost-sensitive-agent-workflow.md` if present
- `get_iteration_advice(concern_id)` — stage gates / attempt budgets / interlocks (needs `plans/iteration.toml`)
- `record_iteration_attempt(concern_id, outcome)` — append to `plans/iteration_log.jsonl` (does **not** tick PLAN)
- `get_iteration_config()` — effective iteration.toml

Setup: see `docs/addons/workflow-mcp/README.md`. Requires an optional sibling clone of [dighum_template](https://github.com/HoekR/dighum_template) for the server package (not vendored — no code replication). Still follow **one step per chat**; MCP does not replace human progress ticks in `PLAN.md`. Before retrying the same iterative concern, call `get_iteration_advice`. See wisdom `iteration-decision-framework`.
