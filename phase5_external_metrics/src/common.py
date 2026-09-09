"""Shared contracts and filesystem helpers for Phase 5 external metrics."""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_SCHEMA = "feats-phase5-external-metrics-experiment-v1"
MODEL_SCHEMA = "feats-phase5-external-metric-model-v1"
OUTPUT_SCHEMA = "feats-phase5-external-metric-prediction-v1"
REQUIRED_INPUT_FIELDS = {
    "canonical_pair_id", "language", "original", "simple"
}


def project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def atomic_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("Cannot write an empty CSV manifest.")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    seen: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON at {path}:{line_number}: {error}") from error
            missing = REQUIRED_INPUT_FIELDS - set(record)
            if missing:
                raise ValueError(f"{path}:{line_number} missing {sorted(missing)}")
            pair_id = str(record["canonical_pair_id"])
            if pair_id in seen:
                raise ValueError(f"Duplicate canonical_pair_id {pair_id}: {path}")
            seen.add(pair_id)
            if record["language"] != "en":
                raise ValueError(
                    f"Phase 5 external metrics support English only: {pair_id}"
                )
            yield record


def batches(records: Iterable[dict[str, Any]], size: int) -> Iterator[list[dict[str, Any]]]:
    if size < 1:
        raise ValueError("batch_size must be positive.")
    batch: list[dict[str, Any]] = []
    for record in records:
        batch.append(record)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def validate_shards(index: int | None, count: int | None) -> None:
    if (index is None) != (count is None):
        raise ValueError("--shard-index and --num-shards must be supplied together.")
    if index is not None and (count is None or count < 1 or not 0 <= index < count):
        raise ValueError("Invalid shard index/count.")


def shard_root(metric_root: Path, index: int | None, count: int | None) -> Path:
    if index is None:
        return metric_root
    return metric_root / "shards" / f"shard-{index:05d}-of-{count:05d}"


def selected_records(
    path: Path, index: int | None = None, count: int | None = None
) -> Iterator[dict[str, Any]]:
    for row_index, record in enumerate(read_jsonl(path)):
        if index is None or row_index % int(count) == index:
            yield record


def environment_info(extra_packages: Iterable[str] = ()) -> dict[str, Any]:
    package_names = ("torch", "transformers", "huggingface-hub", *extra_packages)
    versions = {}
    for name in package_names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not-installed"
    info: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": versions,
    }
    try:
        import torch
    except ImportError:
        info["device"] = "cpu"
    else:
        info["device"] = "cuda" if torch.cuda.is_available() else "cpu"
        if torch.cuda.is_available():
            info["cuda_device_name"] = torch.cuda.get_device_name(0)
    return info

