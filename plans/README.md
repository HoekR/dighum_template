# Plans (dighum_template)

Maintainer plans for this meta-repo live here. Pipeline **project** repos get a short root [`PLAN.md`](../template/PLAN.md) (headlines) plus an empty [`template/plans/`](../template/plans/) tree at bootstrap; add milestone/step files on demand.

## Layout (projects)

| Path | When | Role |
|------|------|------|
| `PLAN.md` (root) | Always | Headlines: goal, milestone index, progress checklist, data paths |
| `plans/` | Always (empty skeleton) | Index + `milestones/` + `steps/` |
| `plans/<name>.md` | On demand | Full / cross-cutting plans |
| `plans/milestones/M*.md` | On demand | Milestone writeups |
| `plans/steps/STEP*.md` | On demand | Per-step guides (workflow MCP) |

Convention: [wisdom/topics/cost-sensitive-agent-workflow.md](../wisdom/topics/cost-sensitive-agent-workflow.md). Do not copy this meta-repo catalog into derivatives.

## Catalog (this repo)

| Plan | Notes |
|------|-------|
| [PLAN-raa-modernized.md](PLAN-raa-modernized.md) | RAA modern webapp track (belongs with `dighum_web_template`) |
| [OPTION-1-BUILD.md](OPTION-1-BUILD.md) | Phase 0 + Milestone B build track for that plan |
