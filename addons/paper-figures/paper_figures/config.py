"""Load and merge TOML configuration for figure styling."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a ``figure_style.toml`` (or bundled defaults) file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(p)
    return tomllib.loads(p.read_text(encoding="utf-8"))


def merge_config(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge override into base (override wins)."""
    out = dict(base)
    for key, val in override.items():
        if key in out and isinstance(out[key], dict) and isinstance(val, dict):
            out[key] = merge_config(out[key], val)
        else:
            out[key] = val
    return out


def resolve_config(
    *,
    config_path: str | Path | None = None,
    extra_paths: list[str | Path] | None = None,
) -> dict[str, Any]:
    """Load defaults, optional project config, extension fragments, and extra paths."""
    pkg_defaults = Path(__file__).resolve().parent / "defaults.toml"
    merged: dict[str, Any] = load_config(pkg_defaults) if pkg_defaults.is_file() else {}

    paths: list[Path] = []
    if config_path:
        paths.append(Path(config_path))
    if extra_paths:
        paths.extend(Path(p) for p in extra_paths)

    for p in paths:
        if not p.is_file():
            continue
        chunk = load_config(p)
        extensions = chunk.pop("extensions", [])
        merged = merge_config(merged, chunk)
        for ext in extensions:
            ext_path = Path(ext.get("path", ""))
            if not ext_path.is_absolute() and config_path:
                ext_path = Path(config_path).parent / ext_path
            if ext_path.is_file():
                merged = merge_config(merged, load_config(ext_path))

    return merged
