# TRIFECTA annotation

Multi-stage LLM pipeline for semantic frame annotation of historical food texts.

## Pipeline

1. **Step A** — classify / filter (early dropout if not food-related)
2. **Step B** — frame discovery
3. **Step C** — structured annotation record

## Rules

- Use `instructor` + Pydantic for all production outputs
- Era is a **provenance field**, not a separate pipeline fork
- Optional KWIC helpers from `hist-text-utils` — keep that repo generic

## Reference

- `trifecta-annotation` repo: `docs/TRIFECTA.md`, `PLAN.md`
- CLI pattern: `uv run trifecta-batch`, `uv run trifecta-eval`
