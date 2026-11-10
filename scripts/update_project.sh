#!/usr/bin/env bash
# Add/update Living Project State files in an existing derivative project.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

usage() {
  cat <<EOF
Usage: ./scripts/update_project.sh /path/to/project [--dry-run]

Adds the Living Project State CLI, dashboard notebooks, and missing docs to an
existing derived project. Existing project-specific files are preserved; template
copies are written with a .new suffix when a conflict exists.
EOF
}

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 1
fi

PROJECT="$1"
shift

ARGS=("$PROJECT" --state --editor-rules)
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) ARGS+=(--dry-run); shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Error: unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

"$REPO_ROOT/scripts/sync_project.sh" "${ARGS[@]}"