#!/usr/bin/env bash
# Document orphan files in output/_inbox with llm_archivist (Ollama required).
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INBOX="${1:-$REPO_ROOT/output/_inbox}"
MODEL="${2:-qwen2.5-coder:latest}"
uv run archive-scan "$INBOX" --model "$MODEL"
