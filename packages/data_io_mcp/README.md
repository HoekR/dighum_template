# data_io MCP server

FastMCP server exposing manifest-backed dataset registry to Cursor agents.

## Install (once)

```bash
cd packages/data_io_mcp && uv sync
```

## Cursor config

Add to your **project's** `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "data-io": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/path/to/dighum_template/packages/data_io_mcp",
        "data-io-mcp",
        "--project-root", "${workspaceFolder}"
      ]
    }
  }
}
```

Or apply the `data-io-mcp` add-on for `.cursor/mcp.json.example`.

## Tools

- `check_manifest()` — tiers + datasets with availability
- `list_datasets(prefix?)` — filtered registry
- `resolve_dataset(logical_name)` — path resolution
- `preview_dataset(logical_name, limit=10)` — capped schema/sample
- `get_provenance(logical_name)` — sidecar + parent chain
- `suggest_manifest_entry(...)` — draft TOML snippet

## Environment

| Variable | Purpose |
|----------|---------|
| `DATA_IO_PROJECT_ROOT` | Override project root (alternative to `--project-root`) |

## Tests

```bash
cd packages/data_io_mcp && uv run pytest ../../tests/test_data_io_mcp.py -v
```

## Project requirements

Target project must have:

- `data_manifest.toml` at root
- Vendored `data_io/` package (from bootstrap)
