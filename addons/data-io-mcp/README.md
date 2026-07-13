# data_io MCP add-on

Exposes manifest-backed dataset registry to Cursor via MCP — same governed API as `data_io.check`, `resolve`, and provenance sidecars.

## Adds to your project

- `docs/addons/data-io-mcp/README.md` — setup and tool reference
- `.cursor/mcp.json.example` — copy to `.cursor/mcp.json` and edit paths
- Appended section in `AGENTS.md`

## MCP package location

The server package lives in **dighum_template**:

`~/develop/dighum_template/packages/data_io_mcp`

It is not vendored into each project; point `--project-root` at your DH project (which must already have `data_io/` and `data_manifest.toml`).

## Apply

```bash
~/develop/dighum_template/scripts/apply_addon.sh ~/develop/my-project data-io-mcp
```

Then configure `.cursor/mcp.json` per `docs/addons/data-io-mcp/README.md`.
