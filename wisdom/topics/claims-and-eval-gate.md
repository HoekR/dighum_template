# Claims ledger and eval gatekeeper

**Status:** stable (v1)  
**Applies to:** DH projects with Living Project State (`scripts/svz.py`, `docs/state.json`)  
**Portable:** yes  
**Origin:** eval-strategy discussion (republic_sittings / multi-repo milestone failures), 2026-11  
**Companion:** [iteration-policy](iteration-policy.md), [iteration-decision-framework](iteration-decision-framework.md), [cost-sensitive-agent-workflow](cost-sensitive-agent-workflow.md)

## Problem

Agents are weak at bookkeeping: **context is a peephole**, incentives favour a coherent *next turn*, and long `PLAN.md` / metric dumps drown the one active question. Eval milestones drift when conclusions live only in chat.

## Rule

Keep a **thin claims table**. Make agents pass a **mechanical gate** before continuing work. Explore in notebooks; conclude in one claim line.

```text
svz review / iteration advise   → which track / concern?
svz gate                        → is there an active claim with consequence?
notebooks                       → exploration (no ship authority)
claim open|close                → conclusions / wrong-track / defer
```

## Claims schema (`docs/claims.jsonl`)

One JSON object per claim (upsert by `id`):

| Field | Meaning |
|-------|---------|
| `id` | Stable refer-id (e.g. `signal-compare-cohort`) |
| `question` | One sentence — what this claim answers |
| `status` | `open` \| `deferred` \| `answered` \| `dead_for_this_q` |
| `evidence` | Path to report/sheet/SETUP (required when closed) |
| `consequence` | What we do/stop doing given the outcome |
| `supersedes` | Optional prior claim id |
| `interpretation_id` | Optional cheap-loop freeze label |
| `updated` | ISO date |

`docs/state.json` holds `active_claim_id` (nullable). **`docs/STATE.md` mirrors only the active claim** — not the full ledger.

### Status meanings

| Status | Use |
|--------|-----|
| `open` | Working this question |
| `answered` | Usable yes/no with evidence |
| `deferred` | Right idea, wrong time |
| `dead_for_this_q` | Wrong track for this question — keep the row |

## Gatekeeper

```bash
uv run python scripts/svz.py gate    # exit 1 if no valid active claim
uv run python scripts/svz.py doctor  # schema + informational gate
```

**Pass** when `active_claim_id` points at a claim with non-empty `question` and `consequence`; closed statuses also need `evidence`.

**Fail** after a kill with `--clear-active` until a new claim is opened — that pause is intentional.

## Wrong track

1. `claim close <id> --status dead_for_this_q --evidence … --consequence "Stop …"`  
2. Optionally `--clear-active` (park).  
3. If the next question is known: `claim open <new> --supersedes <old> …`.  
4. Do **not** delete history; do **not** reuse `answered` for quitting.

## Exploration vs conclusion

| Layer | Where |
|-------|--------|
| Exploration | **Notebooks** (heatmaps, distributions, sequence graphs) |
| Frozen glance | Optional `output/` sheet/HTML tied to a claim |
| Conclusion | One claims line; STATE shows active only |

## Eval report dual verdict

Every eval SETUP/report should separate:

| Verdict | Means |
|---------|--------|
| **Process** | Run finished / cache / scripts reproducible |
| **Product** | Pre-registered quality threshold on a **named stratum** |

Process green alone must not authorise placement or PRINCIPLES changes.

## Cheap loops

Before retrying the same concern: freeze definitions (`interpretation_id`). A cheap loop may change **one** of code-bug / slice / threshold — not the story. Max a few smokes, then escalate to a registered claim close (`answered` / `dead_for_this_q` / `deferred`).

## CLI sketch

```bash
uv run python scripts/svz.py claim open my-q \
  --question "…" --consequence "…" --sync-focus
uv run python scripts/svz.py gate
# … work / notebooks …
uv run python scripts/svz.py claim close my-q \
  --status dead_for_this_q --evidence output/report.md \
  --consequence "Stop expanding this grid" --clear-active
```

## Relation to tracks / concerns

| Layer | Artefact |
|-------|----------|
| Tracks | `state.json` tasks + `svz review` |
| Concerns | `plans/iteration.toml` + orchestrator |
| **Claims** | `claims.jsonl` + `svz gate` |

Do not collapse them: tracks choose the line of work; concerns budget polish; **claims hold what we decided and what follows**.
