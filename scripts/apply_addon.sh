#!/usr/bin/env bash
# Apply an optional add-on overlay to a DH project.
#
# Usage:
#   ./scripts/apply_addon.sh /path/to/project <addon-name>
#
# Example:
#   ./scripts/apply_addon.sh ~/develop/my-project rpp

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${1:?Usage: apply_addon.sh <project_dir> <addon_name>}"
ADDON="${2:?Usage: apply_addon.sh <project_dir> <addon_name>}"
ADDON_DIR="$REPO_ROOT/addons/$ADDON"

if [[ ! -d "$PROJECT" ]]; then
  echo "Error: project directory not found: $PROJECT" >&2
  exit 1
fi

if [[ ! -f "$ADDON_DIR/addon.toml" ]]; then
  echo "Error: add-on not found or missing addon.toml: $ADDON" >&2
  echo "Available:" >&2
  ls -1 "$REPO_ROOT/addons" | grep -v '^_' >&2 || true
  exit 1
fi

export PROJECT ADDON ADDON_DIR REPO_ROOT
python3 <<'PY'
import re
import tomllib
from datetime import date
from pathlib import Path
import os

project = Path(os.environ["PROJECT"])
addon_dir = Path(os.environ["ADDON_DIR"])
addon_name = os.environ["ADDON"]
repo_root = Path(os.environ["REPO_ROOT"])

meta = tomllib.loads((addon_dir / "addon.toml").read_text())
title = meta.get("title", addon_name)
copy_paths = meta.get("copy", [])
agents_append = meta.get("agents_append")
manifest_hint = meta.get("manifest_hint")
pyproject_hint = meta.get("pyproject_hint")

for rel in copy_paths:
    src = addon_dir / rel
    dst = project / rel
    if not src.exists():
        raise SystemExit(f"Add-on copy path missing: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        import shutil
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        import shutil
        shutil.copy2(src, dst)

if agents_append:
    append_src = addon_dir / agents_append
    if append_src.exists():
        agents = project / "AGENTS.md"
        block = append_src.read_text().rstrip() + "\n"
        marker = "## Add-ons"
        if agents.exists():
            text = agents.read_text()
            if marker not in text:
                text = text.rstrip() + f"\n\n{marker}\n\n"
            if f"### {addon_name}" not in text and f"### {title}" not in text:
                # Use addon name as heading if append file starts with ###
                if not block.lstrip().startswith("###"):
                    block = f"### {addon_name}\n\n{block}"
                text = text.rstrip() + "\n\n" + block
                agents.write_text(text)
        else:
            agents.write_text(f"# Agent instructions\n\n{marker}\n\n{block}")

applied = project / "docs" / "addons" / "APPLIED.md"
applied.parent.mkdir(parents=True, exist_ok=True)
line = f"- **{addon_name}** ({title}) — {date.today().isoformat()}\n"
if applied.exists():
    if f"**{addon_name}**" not in applied.read_text():
        applied.write_text(applied.read_text().rstrip() + "\n" + line)
else:
    applied.write_text("# Applied add-ons\n\n" + line)

print(f"Applied add-on: {addon_name} ({title}) → {project}")
if manifest_hint:
    hint = addon_dir / manifest_hint
    if hint.exists():
        print(f"  Manifest hint (merge manually): {hint}")
if pyproject_hint:
    hint = addon_dir / pyproject_hint
    if hint.exists():
        print(f"  pyproject hint (merge manually): {hint}")
PY

echo "  Recorded in $PROJECT/docs/addons/APPLIED.md"
