# data_io MCP add-on

Exposes manifest-backed dataset registry to Cursor via MCP — same governed API as `data_io.check`, `resolve`, and provenance sidecars.

## Adds to your project

- `docs/addons/data-io-mcp/README.md` — setup and tool reference
- `.cursor/mcp.json.example` — copy to `.cursor/mcp.json` and edit paths
- Appended section in `AGENTS.md`

## Optional dependency: dighum_template

The MCP server lives in [dighum_template](https://github.com/HoekR/dighum_template) `packages/data_io_mcp/` — **not** copied into derivatives. Clone dighum once as a sibling; this add-on only copies config and docs. Vendored `data_io/` in the project is separate (runtime). Skip entirely if you do not use Cursor MCP.

## Apply

```bash
~/develop/dighum_template/scripts/apply_addon.sh ~/develop/my-project data-io-mcp
```

Then configure `.cursor/mcp.json` per `docs/addons/data-io-mcp/README.md`.
