#!/usr/bin/env bash
# Copy portable wisdom topics into a project's docs/wisdom/

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${1:?Usage: copy_wisdom.sh <project_dir>}"

WISDOM_SRC="$REPO_ROOT/wisdom/topics"
WISDOM_DST="$PROJECT/docs/wisdom"

if [[ ! -d "$PROJECT" ]]; then
  echo "Error: project directory not found: $PROJECT" >&2
  exit 1
fi

mkdir -p "$WISDOM_DST"

copied=0
for f in "$WISDOM_SRC"/*.md; do
  [[ -f "$f" ]] || continue
  if grep -q '^\*\*Portable:\*\* yes' "$f" 2>/dev/null; then
    cp "$f" "$WISDOM_DST/"
    copied=$((copied + 1))
  fi
done

# Pointer to full wisdom repo
cat > "$PROJECT/docs/wisdom/README.md" <<EOF
# Project wisdom (portable topics)

Copied from \`dighum_template/wisdom/topics/\` (Portable: yes).

Full index and journal: \`~/develop/dighum_template/wisdom/INDEX.md\`

Add project-specific notes under \`docs/\` — keep cross-project lessons in dighum_template.
EOF

echo "Copied $copied portable wisdom topic(s) → $WISDOM_DST/"
