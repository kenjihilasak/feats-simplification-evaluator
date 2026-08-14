"""Shared paths and atomic writers for Phase 1 converters."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Iterable, Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = PROJECT_ROOT / "raw"
DATA_ROOT = PROJECT_ROOT / "phase1_normalization" / "data"
METADATA_ROOT = PROJECT_ROOT / "metadata"
INVENTORY_ROOT = METADATA_ROOT / "inventories"
REPORT_ROOT = METADATA_ROOT / "conversion_reports"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def write_jsonl(path: Path, records: Iterable[dict[str, object]]) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    count = 0
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            stream.write("\n")
            count += 1
    os.replace(temporary, path)
    return {
        "output_path": str(path.relative_to(PROJECT_ROOT)),
        "pairs": count,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def iter_jsonl(path: Path) -> Iterator[dict[str, object]]:
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON {path}:{line_number}") from error
            if not isinstance(value, dict):
                raise ValueError(f"Non-object JSON {path}:{line_number}")
            yield value

