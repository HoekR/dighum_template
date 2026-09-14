# Option 1 build — Phase 0 + Milestone B

**Status:** plan committed; implementation blocked until Agent mode is enabled.

## Scope

1. Finish `dighum_web_template` (`bootstrap_web.sh`, overlays, web scaffold)
2. Bootstrap `~/develop/raa_modernized` (`--monorepo`)
3. Copy `PLAN.md` into `raa_modernized`
4. Milestone B: `import_release.py` + person search API + minimal UI

## Commands (after agent implements scaffolds)

```bash
cd ~/develop/dighum_web_template
chmod +x scripts/*.sh
./scripts/bootstrap_web.sh ~/develop/raa_modernized raa-modernized --monorepo

cd ~/develop/raa_modernized
cp ../dighum_template/plans/PLAN-raa-modernized.md PLAN.md
# data_manifest.local.toml: register raa_extab → ../raa_convert/extab.pkl
docker compose -f web/docker-compose.yml up -d db
uv run python scripts/import_release.py
cd web/api && uv run uvicorn raa_api.main:app --reload
```

## Blocker

Plan mode only allows markdown edits. Approve **Agent mode** and say "continue Option 1 build" to create repos and code.
