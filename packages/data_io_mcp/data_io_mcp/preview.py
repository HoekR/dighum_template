"""Small dataset previews for MCP tools (never return full wide tables)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TYPE_CHECKING

import pandas as pd
import pyarrow.parquet as pq

if TYPE_CHECKING:
    from data_io.manifest import DataManager

MAX_PREVIEW_ROWS = 20
MAX_PREVIEW_CHARS = 48_000


def _truncate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    encoded = json.dumps(payload, default=str)
    if len(encoded) <= MAX_PREVIEW_CHARS:
        return payload
    payload = dict(payload)
    payload["truncated"] = True
    payload["preview_note"] = (
        f"Preview JSON exceeded {MAX_PREVIEW_CHARS} chars; reduce limit or inspect file on disk."
    )
    if "sample_rows" in payload and isinstance(payload["sample_rows"], list):
        payload["sample_rows"] = payload["sample_rows"][:3]
    return payload


def _preview_parquet(path: Path, *, limit: int, phase: str | None) -> dict[str, Any]:
    from data_io.provenance import read_sidecar

    pf = pq.ParquetFile(path)
    schema = pf.schema_arrow
    columns = [field.name for field in schema]
    num_rows = pf.metadata.num_rows if pf.metadata else None
    table = pf.read_row_group(0, columns=columns[: min(len(columns), 50)])
    df = table.to_pandas()
    sample = df.head(limit)
    wide = len(columns) > 50
    return _truncate_payload(
        {
            "format": "parquet",
            "path": str(path),
            "shape": [num_rows, len(columns)],
            "columns": columns[:100],
            "columns_truncated": len(columns) > 100,
            "wide_table": wide,
            "sample_rows": json.loads(sample.to_json(orient="records", date_format="iso")),
            "sidecar": read_sidecar(path, phase=phase),
        }
    )


def _preview_json(path: Path, *, limit: int, phase: str | None) -> dict[str, Any]:
    from data_io.provenance import read_sidecar

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return _truncate_payload(
            {
                "format": "json",
                "path": str(path),
                "record_count": len(data),
                "sample_rows": data[:limit],
                "sidecar": read_sidecar(path, phase=phase),
            }
        )
    if isinstance(data, dict):
        keys = list(data.keys())
        preview: dict[str, Any] = {
            "format": "json",
            "path": str(path),
            "top_level_keys": keys[:50],
            "sidecar": read_sidecar(path, phase=phase),
        }
        for key in ("transition_counts", "matrices", "items", "records"):
            if key in data and isinstance(data[key], list):
                preview["sample_rows"] = data[key][:limit]
                preview["sample_from_key"] = key
                break
        else:
            preview["sample"] = {k: data[k] for k in keys[: min(5, len(keys))]}
        return _truncate_payload(preview)
    return _truncate_payload(
        {
            "format": "json",
            "path": str(path),
            "value_type": type(data).__name__,
            "sample": data,
            "sidecar": read_sidecar(path, phase=phase),
        }
    )


def _preview_jsonl(path: Path, *, limit: int, phase: str | None) -> dict[str, Any]:
    from data_io.jsonl_io import load_jsonl
    from data_io.provenance import read_sidecar

    rows = load_jsonl(path)
    return _truncate_payload(
        {
            "format": "jsonl",
            "path": str(path),
            "record_count": len(rows),
            "sample_rows": rows[:limit],
            "sidecar": read_sidecar(path, phase=phase),
        }
    )


def preview_dataset(
    manager: DataManager,
    logical_name: str,
    *,
    limit: int = 10,
) -> dict[str, Any]:
    from data_io.manifest import TierUnavailableError
    from data_io.provenance import read_sidecar

    limit = max(1, min(limit, MAX_PREVIEW_ROWS))
    dataset = manager.dataset(logical_name)
    try:
        path = manager.resolve(logical_name)
    except TierUnavailableError as exc:
        return {
            "logical_name": logical_name,
            "available": False,
            "error": str(exc),
            "tier": dataset.tier,
            "phase": dataset.phase,
        }

    if not path.exists():
        return {
            "logical_name": logical_name,
            "available": False,
            "resolved_path": str(path),
            "tier": dataset.tier,
            "phase": dataset.phase,
            "description": dataset.description,
        }

    suffixes = path.suffixes
    inner = path.suffix
    if path.suffix == ".gz" and len(suffixes) >= 2:
        inner = "".join(suffixes[:-1])

    if inner == ".parquet":
        body = _preview_parquet(path, limit=limit, phase=dataset.phase)
    elif inner == ".jsonl":
        body = _preview_jsonl(path, limit=limit, phase=dataset.phase)
    elif inner == ".json":
        body = _preview_json(path, limit=limit, phase=dataset.phase)
    elif inner in {".csv", ".tsv"}:
        sep = "\t" if inner == ".tsv" else ","
        df = pd.read_csv(path, sep=sep, nrows=limit)
        body = _truncate_payload(
            {
                "format": inner.lstrip("."),
                "path": str(path),
                "columns": list(df.columns),
                "sample_rows": json.loads(df.to_json(orient="records", date_format="iso")),
                "sidecar": read_sidecar(path, phase=dataset.phase),
            }
        )
    else:
        body = {
            "format": inner or "unknown",
            "path": str(path),
            "note": "No structured preview for this suffix; use resolve_dataset.",
            "sidecar": read_sidecar(path, phase=dataset.phase),
        }

    return {
        "logical_name": logical_name,
        "available": True,
        "tier": dataset.tier,
        "phase": dataset.phase,
        "description": dataset.description,
        "parent": dataset.parent,
        **body,
    }
