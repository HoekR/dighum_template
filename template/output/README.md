# Local output (scratch fallback)

Pipeline data normally lives on the **scratch tier** (external drive). When that drive is unavailable, override the tier root locally:

```bash
cp data_manifest.local.toml.example data_manifest.local.toml
# Uncomment the [tiers.scratch] block → root = "./output"
```

`data_io` then writes scratch-tier datasets under this directory. The folder is gitignored.

Legacy orphan files (pre-manifest inbox dumps) can go in `output/_inbox/` for `archive-inventory` / `archive-scan` when `llm_archivist` is installed (`--with-archivist` at bootstrap).
