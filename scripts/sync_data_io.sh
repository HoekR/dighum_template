#!/usr/bin/env bash
# Refresh vendored data_io from republic_ner_matching (development source).
#
# Usage:
#   ./scripts/sync_data_io.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="${DATA_IO_SRC:-$REPO_ROOT/../republic_ner_matching/data_io}"

if [[ ! -d "$SOURCE" ]]; then
  echo "Error: data_io source not found at $SOURCE" >&2
  echo "Set DATA_IO_SRC to the live data_io package directory." >&2
  exit 1
fi

rsync -a "$SOURCE/" "$REPO_ROOT/packages/data_io/"
echo "Synced data_io → $REPO_ROOT/packages/data_io/"
