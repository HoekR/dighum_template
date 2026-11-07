# Agent instructions — DH data project

Read this file, `docs/DATA.md`, and `PLAN.md` before writing pipeline code.

## Data paths (strict)

- **Never** hardcode absolute paths (`/Users/...`, `/Volumes/...`) in Python scripts.
- **Always** register datasets in `data_manifest.toml` first, then use:
  ```python
  from data_io import resolve, load, save_semi_structured, save_parquet
  ```
- **Always** run after manifest or tier changes:
  ```bash
  uv run python -m data_io.check
  ```

## Output writes (strict)

- Phase 1–2 (explore / semi): `save_semi_structured(..., logical_name="...", script=__file__)`
- Phase 3 (frozen): `save_parquet(df, logical_name="...", script=__file__)`
- Never write pipeline outputs without sidecar provenance (`data_io` does this automatically).

## Legacy / orphan files — `llm_archivist` (optional)

Available when the project was bootstrapped with `--with-archivist` (or `llm_archivist/` was added manually). For **existing** files without `data_io` sidecars (inbox dumps, old exports):

```bash
# Fast — no Ollama (columns, coverage, row counts)
uv run archive-inventory /path/to/folder

# LLM — rich description (requires Ollama at localhost:11434)
uv run archive-scan /path/to/folder --model qwen2.5-coder:latest
```

- Profiles `.parquet`, `.csv`, `.xlsx`, `.ipynb` → `filename.meta.toml`
- Use on `output/_inbox/` or migrated legacy data — **not** on `data_io` outputs
- After inventory, read **`INVENTORY.md`** at the scan root; add canonical files to `data_manifest.toml`

| Tool | When | Sidecar | LLM? |
|------|------|---------|------|
| `data_io.save_*` | New pipeline outputs | `.meta.toml` / `.parquet.meta.json` | No |
| `archive-inventory` | Fast orphan triage | `.meta.toml` (`inventory_mode = "fast"`) | No |
| `archive-scan` | Rich archival context | `.meta.toml` | Yes |

## Before adding a dataset

1. Add `[datasets.<logical_name>]` to `data_manifest.toml` (tier, path, phase, description, parent).
2. Run `data_io.check`.
3. Only then reference `logical_name` in code.

## Archival integrity

- Do not drop metadata fields from domain records when transforming.
- Do not mutate canonical reference files in place; write versioned outputs.
- Promote JSONL → Parquet only when schema is stable for one review cycle.

## Session workflow

1. One active step per session — never “execute the whole plan”.
2. **Claims gate (when Living Project State / `svz` is present):** before a PLAN step, eval loop, or changing the research question, run `uv run python scripts/svz.py gate`. On FAIL, stop and patch claims (`claim open|close`) — do not reinterpret quietly under the same id. See wisdom [claims-and-eval-gate](../../wisdom/topics/claims-and-eval-gate.md).
3. Read `PLAN.md` first; if multi-step, follow `plans/steps/STEP*.md` (see wisdom [cost-sensitive-agent-workflow](../../wisdom/topics/cost-sensitive-agent-workflow.md)). Prefer advising commands; user runs the terminal by default.
4. Update `PLAN.md` when a step is done (checklist) and when manifest datasets change. Keep PLAN as **headlines only** — outcomes and wrong-track kills live in `docs/claims.jsonl`, not chat.
5. After a step: short handoff + next step; clear the chat before starting the next step.
6. (Recommended) `uv run python -m data_io.check` before new pipeline work.
7. Smoke test: `uv run python -c "from data_io import resolve; print(resolve('...'))"`

## Claims, eval, and exploration (strict when `svz` is present)

- **New research question → new claim id** (`svz.py claim open …`). Same id may only continue under an explicit `interpretation_id` bump; never silent narrative drift.
- **Wrong track:** `claim close --status dead_for_this_q` (or `deferred`) with `--evidence` and `--consequence`; optionally `--clear-active`. Do not delete history. Gate failing after a kill is correct until the next claim exists.
- **Exploration** stays in **notebooks** (heatmaps, distributions, sequence graphs). Notebooks and “grid finished” are **not** ship/placement authority.
- Eval reports need **two verdicts:** Process (ops/reproducible run) vs Product (pre-registered quality threshold on a named stratum). Never treat Process green as Product permission.

## Editors (Cursor, VS Code, Claude Code)

This file is the **canonical** agent brief. The same non-negotiables are copied into:

| Editor | File |
|--------|------|
| Cursor | `.cursor/rules/project-standards.mdc` (`alwaysApply`) |
| VS Code Copilot | `.github/copilot-instructions.md` |
| Claude Code | `CLAUDE.md` |

Do not edit those generated files by hand in a bootstrapped repo unless you keep all of them in sync. Domain extras go here (and in add-on `.cursor/rules/` + the `## Add-ons` section below).

## Optional: data_io MCP (Cursor)

When the `data-io-mcp` add-on is applied, prefer MCP tools (`check_manifest`, `list_datasets`, `preview_dataset`) over raw filesystem reads. See `docs/addons/data-io-mcp/README.md`.

## Common mistakes (avoid)

| Wrong | Right |
|-------|-------|
| `pd.read_parquet("/Volumes/...")` | `load("resolutions_flat")` |
| `open("data/out.jsonl", "w")` | `save_semi_structured(rows, logical_name="...")` |
| `archive-scan` on `data_io` outputs | Only scan legacy/orphan folders |
| New path in code only | New `[datasets.*]` entry + `data_io.check` |

## Wisdom and add-ons

- **Wisdom** (cross-project lessons): `docs/wisdom/` if bootstrapped with `--with-wisdom`, else `~/develop/dighum_template/wisdom/INDEX.md`
- **Add-ons** (domain overlays): see `docs/addons/APPLIED.md` and extra `.cursor/rules/*` (Cursor) plus this file’s `## Add-ons` section (all editors)
- Apply later: `~/develop/dighum_template/scripts/apply_addon.sh <this-repo> <name>`
