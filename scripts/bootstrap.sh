#!/usr/bin/env bash
# Bootstrap a new DH project from dighum_template.
#
# Usage:
#   ./scripts/bootstrap.sh /path/to/NewProject [python-package-name] [options]
#
# Options:
#   --addon <name>       Apply add-on overlay (repeatable)
#   --with-wisdom        Copy portable wisdom topics to docs/wisdom/
#   --with-archivist     Copy llm_archivist + inbox scripts (legacy file inventory)
#
# Environment:
#   LLM_ARCHIVIST_SRC  Path to llm_archivist package (default: ../llm-archivist/src/llm_archivist)
#
# Examples:
#   ./scripts/bootstrap.sh ~/develop/my-new-project my-new-project
#   ./scripts/bootstrap.sh ~/develop/gnb-analysis gnb-analysis --addon rpp --with-wisdom
#   ./scripts/bootstrap.sh ~/develop/my-new-project my-new-project --with-archivist

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ADDONS=()
WITH_WISDOM=false
WITH_ARCHIVIST=false
POSITIONAL=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --addon)
      ADDONS+=("${2:?--addon requires a name}")
      shift 2
      ;;
    --with-wisdom)
      WITH_WISDOM=true
      shift
      ;;
    --with-archivist)
      WITH_ARCHIVIST=true
      shift
      ;;
    -h|--help)
      sed -n '2,20p' "$0"
      exit 0
      ;;
    --)
      shift
      while [[ $# -gt 0 ]]; do POSITIONAL+=("$1"); shift; done
      break
      ;;
    -*)
      echo "Error: unknown option: $1" >&2
      exit 1
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

TARGET="${POSITIONAL[0]:?Usage: bootstrap.sh <target_dir> [package_name] [--addon NAME] [--with-wisdom] [--with-archivist]}"
PKG_NAME="${POSITIONAL[1]:-$(basename "$TARGET" | tr '[:upper:]' '[:lower:]' | tr ' _' '-')}"
LLM_ARCHIVIST_SRC="${LLM_ARCHIVIST_SRC:-$REPO_ROOT/../llm-archivist/src/llm_archivist}"

if [[ -e "$TARGET" && "$(ls -A "$TARGET" 2>/dev/null)" ]]; then
  echo "Error: target directory exists and is not empty: $TARGET" >&2
  exit 1
fi

if [[ "$WITH_ARCHIVIST" == true && ! -d "$LLM_ARCHIVIST_SRC" ]]; then
  echo "Error: llm_archivist not found at $LLM_ARCHIVIST_SRC" >&2
  echo "Clone llm-archivist as a sibling repo or set LLM_ARCHIVIST_SRC." >&2
  exit 1
fi

mkdir -p "$TARGET/tests"

echo "Copying template → $TARGET"
rsync -a \
  --exclude 'optional/' \
  --exclude 'pyproject.with-archivist.toml' \
  --exclude 'README.md.template' \
  "$REPO_ROOT/template/" "$TARGET/"

if [[ "$WITH_ARCHIVIST" == true ]]; then
  cp "$REPO_ROOT/template/pyproject.with-archivist.toml" "$TARGET/pyproject.toml"
fi

sed "s/PROJECT_NAME/$PKG_NAME/g" "$REPO_ROOT/template/README.md.template" > "$TARGET/README.md"

echo "Copying data_io package"
rsync -a "$REPO_ROOT/packages/data_io/" "$TARGET/data_io/"

if [[ "$WITH_ARCHIVIST" == true ]]; then
  echo "Copying llm_archivist package from $LLM_ARCHIVIST_SRC"
  rsync -a "$LLM_ARCHIVIST_SRC/" "$TARGET/llm_archivist/"
  rsync -a "$REPO_ROOT/template/optional/archivist/scripts/" "$TARGET/scripts/"
fi

echo "Copying tests"
cp "$REPO_ROOT/tests/test_data_io.py" "$TARGET/tests/"
if [[ "$WITH_ARCHIVIST" == true ]]; then
  if [[ -f "$REPO_ROOT/../llm-archivist/tests/test_scanners.py" ]]; then
    cp "$REPO_ROOT/../llm-archivist/tests/test_scanners.py" "$TARGET/tests/test_llm_archivist.py"
  fi
  if [[ -f "$REPO_ROOT/../llm-archivist/tests/test_inventory.py" ]]; then
    cp "$REPO_ROOT/../llm-archivist/tests/test_inventory.py" "$TARGET/tests/test_inventory.py"
  fi
fi

cp "$TARGET/data_manifest.toml.example" "$TARGET/data_manifest.toml"

if [[ "$(uname)" == "Darwin" ]]; then
  sed -i '' "s/PROJECT_NAME/$PKG_NAME/g" "$TARGET/pyproject.toml"
  sed -i '' "s/PROJECT_NAME/$PKG_NAME/g" "$TARGET/data_manifest.toml"
else
  sed -i "s/PROJECT_NAME/$PKG_NAME/g" "$TARGET/pyproject.toml"
  sed -i "s/PROJECT_NAME/$PKG_NAME/g" "$TARGET/data_manifest.toml"
fi

WORKSPACE_TEMPLATE="$TARGET/PROJECT_NAME.code-workspace"
WORKSPACE_FILE="$TARGET/$PKG_NAME.code-workspace"
if [[ -f "$WORKSPACE_TEMPLATE" ]]; then
  mv "$WORKSPACE_TEMPLATE" "$WORKSPACE_FILE"
fi

chmod +x "$TARGET/scripts"/*.sh 2>/dev/null || true

if [[ "$WITH_WISDOM" == true ]]; then
  echo "Copying portable wisdom → $TARGET/docs/wisdom/"
  "$REPO_ROOT/scripts/copy_wisdom.sh" "$TARGET"
fi

if ((${#ADDONS[@]} > 0)); then
  for addon in "${ADDONS[@]}"; do
    echo "Applying add-on: $addon"
    "$REPO_ROOT/scripts/apply_addon.sh" "$TARGET" "$addon"
  done
fi

ADDON_NOTE=""
if [[ ${#ADDONS[@]} -gt 0 ]]; then
  ADDON_NOTE="
Applied add-ons: ${ADDONS[*]}
See docs/addons/APPLIED.md"
fi

WISDOM_NOTE=""
if [[ "$WITH_WISDOM" == true ]]; then
  WISDOM_NOTE="
Portable wisdom copied to docs/wisdom/"
fi

ARCHIVIST_NOTE=""
if [[ "$WITH_ARCHIVIST" == true ]]; then
  ARCHIVIST_NOTE="
llm_archivist installed — uv run archive-inventory / uv run archive-scan"
fi

echo "Setting up uv venv + installing IPython kernel"
(
  cd "$TARGET"
  uv sync
  uv run python -m ipykernel install --user \
    --name "$PKG_NAME" \
    --display-name "Python ($PKG_NAME)"
)

cat <<EOF

Created: $TARGET

Next steps:
  cd $TARGET
  # Edit data_manifest.toml (tier roots + datasets)
  # Optional laptop fallback: cp data_manifest.local.toml.example data_manifest.local.toml
  uv run python -m data_io.check
  cursor $WORKSPACE_FILE    # or: code $WORKSPACE_FILE
$WISDOM_NOTE$ADDON_NOTE$ARCHIVIST_NOTE

Notebook workspace: notebooks/
Scratch fallback:   output/ (via data_manifest.local.toml when drive unplugged)

Optional later:
  $REPO_ROOT/scripts/apply_addon.sh $TARGET <name>
  $REPO_ROOT/scripts/copy_wisdom.sh $TARGET

For LLM coding: read AGENTS.md, PLAN.md, and .cursor/rules/project-standards.mdc
Wisdom index: $REPO_ROOT/wisdom/INDEX.md
Add-ons catalog: $REPO_ROOT/addons/README.md
Full guide: $REPO_ROOT/docs/NEW_REPO.md

EOF
