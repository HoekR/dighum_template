#!/usr/bin/env bash
# Write Cursor + VS Code Copilot rule files from template/shared/agent-standards.md
#
# Usage:
#   ./scripts/sync_editor_rules.sh              # refresh files under template/
#   ./scripts/sync_editor_rules.sh /path/to/project

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-$REPO_ROOT/template}"
SRC="$REPO_ROOT/template/shared/agent-standards.md"

if [[ ! -f "$SRC" ]]; then
  echo "Error: shared standards not found: $SRC" >&2
  exit 1
fi

BODY="$(cat "$SRC")"

mkdir -p "$TARGET/.cursor/rules" "$TARGET/.github"

cat >"$TARGET/.cursor/rules/project-standards.mdc" <<EOF
---
description: Core project standards for DH data projects (shared with VS Code Copilot)
alwaysApply: true
---

$BODY
EOF

cat >"$TARGET/.github/copilot-instructions.md" <<EOF
<!-- Same body as .cursor/rules/project-standards.mdc.
     Source: dighum_template/template/shared/agent-standards.md -->

$BODY
EOF

echo "Synced editor rules → $TARGET/.cursor/rules/project-standards.mdc"
echo "Synced editor rules → $TARGET/.github/copilot-instructions.md"
