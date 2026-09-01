#!/usr/bin/env bash
# Sync dighum_template updates into an existing derivative project.
#
# Usage:
#   ./scripts/sync_project.sh /path/to/project [options]
#
# Options:
#   --data-io          Refresh vendored data_io/ from dighum_template
#   --wisdom           Copy portable wisdom topics → docs/wisdom/
#   --editor-rules     Refresh .cursor/rules + .github/copilot-instructions.md
#   --state            Add/update Living Project State CLI and missing dashboard files
#   --addons           Re-apply add-ons listed in docs/addons/APPLIED.md
#   --addon NAME       Re-apply one add-on (repeatable)
#   --mcp              uv sync MCP packages in dighum_template (not copied into project)
#   --all              --data-io --wisdom --editor-rules --state --addons --mcp
#   --dry-run          Print actions without executing
#
# Examples:
#   ./scripts/sync_project.sh ~/develop/wvo_corr --all
#   ./scripts/sync_project.sh ~/develop/wvo_corr --wisdom --addon workflow-mcp
#
# Manual merge still required for: AGENTS.md (base), pyproject.toml, data_manifest.toml,
# PLAN.md, domain code. Re-applying add-ons updates docs/addons/* but skips AGENTS.md
# sections that already exist.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT=""
DO_DATA_IO=false
DO_WISDOM=false
DO_EDITOR=false
DO_STATE=false
DO_ADDONS=false
DO_MCP=false
DRY_RUN=false
ADDON_NAMES=()

usage() {
  sed -n '2,25p' "$0"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --data-io) DO_DATA_IO=true; shift ;;
    --wisdom) DO_WISDOM=true; shift ;;
    --editor-rules) DO_EDITOR=true; shift ;;
    --state) DO_STATE=true; shift ;;
    --addons) DO_ADDONS=true; shift ;;
    --mcp) DO_MCP=true; shift ;;
    --all)
      DO_DATA_IO=true
      DO_WISDOM=true
      DO_EDITOR=true
      DO_STATE=true
      DO_ADDONS=true
      DO_MCP=true
      shift
      ;;
    --addon)
      ADDON_NAMES+=("${2:?--addon requires a name}")
      shift 2
      ;;
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help) usage; exit 0 ;;
    --)
      shift
      while [[ $# -gt 0 ]]; do
        if [[ -z "$PROJECT" ]]; then PROJECT="$1"; else echo "Error: unexpected argument: $1" >&2; exit 1; fi
        shift
      done
      break
      ;;
    -*)
      echo "Error: unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      if [[ -z "$PROJECT" ]]; then PROJECT="$1"; else echo "Error: unexpected argument: $1" >&2; exit 1; fi
      shift
      ;;
  esac
done

PROJECT="${PROJECT:?Usage: sync_project.sh <project_dir> [options]}"

if [[ ! -d "$PROJECT" ]]; then
  echo "Error: project directory not found: $PROJECT" >&2
  exit 1
fi

if [[ "$DO_DATA_IO$DO_WISDOM$DO_EDITOR$DO_STATE$DO_ADDONS$DO_MCP" == "false" && ${#ADDON_NAMES[@]} -eq 0 ]]; then
  echo "Error: no sync targets selected (try --all or see --help)" >&2
  exit 1
fi

run() {
  if [[ "$DRY_RUN" == true ]]; then
    echo "[dry-run] $*"
  else
    echo "→ $*"
    "$@"
  fi
}

read_applied_addons() {
  local applied="$PROJECT/docs/addons/APPLIED.md"
  if [[ ! -f "$applied" ]]; then
    return 0
  fi
  sed -n 's/^- \*\*\([^*]*\)\*\*.*/\1/p' "$applied"
}

copy_missing_or_new() {
  local source="$1"
  local destination="$2"
  if [[ ! -e "$source" ]]; then
    echo "Warning: missing template file: $source" >&2
    return 0
  fi
  if [[ "$DRY_RUN" == true ]]; then
    if [[ -e "$destination" ]]; then
      echo "[dry-run] would leave existing $destination and write $destination.new"
    else
      echo "[dry-run] cp $source $destination"
    fi
    return 0
  fi
  mkdir -p "$(dirname "$destination")"
  if [[ -e "$destination" ]]; then
    cp "$source" "$destination.new"
    echo "Note: kept existing $destination; wrote template copy to $destination.new"
  else
    cp "$source" "$destination"
  fi
}

echo "Sync dighum_template → $PROJECT"
[[ "$DRY_RUN" == true ]] && echo "(dry-run — no changes)"

if [[ "$DO_DATA_IO" == true ]]; then
  if [[ ! -d "$PROJECT/data_io" ]]; then
    echo "Warning: skipping --data-io (no data_io/ in project)" >&2
  elif [[ ! -d "$REPO_ROOT/packages/data_io" ]]; then
    echo "Error: dighum_template packages/data_io not found" >&2
    exit 1
  else
    run rsync -a "$REPO_ROOT/packages/data_io/" "$PROJECT/data_io/"
  fi
fi

if [[ "$DO_WISDOM" == true ]]; then
  run "$REPO_ROOT/scripts/copy_wisdom.sh" "$PROJECT"
fi

if [[ "$DO_EDITOR" == true ]]; then
  run "$REPO_ROOT/scripts/sync_editor_rules.sh" "$PROJECT"
fi

if [[ "$DO_STATE" == true ]]; then
  if [[ ! -d "$REPO_ROOT/template/docs" ]]; then
    echo "Error: template docs not found" >&2
    exit 1
  fi
  copy_missing_or_new "$REPO_ROOT/template/scripts/svz.py" "$PROJECT/scripts/svz.py"
  copy_missing_or_new "$REPO_ROOT/template/docs/state.json" "$PROJECT/docs/state.json"
  copy_missing_or_new "$REPO_ROOT/template/docs/STATE.md" "$PROJECT/docs/STATE.md"
  copy_missing_or_new "$REPO_ROOT/template/docs/DECISIONS.md" "$PROJECT/docs/DECISIONS.md"
  copy_missing_or_new "$REPO_ROOT/template/00_project_dashboard.ipynb" "$PROJECT/00_project_dashboard.ipynb"
  if [[ -d "$REPO_ROOT/template/tasks" ]]; then
    if [[ "$DRY_RUN" == true ]]; then
      echo "[dry-run] rsync missing task templates into $PROJECT/tasks/"
    else
      mkdir -p "$PROJECT/tasks"
      rsync -a --ignore-existing "$REPO_ROOT/template/tasks/" "$PROJECT/tasks/"
    fi
  fi
  if [[ "$DRY_RUN" != true ]]; then
    chmod +x "$PROJECT/scripts/svz.py" 2>/dev/null || true
  fi
fi

if [[ "$DO_ADDONS" == true ]]; then
  applied="$PROJECT/docs/addons/APPLIED.md"
  if [[ ! -f "$applied" ]]; then
    echo "Note: no docs/addons/APPLIED.md — skip --addons" >&2
  else
    while IFS= read -r addon; do
      [[ -n "$addon" ]] || continue
      run "$REPO_ROOT/scripts/apply_addon.sh" "$PROJECT" "$addon"
    done < <(read_applied_addons)
  fi
fi

if ((${#ADDON_NAMES[@]} > 0)); then
  for addon in "${ADDON_NAMES[@]}"; do
    run "$REPO_ROOT/scripts/apply_addon.sh" "$PROJECT" "$addon"
  done
fi

if [[ "$DO_MCP" == true ]]; then
  for pkg in workflow_mcp data_io_mcp notebook_env_mcp; do
    if [[ -d "$REPO_ROOT/packages/$pkg" ]]; then
      if [[ "$DRY_RUN" == true ]]; then
        echo "[dry-run] (cd $REPO_ROOT/packages/$pkg && uv sync)"
      else
        echo "→ uv sync packages/$pkg"
        (cd "$REPO_ROOT/packages/$pkg" && uv sync)
      fi
    fi
  done
fi

echo ""
echo "Done."

SUGGESTIONS=()
if [[ "$DO_DATA_IO" == true && -d "$PROJECT/data_io" ]]; then
  SUGGESTIONS+=("uv run python -m data_io.check")
fi
if [[ -d "$PROJECT/tests" && -f "$PROJECT/pyproject.toml" ]]; then
  SUGGESTIONS+=("uv run pytest tests/ -q")
fi
if [[ "$DO_STATE" == true ]]; then
  SUGGESTIONS+=("uv run python scripts/svz.py doctor")
fi

if ((${#SUGGESTIONS[@]} > 0)); then
  cat <<EOF

Suggested checks in the project:
  cd $PROJECT
$(printf '  %s\n' "${SUGGESTIONS[@]}")
EOF
else
  cat <<EOF

No post-sync checks suggested — project has no data_io/ or tests/ yet (e.g. pre–Step 0).
EOF
fi

cat <<EOF

Manual merge may still be needed for AGENTS.md (base), pyproject.toml, PLAN.md.
Add-on docs under docs/addons/ were refreshed; AGENTS.md add-on blocks are not overwritten if already present.

EOF
