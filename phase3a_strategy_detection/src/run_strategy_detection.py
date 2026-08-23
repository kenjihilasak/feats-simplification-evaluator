"""Run one model-agnostic Phase 3a strategy-detection configuration."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

from experiment_config import resolve_run
from model_registry import create_backend
from strategy_backend import materialize_prediction


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_INPUT_FIELDS = {
    "id", "language", "original", "simple"
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def read_jsonl(
    path: Path,
    limit: int | None = None,
    require_canonical: bool = False,
    shard_index: int | None = None,
    num_shards: int | None = None,
) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if limit is not None and index >= limit:
                break
            if shard_index is not None and index % int(num_shards) != shard_index:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON at {path}:{index + 1}: {error}"
                ) from error
            missing = REQUIRED_INPUT_FIELDS - set(record)
            if missing:
                raise ValueError(
                    f"{path}:{index + 1} missing fields: {sorted(missing)}"
                )
            if require_canonical:
                canonical_id = record.get("canonical_pair_id")
                if canonical_id is None or str(canonical_id) != str(record["id"]):
                    raise ValueError(
                        f"{path}:{index + 1} does not use canonical Phase 2b IDs"
                    )
            yield record


def batches(
    records: Iterable[dict[str, Any]], batch_size: int
) -> Iterator[list[dict[str, Any]]]:
    batch: list[dict[str, Any]] = []
    for record in records:
        batch.append(record)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def validate_shard_args(
    shard_index: int | None,
    num_shards: int | None,
) -> None:
    if (shard_index is None) != (num_shards is None):
        raise ValueError("--shard-index and --num-shards must be supplied together.")
    if shard_index is not None:
        if num_shards is None or num_shards < 1:
            raise ValueError("--num-shards must be positive.")
        if not 0 <= shard_index < num_shards:
            raise ValueError("--shard-index must be within [0, num_shards).")


def shard_pair_count(selected_pairs: int, shard_index: int, num_shards: int) -> int:
    if shard_index >= selected_pairs:
        return 0
    return (selected_pairs - 1 - shard_index) // num_shards + 1


def sharded_run_root(
    model_root: Path,
    shard_index: int | None,
    num_shards: int | None,
) -> Path:
    if shard_index is None or num_shards is None:
        return model_root
    return (
        model_root
        / "shards"
        / f"shard-{shard_index:05d}-of-{num_shards:05d}"
    )


def environment_versions() -> dict[str, Any]:
    packages = (
        "torch", "transformers", "peft", "bitsandbytes", "accelerate",
        "huggingface-hub", "PyYAML", "safetensors",
    )
    versions: dict[str, str] = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not-installed"
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": versions,
    }


def hardware_info() -> dict[str, Any]:
    info: dict[str, Any] = {
        "cpu": platform.processor() or "unknown",
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    }
    try:
        import torch
    except ImportError:
        info["cuda_available"] = False
        return info

    info["cuda_available"] = bool(torch.cuda.is_available())
    if torch.cuda.is_available():
        info.update(
            {
                "cuda_device_count": torch.cuda.device_count(),
                "cuda_device_name": torch.cuda.get_device_name(0),
            }
        )
    return info


def build_manifest(
    input_root: Path,
    relative_files: list[str],
    limit_per_file: int | None,
    manifest_path: Path,
) -> list[dict[str, Any]]:
    if manifest_path.is_file():
        with manifest_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if [row["input_file"] for row in rows] != relative_files:
            raise ValueError(
                f"Existing manifest file list differs from config: {manifest_path}"
            )
        return rows

    rows: list[dict[str, Any]] = []
    for relative in relative_files:
        input_path = input_root / relative
        if not input_path.is_file():
            raise FileNotFoundError(f"Phase 3a input does not exist: {input_path}")
        total = line_count(input_path)
        selected = total if limit_per_file is None else min(total, limit_per_file)
        relative_path = Path(relative)
        output_relative = Path("predictions") / relative_path
        rows.append(
            {
                "input_file": relative_path.as_posix(),
                "output_file": output_relative.as_posix(),
                "language": relative_path.parent.as_posix(),
                "total_pairs": total,
                "selected_pairs": selected,
                "input_sha256": sha256(input_path),
            }
        )

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = manifest_path.with_suffix(f".csv.tmp-{os.getpid()}")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    if manifest_path.exists():
        existing = manifest_path.read_text(encoding="utf-8")
        candidate = temporary.read_text(encoding="utf-8")
        temporary.unlink()
        if existing != candidate:
            raise ValueError(
                f"Existing experiment manifest differs from requested input: {manifest_path}"
            )
    else:
        os.replace(temporary, manifest_path)
    return rows


def run(
    config_path: Path,
    model_alias: str | None = None,
    shard_index: int | None = None,
    num_shards: int | None = None,
    resume: bool = False,
) -> Path:
    validate_shard_args(shard_index, num_shards)
    resolved = resolve_run(config_path, model_alias=model_alias)
    config = resolved.requested_config
    input_root = resolved.input_root
    run_root = sharded_run_root(resolved.model_root, shard_index, num_shards)
    reports_root = run_root / "reports"
    reports_root.mkdir(parents=True, exist_ok=True)
    canonical_input = config.get("input_schema") == "feats-phase2b-consolidated"

    selection = config["selection"]
    limit = selection.get("limit_per_file")
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise ValueError(
            "selection.limit_per_file must be null or a positive integer."
        )
    relative_files = [str(value) for value in selection["files"]]
    if not relative_files:
        raise ValueError("selection.files cannot be empty.")

    manifest = build_manifest(
        input_root, relative_files, limit, resolved.manifest_path
    )
    expected_pairs = config.get("expected_pairs")
    selected_pairs = sum(int(row["selected_pairs"]) for row in manifest)
    if expected_pairs is not None and selected_pairs != int(expected_pairs):
        raise ValueError(
            f"Experiment expected {expected_pairs} pairs, manifest has {selected_pairs}."
        )
    for row in manifest:
        selected = int(row["selected_pairs"])
        row["effective_pairs"] = (
            selected
            if shard_index is None
            else shard_pair_count(selected, shard_index, int(num_shards))
        )
    effective_pairs = sum(int(row["effective_pairs"]) for row in manifest)
    shard = (
        None
        if shard_index is None
        else {"index": shard_index, "count": num_shards, "pairs": effective_pairs}
    )
    if not resolved.legacy:
        atomic_json(
            resolved.experiment_root / "experiment_config.json",
            config,
        )
    backend = create_backend(resolved.model_config, cache_root=resolved.cache_root)
    wall_start = time.monotonic()
    prepare_start = time.monotonic()
    backend.prepare()
    prepare_seconds = time.monotonic() - prepare_start

    started = datetime.now(timezone.utc)
    resolved_config = {
        "schema": (
            "feats-phase3-run-v1" if resolved.legacy
            else "feats-phase3-model-run-v2"
        ),
        "status": "running",
        "experiment_id": resolved.experiment_id,
        "model_alias": backend.alias,
        "shard": shard,
        "resume": bool(resume),
        "input_schema": config.get("input_schema", "phase2-cleaned-observations"),
        "started_at": started.isoformat(),
        "requested_config": config,
        "requested_config_sha256": sha256(config_path),
        "model_config": resolved.model_config,
        "model_config_sha256": (
            sha256(resolved.model_config_path)
            if resolved.model_config_path is not None else None
        ),
        "input_manifest_sha256": sha256(resolved.manifest_path),
        "model": dict(backend.provenance()),
        "environment": environment_versions(),
        "hardware": hardware_info(),
    }
    atomic_json(run_root / "run_config.json", resolved_config)

    processed = 0
    output_rows: list[dict[str, Any]] = []
    model_load_seconds = 0.0
    inference_seconds = 0.0
    progress_every = int(resolved.model_config.get("progress_every_pairs", 1000))
    if progress_every < 1:
        raise ValueError("progress_every_pairs must be positive.")
    try:
        load_start = time.monotonic()
        backend.load()
        model_load_seconds = time.monotonic() - load_start
        inference_start = time.monotonic()
        for manifest_row in manifest:
            input_path = input_root / manifest_row["input_file"]
            output_path = run_root / manifest_row["output_file"]
            expected_file_pairs = int(manifest_row["effective_pairs"])
            if output_path.exists():
                if not resume:
                    raise FileExistsError(
                        "Refusing to overwrite an existing Phase 3a prediction: "
                        f"{output_path}"
                    )
                existing_pairs = line_count(output_path)
                if existing_pairs != expected_file_pairs:
                    raise ValueError(
                        f"Cannot resume {output_path}: expected {expected_file_pairs} "
                        f"pairs, found {existing_pairs}."
                    )
                processed += existing_pairs
                output_rows.append(
                    {
                        "input_file": manifest_row["input_file"],
                        "output_file": manifest_row["output_file"],
                        "pairs": existing_pairs,
                        "seconds": 0.0,
                        "reused": True,
                        "output_sha256": sha256(output_path),
                    }
                )
                print(
                    f"[{backend.alias}] reused {manifest_row['input_file']}: "
                    f"{existing_pairs}/{expected_file_pairs}",
                    flush=True,
                )
                continue
            output_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = output_path.with_suffix(
                output_path.suffix + f".tmp-{os.getpid()}"
            )
            file_start = time.monotonic()
            file_count = 0
            with temporary.open("w", encoding="utf-8") as output_handle:
                records = read_jsonl(
                    input_path,
                    limit=limit,
                    require_canonical=canonical_input,
                    shard_index=shard_index,
                    num_shards=num_shards,
                )
                for batch in batches(records, backend.batch_size):
                    predictions = backend.predict_batch(
                        [
                            (str(record["original"]), str(record["simple"]))
                            for record in batch
                        ]
                    )
                    if len(predictions) != len(batch):
                        raise RuntimeError(
                            f"Backend returned {len(predictions)} predictions "
                            f"for a batch of {len(batch)} pairs."
                        )
                    for record, prediction in zip(batch, predictions):
                        pair_id = str(record["id"])
                        result = materialize_prediction(
                            pair_id=pair_id,
                            canonical_pair_id=(pair_id if canonical_input else None),
                            model_alias=backend.alias,
                            prediction=prediction,
                            thresholds=backend.thresholds,
                        )
                        output_handle.write(
                            json.dumps(
                                result,
                                ensure_ascii=False,
                                separators=(",", ":"),
                            )
                            + "\n"
                        )
                        file_count += 1
                        processed += 1
                    if (
                        file_count == expected_file_pairs
                        or file_count % progress_every < len(batch)
                    ):
                        print(
                            f"[{backend.alias}] {manifest_row['input_file']}: "
                            f"{file_count}/{expected_file_pairs}",
                            flush=True,
                        )
            if file_count != expected_file_pairs:
                raise RuntimeError(
                    f"{manifest_row['input_file']}: produced {file_count} pairs, "
                    f"expected {expected_file_pairs}."
                )
            os.replace(temporary, output_path)
            output_rows.append(
                {
                    "input_file": manifest_row["input_file"],
                    "output_file": manifest_row["output_file"],
                    "pairs": file_count,
                    "seconds": time.monotonic() - file_start,
                    "output_sha256": sha256(output_path),
                }
            )
        inference_seconds = time.monotonic() - inference_start
    finally:
        backend.close()

    elapsed = time.monotonic() - wall_start
    completed = datetime.now(timezone.utc)
    resolved_config.update(
        {
            "status": "complete",
            "completed_at": completed.isoformat(),
            "elapsed_seconds": elapsed,
            "processed_pairs": processed,
            "timings": {
                "prepare_seconds": prepare_seconds,
                "model_load_seconds": model_load_seconds,
                "inference_seconds": inference_seconds,
            },
            "outputs": output_rows,
        }
    )
    atomic_json(run_root / "run_config.json", resolved_config)
    atomic_json(
        reports_root / "run_summary.json",
        {
            "experiment_id": resolved.experiment_id,
            "model_alias": backend.alias,
            "legacy_run_id": config.get("run_id"),
            "shard": shard,
            "processed_pairs": processed,
            "binary_decisions": processed * 6,
            "elapsed_seconds": elapsed,
            "prepare_seconds": prepare_seconds,
            "model_load_seconds": model_load_seconds,
            "inference_seconds": inference_seconds,
            "hardware": resolved_config["hardware"],
            "inference_seconds_per_pair": (
                inference_seconds / processed if processed else None
            ),
            "outputs": output_rows,
        },
    )
    return run_root


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--model-alias")
    parser.add_argument("--shard-index", type=int)
    parser.add_argument("--num-shards", type=int)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    run_root = run(
        args.config.resolve(),
        model_alias=args.model_alias,
        shard_index=args.shard_index,
        num_shards=args.num_shards,
        resume=args.resume,
    )
    print(f"Completed Phase 3a run: {run_root}", flush=True)


if __name__ == "__main__":
    main()
