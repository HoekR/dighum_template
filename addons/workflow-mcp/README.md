# workflow-mcp add-on

Optional overlay for multi-step DH projects using `PLAN.md` + `plans/steps/`.

Copies:

- `docs/addons/workflow-mcp/README.md` — setup and tool reference
- `.cursor/mcp.json.example` — MCP server stub (merge with `data-io` if both apply)

Apply:

```bash
~/develop/dighum_template/scripts/apply_addon.sh ~/develop/my-project workflow-mcp
```

## Optional dependency: dighum_template

The MCP server lives in [dighum_template](https://github.com/HoekR/dighum_template) `packages/workflow_mcp/` — **not** copied into derivatives. Clone dighum once as a sibling; this add-on only copies config and docs. Skip entirely if you do not use Cursor MCP.
