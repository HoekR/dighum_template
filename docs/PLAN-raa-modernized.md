# RAA Modern Webapp Port Plan

> **Active build track (Option 1):** Phase 0 (`dighum_web_template`) + Milestone B (`raa_modernized` person search slice). See [OPTION-1-BUILD.md](OPTION-1-BUILD.md).

## What you have today

```mermaid
flowchart LR
    subgraph legacy [Legacy stack - discard for runtime]
        Zope[Zope2/Five Product]
        SQLos[SQLObject/SQLos]
        MySQL[(MySQL webraa)]
        PT[Page Templates .pt]
        Zope --> SQLos --> MySQL
        Zope --> PT
    end

    subgraph convert [raa_convert - keep]
        MDB[MS Access .mdb]
        Notebooks[Notebook pipeline]
        extab[extab.pkl / raa_nw]
        MDB --> Notebooks --> extab
    end

    legacy -.->|same schema| convert
```

| Layer | Legacy [`src/raa`](file:///Users/rikhoekstra/develop/RepertoriumAmbtenarenAmbtsdragers/src/raa) | Modern replacement |
|-------|------|-------------------|
| Runtime | Python 2, Zope 2/3, SQLObject | Python 3.12, FastAPI |
| Search store | MySQL + SQLObject queries | **TBD after Milestone B** — Postgres SQL facets (default pilot) or Elasticsearch; see [Search store decision](#search-store-decision) |
| UI | Server-rendered `.pt` templates | SvelteKit with **faceted search** UI |
| Search logic | [`query.py`](file:///Users/rikhoekstra/develop/RepertoriumAmbtenarenAmbtsdragers/src/raa/query.py) + [`form.py`](file:///Users/rikhoekstra/develop/RepertoriumAmbtenarenAmbtsdragers/src/raa/browser/form.py) | Backend-agnostic query builder; legacy wildcard semantics preserved |
| Data source | ETL → MySQL | [`raa_convert`](file:///Users/rikhoekstra/develop/raa_convert) → `extab.pkl` → Postgres import (pilot) or ES index |
| Period model | Not in legacy search UI | **Top-level period facet** + **overall (all-period) search** |

**Data ready for the webapp** ([`raa_convert/extab.pkl`](file:///Users/rikhoekstra/develop/raa_convert/extab.pkl)): 14 tables, ~22k persons, ~54k appointments, ~535 institutions. Schema documented in [`data_definitions.py`](file:///Users/rikhoekstra/develop/raa_convert/data_definitions.py) and validated by [`validate_export.py`](file:///Users/rikhoekstra/develop/raa_convert/validate_export.py).

**Feature surface to replicate** (from [`browser/configure.zcml`](file:///Users/rikhoekstra/develop/RepertoriumAmbtenarenAmbtsdragers/src/raa/browser/configure.zcml)):

- Search/browse: **personen**, **aanstellingen**, **instellingen**, **functies**
- **Period-scoped search** per source period + **overall search** across all periods
- **Faceted search**: period, functie, instelling, provincie, regio, lokaal, stand, adel, titles, date ranges — with live facet counts
- Detail pages: person (aliases, appointments split local/supra-local, bronnen), institution (HTML `toelichting`), appointment, function
- Legacy search capabilities to preserve: wildcard text (`*`/`?`, quoted phrases), multi-select AND/OR, sortable columns, pagination (20), appointment grouping
- Optional later: institution `toelichting` editing (was TinyMCE + Zope admin in legacy) — **Phase 5 editorial layer**

**Do not port:** Zope product wiring, FiveSQLOS traversable containers, SQLObject, bundled TinyMCE 2.x, legacy ETL in `RepertoriumAmbtenarenAmbtsdragers/src/scripts/` (superseded by `raa_convert`).

---

## Phase 0 — `dighum_web_template` (sibling derivative repo)

`dighum_template` should stay **pipeline-only** ([`data_io`](file:///Users/rikhoekstra/develop/dighum_template/packages/data_io/), notebooks, manifests, addons like `rpp`). Web search apps are a different purpose — embedding FastAPI, Postgres, SvelteKit scaffolds inside it would clutter the template.

**Create a separate sibling repo:** `dighum_web_template` — a **derivative** of `dighum_template`, not a folder inside it.

### Repo relationship

```mermaid
flowchart TB
    subgraph upstream [dighum_template - unchanged focus]
        pipeline[data_io pipelines]
        bootstrap[bootstrap.sh]
        addons_rpp[rpp trifecta addons]
    end

    subgraph derivative [dighum_web_template - new sibling repo]
        bootstrap_web[bootstrap_web.sh]
        web_data[web-data overlay]
        web_app[web-app scaffold]
        docs_web[docs/WEB_APP.md]
    end

    subgraph projects [Project repos]
        raa_mod[raa_modernized monorepo]
    end

    bootstrap_web --> raa_mod
    upstream -->|"sync data_io"| derivative
```

| Repo | Role | Stays clean of |
|------|------|----------------|
| **`dighum_template`** | DH pipeline bootstrap | Web stacks, Postgres, SvelteKit |
| **`dighum_web_template`** | Web-app bootstrap derivative | Domain data (RAA, RPP, …) |
| **`raa_modernized`** | RAA monorepo (data + web) | Template maintenance |

`bootstrap_web.sh` supports **`--monorepo`** (default for RAA): one repo with pipeline root + `web/` subfolder, instead of `{name}-data` + `{name}-web` siblings.

### How the derivative stays in sync

- **Vendor `data_io`:** copy or `sync_data_io.sh`-style script pointing at `../dighum_template/packages/data_io`
- **Monorepo mode (`--monorepo`):** bootstrap pipeline root via upstream `bootstrap.sh` into target dir, merge `overlay/web-data/`, copy `template/web-app/` → `web/`
- **Sibling mode (default for generic projects):** creates `{name}-data` + `{name}-web` with `bridge.local.toml`
- **Upstream updates:** periodic re-sync from `dighum_template` main

### Minimal touch on `dighum_template` itself

Only a **pointer**, not web code:

- One paragraph in [`docs/NEW_REPO.md`](file:///Users/rikhoekstra/develop/dighum_template/docs/NEW_REPO.md) or [`addons/README.md`](file:///Users/rikhoekstra/develop/dighum_template/addons/README.md): "For search/browse webapps, use sibling [`dighum_web_template`](../dighum_web_template)"
- Optional portable wisdom topic in `dighum_template/wisdom/topics/web-app-bridge.md` (architecture only, no scaffolds) — or keep all web docs solely in the derivative

### New artifacts in `dighum_web_template`

| Artifact | Purpose |
|----------|---------|
| `scripts/bootstrap_web.sh` | Creates monorepo (`--monorepo`) or sibling `{name}-data` + `{name}-web` |
| `overlay/web-data/` | Files merged into data repo: `scripts/import_release.py` template, manifest snippet |
| `template/web-app/` | FastAPI + `SearchBackend`, SvelteKit stub, `docker-compose.yml`, `bridge.toml.example`, `search_contexts.yaml` |
| `docs/WEB_APP.md` | Bootstrap, bridge wiring, dev stack, deploy |
| `AGENTS.md` / `.cursor/rules/` | Web-app agent standards |
| `README.md` | States derivative relationship + sync instructions |

### Bootstrap command (target UX)

```bash
cd ~/develop/dighum_web_template
./scripts/bootstrap_web.sh ~/develop/raa_modernized raa-modernized --monorepo
# Creates:
#   ~/develop/raa_modernized/     — monorepo: pipeline root + web/ subfolder
```

Requires `dighum_template` as sibling. Optional: `--with-wisdom`, `--addon <name>` for pipeline layer.

### Monorepo layout (`raa_modernized`)

```
raa_modernized/
├── data_io/                 # vendored from dighum_template
├── data_manifest.toml
├── scripts/
│   └── import_release.py    # extab.pkl → Postgres
├── notebooks/
├── web/
│   ├── api/                 # FastAPI + SearchBackend
│   ├── frontend/            # SvelteKit
│   ├── search_contexts.yaml
│   └── docker-compose.yml   # Postgres + API + frontend
├── config.local.toml        # DB URL etc. (gitignored; no cross-repo bridge)
├── pyproject.toml
└── AGENTS.md
```

Pipeline and web share one git repo; `config.local.toml` replaces `bridge.local.toml` (internal paths only).

### Config contract (`config.local.toml`) — monorepo

```toml
[database]
url = "postgresql://localhost/raa_modernized"

[web]
api_port = 8000
frontend_port = 5173

[data]
extab_logical = "raa_extab"   # manifest logical name

# Optional — only if decision gate chooses ES:
# [elasticsearch]
# url = "http://localhost:9200"
```

For **sibling-repo** projects (non-RAA), `bridge.toml` still links separate data + web repos. RAA uses monorepo config only.

### Web scaffold conventions (reusable defaults)

These become the **standard DH web stack** in the derivative — RAA customizes on top:

| Layer | Default choice | Rationale |
|-------|----------------|-----------|
| API | FastAPI + SQLAlchemy 2 + Pydantic | Python 3.12; `SearchBackend` protocol with Postgres impl |
| Data store | PostgreSQL (pilot) | Facets via SQL, editorial-ready, one service |
| Search abstraction | `SearchBackend` protocol | Swap to ES after Milestone B if needed |
| Frontend | SvelteKit + facet sidebar | Backend-agnostic facet UI |
| Dev | `docker compose up` (Postgres + API + frontend) | Simpler than ES for pilot |

**Not in v1 of the derivative:** auth, CMS editing, Observable dashboards (separate bridge doc).

### Relationship to Observable bridge

| Pattern | Repo | Use when |
|---------|------|----------|
| **Pipeline template** | `dighum_template` | Data pipelines, notebooks, MCP |
| **Web-app template** | `dighum_web_template` | Search/browse apps with bridge to data repo |
| **Observable bridge** (deferred) | separate dashboard repo | Exploratory charts only |

---

## Recommended repository model (RAA)

**Single monorepo:** [`raa_modernized`](file:///Users/rikhoekstra/develop/raa_modernized) — bootstrapped via `dighum_web_template/scripts/bootstrap_web.sh --monorepo`.

| Part | Path in repo | Responsibility |
|------|--------------|----------------|
| **Data / pipeline** | repo root | Manifest, `import_release.py`, validation, `data_io` |
| **Web** | `web/` | Search API, RQ-driven UI, deployment |

`raa_convert` stays the **upstream conversion lab**; `raa_modernized` consumes its outputs via manifest (`raa_extab`).

---

## Search store decision

**Status: deferred until after Milestone B.** Build an abstract search layer first; pilot with **PostgreSQL**, keep Elasticsearch as a documented alternative.

### Comparison at RAA scale (~22k persons, ~54k appointments)

| Criterion | PostgreSQL + SQL facets | Elasticsearch |
|-----------|-------------------------|---------------|
| **Facet counts** | `GROUP BY` per dimension (post-filter pattern) — fast at this scale | Native aggregations — very ergonomic |
| **Full-text / wildcards** | `pg_trgm`, `ILIKE`, or app-layer `query.py` port | Strong analyzers, `query_string` |
| **Relational detail pages** | Natural JOINs | Denormalized docs or second lookup |
| **Editorial layer (Phase 5)** | Same database — no sync | Needs Postgres anyway + ES sync |
| **Ops complexity** | One service (already in plan) | ES cluster + index rebuild + sync |
| **Appointment grouping** | SQL `GROUP BY` fits well | `terms` agg — works, less familiar |
| **Re-import on new extab** | Merge into base tables | Reindex from merged export |
| **Scale headroom** | Fine to ~low millions with indexes | Better if 10×+ growth or heavy text search |
| **Debuggability** | SQL you can inspect | JSON queries, mapping tuning |

### Recommendation

For RAA specifically, **PostgreSQL is likely the long-term winner** because Phase 5 editorial storage needs it anyway, the dataset is small, and legacy search maps cleanly to SQL filters. Elasticsearch is worth it if Milestone B shows pain on wildcard name search, facet latency with many concurrent filters, or Dutch text relevance.

### Pilot strategy (your choice: decide later)

```mermaid
flowchart LR
    api[FastAPI SearchService]
    backend[SearchBackend protocol]
    pg[PostgresBackend - pilot]
    es[ElasticsearchBackend - optional]
    api --> backend
    backend --> pg
    backend -.->|if needed| es
```

1. **Milestone B** ships with `PostgresBackend` only — validates data model, facets, period modes, UI
2. **Decision gate** — measure:
   - Person search p95 latency with 3+ active facets
   - Wildcard query correctness vs legacy `query.py` test cases
   - Developer ergonomics (SQL complexity)
3. **Commit** to Postgres (remove ES path) **or** add ES as read projection synced from Postgres

**Do not maintain both in production** — pick one after the gate to avoid permanent dual-sync tax.

### SQL facet pattern (Postgres pilot)

For each facet dimension, run a count query with **all active filters except that dimension** (same semantics as ES `post_filter`):

```sql
-- Example: functie facet counts given current filters
SELECT f.id, f.naam, COUNT(DISTINCT p.id)
FROM persoon p
JOIN aanstelling a ON ...
JOIN functie f ON ...
WHERE <period + text + other facets, NOT functie>
GROUP BY f.id, f.naam
ORDER BY count DESC
LIMIT 50;
```

Period flags: boolean columns per period on base tables, or `period_membership(entity_type, entity_id, period)` junction table.

---

## Architecture target (pilot: PostgreSQL)

```mermaid
flowchart TB
    subgraph raa_convert [raa_convert]
        extab[extab.pkl]
    end

    subgraph raa_modernized [raa_modernized monorepo]
        import[scripts/import_release.py]
        manifest[data_manifest.toml]
        api[web/api FastAPI]
        ui[web/frontend SvelteKit]
        pg[(PostgreSQL)]
        extab --> import --> pg
        manifest --> import
        ui --> api --> pg
    end
```

**Optional ES path (if decision gate chooses it):** Postgres remains canonical; `build_search_index.py` projects to ES for search only; editorial amendments sync to both.

---

## Search model: period division + overall search

### Why period separation exists

Period division serves **two goals**:

1. **Historical coherence** — institutions, offices, and geography differ across eras; mixing them blurs meaning.
2. **Facet / filter clutter reduction** — the main UX reason. A single cross-period index inflates vocabularies: many functies and instellingen only exist in one period. Scoping to e.g. **Republiek** shrinks every filter list and suggest result to **entities that actually occur in that period**, making typeahead, browse A–Z, and small-set checkboxes tractable.

Overall ("Alle perioden") search remains available for **cross-period RQs**, but is the **noisier mode** — users accept broader vocabularies and may need period as an explicit filter to narrow.

**Default:** period-scoped on entry (recommended path); overall is opt-in.

### Period data (from `raa_convert`)

Each export row carries period flags (`1` = included in that period's search), documented in [`CONVERSION_NOTES.md`](file:///Users/rikhoekstra/develop/raa_convert/docs/CONVERSION_NOTES.md):

| Period key | Label (NL) |
|------------|------------|
| `republiek` | Republiek (incl. Friezen — shares `pmap` value; derive `republiek_friezen` at index time where distinguishable) |
| `batfra` | Bataafs-Franse Tijd |
| `negentiende_eeuw` | Negentiende Eeuw |
| `me` | Middeleeuwen |
| `divperioden` | Diverse Perioden |

At index time, convert boolean flags → **`periods: ["republiek", "batfra"]`** keyword array on every document.

### Two search modes (single app)

| Mode | UI | Query behavior | Filter clutter |
|------|-----|----------------|----------------|
| **Period-scoped** (default) | User picks one period from top-level selector | Filter `period = <selected>`; all suggests/browse/lists scoped to that period's entities only | **Low** — primary mode |
| **Overall** | "Alle perioden" in same selector | No period filter; period available as filter to drill down | **High** — opt-in for cross-period RQs |

Period scope applies **globally** to every search context (personen, aanstellingen, …) and to `/api/suggest` and `/api/browse` — not only to main search results.

```mermaid
flowchart LR
    selector[Period selector]
    scoped[Period-scoped - smaller vocabs]
    overall[Overall - full vocabs]
    filters[Filters and suggests]
    results[Results]

    selector -->|default| scoped
    selector -->|Alle perioden| overall
    scoped -->|"functie/instelling lists trimmed"| filters --> results
    overall -->|"full lists; period filter to narrow"| filters --> results
```

### Filters and facets — depends on the research question

There is no single "best" filter layout. A repertorium serves **different research questions (RQ)**; the UI should match **how the user enters the question**, not impose one global facet sidebar.

**Design principle:** keep **four separate search contexts** from the legacy app (personen, aanstellingen, instellingen, functies). Each page exposes **only the filters relevant to that RQ** — configured in `search_contexts.yaml`, not hardcoded tiers.

#### Typical research questions → entry path

| Research question | Start at | Period mode | Why |
|-------------------|----------|-------------|-----|
| "Who held office Y at Z in the **Republiek**?" | `/aanstellingen` | **Scoped** | Smaller functie/instelling vocab |
| "Who was person X?" (any period) | `/personen` | Overall or scoped | Name search; period optional |
| "Compare office holders across periods" | `/aanstellingen` | **Overall** | Cross-period RQ — accepts clutter |
| "What institutions in period P?" | `/instellingen` | **Scoped** | Browse list stays bounded |

Home page (`/`) offers **"Waar wilt u mee beginnen?"** plus period selector — choosing a period first keeps subsequent filters manageable.

```mermaid
flowchart LR
    home[Home]
    personen[Personen - name-led]
    aanst[Aanstellingen - office-led]
    inst[Instellingen - institution-led]
    funct[Functies - function-led]

    home -->|"Wie was...?"| personen
    home -->|"Wie bekleedde...?"| aanst
    home -->|"Welke instelling...?"| inst
    home -->|"Welke functie...?"| funct
```

#### Filter widget types (implementation, not UX driver)

Choose widget **per field per search context** based on cardinality + how users approach that RQ:

| Widget | Use when | Sort / order |
|--------|----------|--------------|
| **Full list** (checkbox) | Small closed set in this context | Alphabetical (nl_NL) |
| **Typeahead** | User knows (part of) the name | Alphabetical matches, not by count |
| **Browse A–Z** | User is exploring, no name yet | Alphabetical pages |
| **Free text** | Legacy-style "contains" on naam | N/A |
| **Date range** | Temporal RQ | N/A |

**Counts:** show as optional scope hints ("42 treffers") — never use count to rank or promote options.

**Do not:** one sidebar with every dimension on every page; top-N by popularity; assume bigger = more searched.

#### Per-context filter sets (defaults — tune with user testing)

| Context | Prominent | In advanced / on demand |
|---------|-----------|-------------------------|
| **Personen** | naam, period | stand, adel, geo, functie/instelling lookup, birth/death dates |
| **Aanstellingen** | functie + instelling lookup, period, date range | geo, stand, grouping by instelling/functie |
| **Instellingen** | naam (browse/typeahead), period | — |
| **Functies** | naam (browse/typeahead), period | — |

Users add dimensions as needed (progressive disclosure) — most RQs need 1–3 filters, not all eight.

#### API support

- `search_contexts.yaml` — defines which filters appear per `entity` + widget type
- `GET /api/suggest/{field}` — alphabetical typeahead; **respects period scope** (returns only entities with appointments/records in that period)
- `GET /api/browse/{entity}/az` — A–Z catalog; **period-scoped by default**
- Same `SearchBackend` underneath; only exposed filters change per context

Legacy AND/OR multi-select: per filter group where multiple values apply; same semantics as [`query.py`](file:///Users/rikhoekstra/develop/RepertoriumAmbtenarenAmbtsdragers/src/raa/query.py).

**Validate in Milestone B:** test 3–4 real RQs from historians against each search context; adjust `search_contexts.yaml` before building all four pages.

## Phase 1 — Data import (`raa_modernized` repo root)

1. Bootstrap: `dighum_web_template/scripts/bootstrap_web.sh ~/develop/raa_modernized raa-modernized --monorepo`
2. Register datasets in `data_manifest.toml`:
   - `raa_extab` → logical path to `raa_convert/extab.pkl` (via `data_manifest.local.toml`)
   - `web_db` → Postgres connection / release tag
3. Add **`scripts/import_release.py`**:
   - Load `extab.pkl` (reuse loader from [`validate_export.py`](file:///Users/rikhoekstra/develop/raa_convert/validate_export.py))
   - Import into normalized Postgres tables (14 entities, FK constraints, indexes)
   - Period flags → boolean columns or `period_membership` junction table
   - Key indexes: `persoon.searchable`, `geslachtsnaam` (pg_trgm), `aanstelling.van/tot`, FK columns
   - Tag import with `release_id` (e.g. `2025-06`) for future merge
4. Run existing validation (`validate_export.py`) as pre-build gate.
5. Export frozen parquet per table (optional, analytics) via `data_io.save_parquet`.

**If decision gate later chooses ES:** add `build_search_index.py` that projects from Postgres (not directly from extab) — single import path.

---

## Phase 2 — Backend API (`raa_modernized/web/api`)

Stack: **FastAPI + SQLAlchemy 2 + Pydantic + `SearchBackend` protocol**. Pilot: `PostgresBackend`.

### 2a. SearchBackend interface

```python
class SearchBackend(Protocol):
    async def search(self, entity: str, request: SearchRequest) -> SearchResponse: ...
    async def get_detail(self, entity: str, id: int) -> dict: ...
    async def list_periods(self) -> list[PeriodCount]: ...
```

`SearchRequest` / `SearchResponse` are backend-agnostic (hits, total, facets dict). Frontend never knows Postgres vs ES.

### 2b. Search endpoints

| Endpoint | Notes |
|----------|-------|
| `POST /api/search/personen` | Text + facets + date ranges; returns hits + facet counts |
| `POST /api/search/aanstellingen` | Group-by via SQL `GROUP BY` or ES `terms` agg |
| `POST /api/search/instellingen`, `/functies` | |
| `GET /api/{entity}/{id}` | Detail via JOINs (Postgres) or doc fetch (ES) |
| `GET /api/periods` | Period labels + doc counts |
| `GET /api/suggest/{field}` | Typeahead for tier B/C (alphabetical, not by count); optional contextual count per hit |
| `GET /api/browse/{entity}/az` | Paginated A–Z catalog for exploration (instelling, functie) |

Port `_text_search()` wildcard/quote semantics in a shared query builder (used by both backends).

Legacy AND/OR multi-select: SQL `IN` / nested subqueries (Postgres) or `bool` queries (ES).

### 2c. Facet response contract

Every search response includes `hits`, `total`, `facets` — tier A buckets only (complete lists, alphabetical). Tier B/C filters come from suggest/browse, not sidebar facet buckets.

### 2d. Tests

- Unit tests for text query builder (backend-agnostic)
- Integration tests against Postgres testcontainer (pilot)
- Regression: result counts vs legacy searches, per period and overall
- **Decision gate tests:** document p95 latency + wildcard correctness metrics

---

## Phase 3 — Frontend (`raa_modernized/web/frontend`)

**SvelteKit** with Dutch UI copy from legacy templates.

### Global chrome

- **Period selector** (always visible): scopes all contexts unless "Alle perioden"
- Nav: **four search contexts** (personen / aanstellingen / instellingen / functies) — each with its own filter set per RQ
- Home: guided entry ("Waar wilt u mee beginnen?") — not a unified facet wall

### Search page layout (varies by context)

Not one layout for all pages. Example for **aanstellingen** (office-led RQ):

```
[Period]  Personen | Aanstellingen | Instellingen | Functies
────────────────────────────────────────────────────────────
Functie: [typeahead]   Instelling: [typeahead]   Periode: [range]
[Uitgebreid ▼]  geo, stand, AND/OR
Chips: Burgemeester ×  Utrecht ×
────────────────────────────────────────────────────────────
Results (group by instelling | functie)
```

**Personen** leads with name search; **instellingen/functies** lead with browse/typeahead on naam. Sidebar facets only where the RQ calls for a small closed set (e.g. stand on personen advanced).

### Pages

| Route | Notes |
|-------|-------|
| `/` | Home + period selector |
| `/personen` | Faceted search (primary v1 slice) |
| `/personen/{id}` | Detail via API JOINs; local/supra-local split |
| `/aanstellingen` | Faceted search + group-by institution/function |
| `/instellingen`, `/instellingen/{id}` | Faceted search + sanitized HTML toelichting |
| `/functies`, `/functies/{id}` | Faceted search + detail |

### UI components

- **SearchContextLayout** — renders filter set from `search_contexts.yaml` per page
- **FilterTypeahead**, **BrowseAZ**, **FacetCheckboxList** (small sets only), **FilterChips**
- **AdvancedPanel** — progressive disclosure per context

---

## Phase 4 — Deployment and ops

| Concern | Approach |
|---------|----------|
| Local dev | `docker compose`: PostgreSQL + FastAPI + SvelteKit |
| Build | `uv run python scripts/import_release.py`; `web/frontend` build + API |
| Hosting | Managed Postgres + API container + static frontend |
| Data updates | Re-run convert → `merge_release.py` → refresh search (SQL or ES reindex) |
| Auth | Public read-only for v1; editorial auth in Phase 5 |
| CI | Validate extab → import fixture DB → API integration tests |

---

## Phase 5 — Editorial layer (editing without re-converting)

**Problem:** `raa_convert` is a heavy, offline pipeline (MDB → merge → `extab.pkl`). Editorial fixes must not require re-running it. A full re-import should happen only when source databases change (new research, corrected MDBs) — and even then, **human corrections must survive**.

**Recommended model: immutable releases + editorial overlay + PostgreSQL**

```mermaid
flowchart TB
    subgraph convert [raa_convert - occasional]
        extab_v1[extab-2025-06.pkl]
        extab_v2[extab-2026-01.pkl]
    end

    subgraph raa_modernized [raa_modernized]
        import[import_release.py]
        merge[merge_release.py]
    end

    subgraph store [PostgreSQL in docker-compose]
        pg[(PostgreSQL)]
        base[base_entities]
        amend[editorial_amendments]
        pg --> base
        pg --> amend
    end

    subgraph search [Search via web/api]
        api[SearchBackend]
        pg --> api
    end

    extab_v1 --> import --> base
    extab_v2 --> merge
    amend --> merge
    merge --> base
    base --> api
    amend --> api
```

### Three layers of truth

| Layer | What it is | Mutability |
|-------|------------|------------|
| **Source release** | Versioned `extab.pkl` (or parquet) from `raa_convert`, registered in manifest as `raa_extab@2025-06` | Immutable once published |
| **Base tables** | Postgres copy of current release (`import_batch_id` on every row) | Replaced/merged on release upgrade only |
| **Editorial amendments** | Overrides keyed by `(entity_type, entity_id, field)` | Append/update by authenticated editors |

**Read path:** `effective_value = amendment.value ?? base.value` — applied in SQL queries (and ES docs if that path is added later).

**Write path:** Edit UI → `POST /api/editorial/...` → Postgres `editorial_amendments` → search results reflect amendments immediately (same DB) or via partial reindex (if ES path chosen).

### Why PostgreSQL fits editing (and likely search)

Postgres gives amendment history, conflict detection on re-import, and — at RAA scale — SQL facets are fast enough. ES only adds value if the decision gate shows search pain.

If ES is chosen after Milestone B: Postgres stays canonical; ES becomes a read projection synced on import/edit.

### Re-import without losing edits

When a new `extab` release arrives:

1. **`import_release.py`** — load new snapshot to staging tables
2. **`merge_release.py`** — for each entity matched by stable `id` (or [`concordance_files/mapping_tables.json`](file:///Users/rikhoekstra/develop/raa_convert/concordance_files/mapping_tables.json) when IDs shift):
   - If no amendment on field → take new base value
   - If amendment exists and new value **equals** old base → amendment still valid, update base underneath
   - If amendment exists and new value **differs** → flag **conflict** for human review (do not auto-overwrite)
3. Rebuild search layer from merged state (SQL views refresh, or ES reindex if that path was chosen)

Editors never touch `raa_convert`; they only touch the amendment API.

### What is editable (phased)

| Phase | Scope | Legacy parallel |
|-------|-------|-----------------|
| **5a** | `instelling.toelichting` (rich HTML) | Only field editable in old Zope app |
| **5b** | `opmerkingen` on persoon/aanstelling | Low-risk text corrections |
| **5c** | Core fields (names, dates, FKs) | Higher risk; needs validation + audit |
| **5d** | Create new records (web-only) | New capability; IDs allocated in Postgres, indexed to ES |

Start with **5a** — matches legacy scope, highest value, lowest merge risk.

### Auth and audit

- Role-based: `viewer` / `editor` / `admin`
- Every amendment: user, timestamp, optional change note
- Optional: link amendments to `data_io` provenance sidecars in repo root
- Sanitize HTML on `toelichting` (unlike legacy TinyMCE raw storage)

### Alternative considered: file-based amendments in git

Store overrides as YAML/JSON in `editorial/` at repo root (manifest-backed). Viable for solo research; Postgres `editorial_amendments` table better for multi-editor.

### Impact on earlier phases

- **v1 (Phases 0–4):** read-only search via `PostgresBackend` pilot
- **After Milestone B:** search store decision gate
- **Phase 5:** editorial amendments in same Postgres instance
- **`dighum_web_template`:** document optional `editorial` module in web-app scaffold for future projects

---

## Effort estimate (rough)

| Phase | Scope | Estimate |
|-------|-------|----------|
| **0 Web derivative** | New `dighum_web_template` repo + pointer in dighum_template docs | 4–6 days |
| 1 Data import | `import_release.py` + Postgres schema + indexes | 3–5 days |
| 2 Backend API | SearchBackend + Postgres impl, period modes, detail | 1–2 weeks |
| 3 Frontend | Facet-first hybrid UI, period selector, 4 search areas | 2–3 weeks |
| 4 Deploy + polish | Postgres hosting, CI, legacy query regression, **decision gate** | 4–6 days |
| 5 Editorial layer | Amendments, edit UI, re-import merge | 2–3 weeks |

**Total v1 (read-only, Phases 0–4):** ~6–8 weeks. **With editing (Phase 5):** ~8–11 weeks.

---

## What to reuse vs rewrite

**Reuse (reference or copy logic):**
- [`query.py`](file:///Users/rikhoekstra/develop/RepertoriumAmbtenarenAmbtsdragers/src/raa/query.py) — search semantics
- [`views.py`](file:///Users/rikhoekstra/develop/RepertoriumAmbtenarenAmbtsdragers/src/raa/browser/views.py) — name formatting, appointment splitting, bron sorting
- [`.pt` templates`](file:///Users/rikhoekstra/develop/RepertoriumAmbtenarenAmbtsdragers/src/raa/browser/templates/) — field labels, page structure, Dutch copy
- [`validate_export.py`](file:///Users/rikhoekstra/develop/raa_convert/validate_export.py) — data quality gate
- [`data_definitions.py`](file:///Users/rikhoekstra/develop/raa_convert/data_definitions.py) — schema truth

**Rewrite from scratch:**
- All Zope/Five/SQLObject integration
- Container/traversal model ([`container.py`](file:///Users/rikhoekstra/develop/RepertoriumAmbtenarenAmbtsdragers/src/raa/container.py))
- MySQL-specific patches ([`monkey.py`](file:///Users/rikhoekstra/develop/RepertoriumAmbtenarenAmbtsdragers/src/raa/monkey.py))

---

## Suggested first milestone

Two-step validation:

**Milestone A — derivative smoke test (generic):**
1. `dighum_web_template/scripts/bootstrap_web.sh ~/develop/hello-web hello-web` creates data + web repos
2. Sample CSV → `import_release.py` → Postgres → facet search via API
3. Scaffold UI: period selector + facet sidebar showing counts

**Milestone B — RAA vertical slice (`raa_modernized`):**
1. `import_release.py` loads current `extab.pkl` into Postgres
2. Period-scoped + overall person search with functie/instelling filters
3. Person detail page
4. **Gate:** measure facet latency + wildcard parity → commit to Postgres or add ES
