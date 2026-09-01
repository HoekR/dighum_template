### data-io-mcp

Optional Cursor MCP server for manifest registry access. Prefer MCP tools over raw filesystem reads:

- `check_manifest()` — tier mounts + dataset availability
- `list_datasets(prefix?)` — filter logical names
- `resolve_dataset(name)` — path + exists
- `preview_dataset(name, limit=10)` — schema/sample only (never full wide tables)
- `get_provenance(name)` — sidecar + parent chain
- `suggest_manifest_entry(...)` — draft `[datasets.*]` TOML for human commit

Setup: see `docs/addons/data-io-mcp/README.md`. Requires an optional sibling clone of [dighum_template](https://github.com/HoekR/dighum_template) for the server package (not vendored — no code replication). Still run `uv run python -m data_io.check` in CI and before sessions.
