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
| [data-io-mcp](topics/data-io-mcp.md) | Cursor MCP for manifest registry, previews, provenance |
| [workflow-mcp](topics/workflow-mcp.md) | Cursor MCP for PLAN.md progress and plans/steps guides |
| [cost-sensitive-agent-workflow](topics/cost-sensitive-agent-workflow.md) | Step-by-step plans, doc split, user-run terminal, model tiers |
| [iteration-decision-framework](topics/iteration-decision-framework.md) | Stage gates, attempt budgets, interlocks; orchestrator advise/record |
| [iteration-policy](topics/iteration-policy.md) | Track choice via `svz review`; compose with orchestrator concerns |
| [macos-batch-execution-power](topics/macos-batch-execution-power.md) | Prevent macOS E-core downclocking & SSD sleep via `caffeinate -dims` |
| [llm-pipeline-batching-strategy](topics/llm-pipeline-batching-strategy.md) | Staged batching (Step A dropout $\rightarrow$ SLM filter $\rightarrow$ HPC scale) |

## Journal (recent)

| Month | Notes |
|-------|-------|
| [2026-09](journal/2026-09.md) | Iteration framework + svz review / track policy |
| [2026-08](journal/2026-08.md) | Cost-sensitive agent workflow (wvo_corr pilot) |
| [2026-06](journal/2026-06.md) | Template repo, addons, wisdom layer |

## By project type

| Type | Read first |
|------|------------|
| Any new DH repo | manifest-discipline, provenance-fields, archivist-vs-data-io, data-io-mcp |
| Existing derivative (dighum updates) | dighum `docs/SYNC-PROJECT.md` + `sync_project.sh` |
| Multi-step / Bayesian / pub pipeline | cost-sensitive-agent-workflow, workflow-mcp, iteration-decision-framework, iteration-policy |
| Republic attendance / RPP | pattern-authority, pandas-pre-1678-dates, observable-framework-bridge |
| LLM annotation | vectorized-pandas + addon `trifecta` |
