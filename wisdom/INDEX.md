# Wisdom index

Start here for cross-project DH pipeline knowledge. See [README.md](README.md) for how to contribute.

## Topics (durable)

| Topic | Summary |
|-------|---------|
| [pandas-pre-1678-dates](topics/pandas-pre-1678-dates.md) | Use `pd.Period`, not `datetime`, before 1678 |
| [manifest-discipline](topics/manifest-discipline.md) | Register datasets before code; no hardcoded paths |
| [local-config-not-env](topics/local-config-not-env.md) | Credentials in gitignored `*.local.toml`, not env vars |
| [provenance-fields](topics/provenance-fields.md) | Never drop metadata when transforming records |
| [pattern-authority](topics/pattern-authority.md) | One canonical pattern source; flag gaps, don't invent |
| [vectorized-pandas](topics/vectorized-pandas.md) | No row loops; no `inplace=True` |
| [notebook-generation-hygiene](topics/notebook-generation-hygiene.md) | Generate notebooks via scripts; avoid hand-editing JSON |
| [archivist-vs-data-io](topics/archivist-vs-data-io.md) | When to use `data_io` vs `archive-scan` |
| [paper-figure-style](topics/paper-figure-style.md) | Use `paper-figures` add-on for matplotlib |
| [observable-framework-bridge](topics/observable-framework-bridge.md) | Deferred plan: Observable Framework dashboard + MCP wired via `bridge.toml` |

## Journal (recent)

| Month | Notes |
|-------|-------|
| [2026-06](journal/2026-06.md) | Template repo, addons, wisdom layer |

## By project type

| Type | Read first |
|------|------------|
| Any new DH repo | manifest-discipline, provenance-fields, archivist-vs-data-io |
| Republic attendance / RPP | pattern-authority, pandas-pre-1678-dates, observable-framework-bridge |
| LLM annotation | vectorized-pandas + addon `trifecta` |
