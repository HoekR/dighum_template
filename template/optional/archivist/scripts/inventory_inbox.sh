#!/usr/bin/env bash
# Fast inventory of orphan files (no Ollama). LLM enrichment: archive_inbox.sh
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INBOX="${1:-$REPO_ROOT/output/_inbox}"
uv run archive-inventory "$INBOX" "${@:2}"
