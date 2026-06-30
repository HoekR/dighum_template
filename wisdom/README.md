# Accumulated wisdom

Durable lessons from DH pipeline work — **not** project-specific PLAN status, but knowledge that transfers across repos.

## How to use

| Audience | Action |
|----------|--------|
| **New project** | Bootstrap with `--with-wisdom` to copy portable topics into `docs/wisdom/` |
| **Existing project** | Read sibling `~/develop/dighum_template/wisdom/INDEX.md` or copy topics you need |
| **Agent session** | Read `INDEX.md` when stuck on manifest tiers, pandas dates, pattern authority, etc. |

## How to contribute

1. **Durable topic** → add or extend a file under `topics/` (one concern per file)
2. **Session note / discovery** → append to the current month in `journal/YYYY-MM.md`
3. Update **`INDEX.md`** with a one-line summary and link

### Topic file format

```markdown
# Title

**Status:** stable | draft | superseded  
**Applies to:** all DH projects | RPP | TRIFECTA | …  
**Portable:** yes | no   ← if yes, copied by bootstrap --with-wisdom

## Rule
…

## Why
…

## Example
…
```

### When to write wisdom vs project docs

| Write here (`wisdom/`) | Write in project (`docs/`, `AGENTS.md`) |
|------------------------|----------------------------------------|
| Pandas pre-1678 dates | Which parquet is canonical for *this* pipeline |
| Never drop provenance fields | Current milestone in PLAN.md |
| Manifest tier philosophy | Tier root paths on your machine |
| Pattern-join anti-patterns | Join coverage numbers for your run |

## Layout

```
wisdom/
├── INDEX.md           # topic index (start here)
├── topics/            # durable, reusable rules
└── journal/           # dated notes (monthly files)
```
