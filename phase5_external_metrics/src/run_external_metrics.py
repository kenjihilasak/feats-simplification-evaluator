"""Run one Phase 5 metric, optionally as a resumable deterministic shard."""

from __future__ import annotations

import argparse
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import Any

from common import (
    EXPERIMENT_SCHEMA,
    MODEL_SCHEMA,
    OUTPUT_SCHEMA,
    PROJECT_ROOT,
    atomic_json,
    batches,
    environment_info,
    load_json,
    project_path,
    selected_records,
    sha256,
    shard_root,
    text_sha256,
    validate_shards,
)
from model_registry import create_backend


def resolve(config_path: Path, metric_alias: str) -> dict[str, Any]:
    experiment = load_json(config_path)
    if experiment.get("schema") != EXPERIMENT_SCHEMA:
        raise ValueError(f"Expected schema {EXPERIMENT_SCHEMA}.")
    metrics = experiment.get("metrics")
    if not isinstance(metrics, dict) or metric_alias not in metrics:
        raise ValueError(f"Unknown metric {metric_alias!r}; available: {sorted(metrics or {})}")
    model_path = project_path(metrics[metric_alias]).resolve()
    model = load_json(model_path)
    if model.get("schema") != MODEL_SCHEMA or model.get("alias") != metric_alias:
        raise ValueError(f"Metric alias/schema mismatch: {model_path}")
    if model.get("score_field") not in {"lens_salsa_score", "referee_score"}:
        raise ValueError("score_field must be lens_salsa_score or referee_score.")
    input_path = project_path(experiment["input_file"]).resolve()
    run_root = project_path(experiment["runs_root"]) / str(experiment["experiment_id"])
    return {
        "experiment": experiment,
        "model": model,
        "model_path": model_path,
        "input_path": input_path,
        "experiment_root": run_root,
        "metric_root": run_root / "metrics" / metric_alias,
        "cache_root": project_path(experiment.get("cache_root", "cache/huggingface")),
    }


def count_records(path: Path) -> int:
    return sum(1 for _ in selected_records(path))


def output_record(
    source: dict[str, Any], prediction, alias: str, score_field: str,
    provenance: dict[str, Any], shard_index: int | None,
) -> dict[str, Any]:
    score = float(prediction.score)
    if not math.isfinite(score):
        raise ValueError(f"Non-finite {alias} score for {source['canonical_pair_id']}")
    record = {
        "schema": OUTPUT_SCHEMA,
        "canonical_pair_id": str(source["canonical_pair_id"]),
        "language": "en",
        "metric_alias": alias,
        "score": score,
        score_field: score,
        "original_sha256": text_sha256(str(source["original"])),
        "simple_sha256": text_sha256(str(source["simple"])),
        "diagnostics": dict(prediction.diagnostics),
        "model": dict(provenance),
    }
    if shard_index is not None:
        record["shard_index"] = shard_index
    return record


def existing_partial_ids(path: Path) -> list[str]:
    if not path.exists():
        return []
    ids = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid partial output {path}:{line_number}") from error
            ids.append(str(row.get("canonical_pair_id", "")))
    return ids


def run(
    config_path: Path,
    metric_alias: str,
    shard_index: int | None = None,
    num_shards: int | None = None,
    resume: bool = False,
) -> Path:
    validate_shards(shard_index, num_shards)
    resolved = resolve(config_path.resolve(), metric_alias)
    input_path: Path = resolved["input_path"]
    if not input_path.is_file():
        raise FileNotFoundError(f"Input does not exist: {input_path}")
    total = count_records(input_path)
    expected = resolved["experiment"].get("expected_pairs")
    if expected is not None and total != int(expected):
        raise ValueError(f"Expected {expected} input pairs, found {total}.")

    root = shard_root(resolved["metric_root"], shard_index, num_shards)
    output_path = root / "predictions.jsonl"
    partial_path = root / "predictions.jsonl.partial"
    if output_path.exists():
        if resume:
            return root
        raise FileExistsError(f"Refusing to overwrite immutable output: {output_path}")
    if partial_path.exists() and not resume:
        raise FileExistsError(f"Partial output exists; pass --resume: {partial_path}")

    records = selected_records(input_path, shard_index, num_shards)
    partial_ids = existing_partial_ids(partial_path)
    for partial_id in partial_ids:
        try:
            source = next(records)
        except StopIteration as error:
            raise ValueError("Partial output is longer than this shard.") from error
        if partial_id != str(source["canonical_pair_id"]):
            raise ValueError("Partial output is not a canonical prefix of this shard.")

    root.mkdir(parents=True, exist_ok=True)
    resolved["experiment_root"].mkdir(parents=True, exist_ok=True)
    atomic_json(resolved["experiment_root"] / "experiment_config.json", resolved["experiment"])
    manifest = {
        "schema": "feats-phase5-input-manifest-v1",
        "input_file": str(input_path.relative_to(PROJECT_ROOT)) if input_path.is_relative_to(PROJECT_ROOT) else str(input_path),
        "input_sha256": sha256(input_path),
        "pairs": total,
        "language": "en",
    }
    manifest_path = resolved["experiment_root"] / "input_manifest.json"
    if manifest_path.exists() and load_json(manifest_path) != manifest:
        raise ValueError("Existing input manifest differs from requested input.")
    atomic_json(manifest_path, manifest)

    backend = create_backend(resolved["model"], resolved["cache_root"])
    started_at = datetime.now(timezone.utc).isoformat()
    start = monotonic()
    try:
        backend.prepare()
        provenance = dict(backend.provenance())
        run_config = {
            "schema": "feats-phase5-external-metric-run-v1",
            "status": "running",
            "experiment_id": resolved["experiment"]["experiment_id"],
            "metric_alias": metric_alias,
            "score_field": resolved["model"]["score_field"],
            "language": "en",
            "shard": None if shard_index is None else {"index": shard_index, "count": num_shards},
            "started_at": started_at,
            "input_manifest_sha256": sha256(manifest_path),
            "model_config_sha256": sha256(resolved["model_path"]),
            "model": provenance,
            "environment": environment_info(("lens-metric",)),
        }
        atomic_json(root / "run_config.json", run_config)
        mode = "a" if partial_ids else "w"
        processed = len(partial_ids)
        with partial_path.open(mode, encoding="utf-8") as handle:
            for batch in batches(records, backend.batch_size):
                pairs = [(str(row["original"]), str(row["simple"])) for row in batch]
                try:
                    predictions = backend.predict_batch(pairs)
                except RuntimeError as error:
                    if "out of memory" in str(error).lower():
                        raise RuntimeError(
                            f"CUDA OOM in {metric_alias}; reduce batch_size and resume."
                        ) from error
                    raise
                if len(predictions) != len(batch):
                    raise RuntimeError("Backend prediction count differs from input batch.")
                for source, prediction in zip(batch, predictions):
                    row = output_record(
                        source, prediction, metric_alias,
                        str(resolved["model"]["score_field"]), provenance, shard_index,
                    )
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                    processed += 1
                handle.flush()
                os.fsync(handle.fileno())
        os.replace(partial_path, output_path)
        run_config.update(
            {
                "status": "complete",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "processed_pairs": processed,
                "elapsed_seconds": monotonic() - start,
                "output_sha256": sha256(output_path),
            }
        )
        atomic_json(root / "run_config.json", run_config)
    finally:
        backend.close()
    return root


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--metric-alias", required=True)
    parser.add_argument("--shard-index", type=int)
    parser.add_argument("--num-shards", type=int)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    print(run(args.config, args.metric_alias, args.shard_index, args.num_shards, args.resume))


if __name__ == "__main__":
    main()

