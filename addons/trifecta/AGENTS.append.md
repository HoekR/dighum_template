### TRIFECTA add-on

Read **`docs/addons/trifecta/README.md`** and **`docs/TRIFECTA.md`** (add from reference repo if needed).

- Pipeline steps **A → B → C**; early dropout on Step A.
- **Structured outputs only** (`instructor` + Pydantic) — no free-text frame labels in production code.
- **Era = provenance** on records, not separate code paths.
- Keep TRIFECTA logic in this repo — do not add frame code to `hist-text-utils`.
