# RPP (Relative Proportional Presence)

Delegate attendance analysis for Dutch Republic *Staten-Generaal* resolutions.

## Naming

Use **RPP** only in code, manifests, and outputs.

## Pattern authority

Before pipeline work, declare in `AGENTS.md`:

1. **Canonical pattern source** (occurrence-level spelling variants)
2. **Corrected identity source** (person IDs, attendance rows)
3. **QA source** (review only — never pattern authority)

Unmatched rows between identity and patterns → validation flags, not invented backfill.

## Pandas dates

Resolution calendar dates before 1678: `pd.Period` with `freq="D"`. See `docs/wisdom/pandas-pre-1678-dates.md` if present.

## Manifest

Merge example keys from `data_manifest.snippet.toml` in this add-on folder (in dighum_template: `addons/rpp/data_manifest.snippet.toml`).

## Further reading

- `~/develop/dighum_template/wisdom/topics/pattern-authority.md`
- Reference repo: `gnb_analysis` — `docs/DATA_LINEAGE.md`, `docs/PRESIDENTS_18C.md`
