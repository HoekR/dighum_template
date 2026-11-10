#!/usr/bin/env bash
# Sync mlx_llm package outward to a target project.
#
# Since mlx_llm is authored in dighum_template (not vendored in from elsewhere),
# this script syncs the core package files (excluding tests, docs) outward.
#
# Usage:
#   ./scripts/sync_mlx_llm.sh /path/to/target/project

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET_PROJECT="${1:?Error: target project path required as \$1}"

if [[ ! -d "$REPO_ROOT/packages/mlx_llm" ]]; then
  echo "Error: mlx_llm source not found at $REPO_ROOT/packages/mlx_llm" >&2
  exit 1
fi

if [[ ! -d "$TARGET_PROJECT" ]]; then
  echo "Error: target project directory not found at $TARGET_PROJECT" >&2
  exit 1
fi

# Sync only the importable package content — never ship local env/lock/docs/tests.
rsync -a \
  --exclude="tests" \
  --exclude="pyproject.toml" \
  --exclude="README.md" \
  --exclude="LICENSE" \
  --exclude="uv.lock" \
  --exclude=".venv" \
  --exclude=".pytest_cache" \
  --exclude="__pycache__" \
  --exclude="*.egg-info" \
  "$REPO_ROOT/packages/mlx_llm/" "$TARGET_PROJECT/mlx_llm/"

echo "Synced mlx_llm → $TARGET_PROJECT/mlx_llm/"
