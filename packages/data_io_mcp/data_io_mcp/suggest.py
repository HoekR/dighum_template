"""Draft manifest entries for human review before commit."""

from __future__ import annotations


def suggest_manifest_entry(
    logical_name: str,
    path: str,
    *,
    tier: str = "scratch",
    phase: str = "semi",
    description: str = "",
    parent: str | None = None,
) -> str:
    lines = [
        f"[datasets.{logical_name}]",
        f'tier = "{tier}"',
        f'path = "{path}"',
        f'phase = "{phase}"',
    ]
    if description:
        lines.append(f'description = "{description}"')
    if parent:
        lines.append(f'parent = "{parent}"')
    lines.append("")
    lines.append("# After merging into data_manifest.toml, run:")
    lines.append("#   uv run python -m data_io.check")
    return "\n".join(lines)
