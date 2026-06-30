# Add-on template

Copy `addons/_template/` to `addons/<your-addon>/` and customize.

Required files:

- `addon.toml` — copy paths and metadata
- `README.md` — what this add-on adds and when to use it

Optional:

- `AGENTS.append.md` — domain instructions merged into project `AGENTS.md`
- `.cursor/rules/*.mdc` — extra Cursor rules
- `docs/addons/<name>/` — domain documentation
- `data_manifest.snippet.toml` — example manifest entries (manual merge)

Test:

```bash
TMP=$(mktemp -d)
./scripts/bootstrap.sh "$TMP/proj" test-proj
./scripts/apply_addon.sh "$TMP/proj" my-addon
```
