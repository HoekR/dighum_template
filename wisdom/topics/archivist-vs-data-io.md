# data_io vs llm_archivist

**Status:** stable  
**Applies to:** all DH projects  
**Portable:** yes

## Rule

| Tool | When | LLM? |
|------|------|------|
| **`data_io.save_*`** | All **new** pipeline outputs | No — deterministic sidecars |
| **`archive-inventory`** | Fast triage of orphan / legacy folders | No |
| **`archive-scan`** | Rich `.meta.toml` for unmigrated legacy files | Yes (Ollama) |

**Never** run archivist tools on files already written by `data_io` (sidecars already exist).

## Workflow for inbox dumps

1. `archive-inventory /path/to/_inbox` — columns, row counts, coverage
2. Read `INVENTORY.md` at scan root
3. Register canonical files in `data_manifest.toml`
4. Optional: `archive-scan` for LLM-rich descriptions
