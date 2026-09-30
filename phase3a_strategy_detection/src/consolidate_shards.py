"""Consolidate validated Phase 3a shards into canonical per-language outputs."""

from __future__ import annotations

import argparse
import csv
import json
import os
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from experiment_config import resolve_run
from run_strategy_detection import atomic_json, sha256, sharded_run_root


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def consolidate(
    config_path: Path,
    model_alias: str,
    num_shards: int,
) -> tuple[Path, dict[str, Any]]:
    if num_shards < 2:
        raise ValueError("num_shards must be at least 2 for consolidation.")
    resolved = resolve_run(config_path, model_alias=model_alias)
    model_root = resolved.model_root
    manifest_path = resolved.manifest_path
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing input manifest: {manifest_path}")
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        manifest = list(csv.DictReader(handle))
    if not manifest:
        raise ValueError("Input manifest is empty.")

    shard_roots = [
        sharded_run_root(model_root, index, num_shards)
        for index in range(num_shards)
    ]
    shard_configs = []
    shard_reports = []
    for index, shard_root in enumerate(shard_roots):
        run_config_path = shard_root / "run_config.json"
        validation_path = shard_root / "reports" / "validation.json"
        if not run_config_path.is_file() or not validation_path.is_file():
            raise FileNotFoundError(f"Shard {index} is incomplete: {shard_root}")
        run_config = load_json(run_config_path)
        validation = load_json(validation_path)
        expected_shard = {"index": index, "count": num_shards}
        observed_shard = run_config.get("shard") or {}
        if any(observed_shard.get(key) != value for key, value in expected_shard.items()):
            raise ValueError(f"Shard metadata mismatch: {shard_root}")
        if run_config.get("status") != "complete" or not validation.get("valid"):
            raise ValueError(f"Shard {index} did not pass validation: {shard_root}")
        if validation.get("model_alias") != model_alias:
            raise ValueError(f"Shard {index} model alias mismatch.")
        shard_configs.append(run_config)
        shard_reports.append(validation)

    limit = resolved.selection.get("limit_per_file")
    where_equals = resolved.selection.get("where_equals")
    output_rows = []
    total_pairs = 0
    for manifest_row in manifest:
        input_path = resolved.input_root / manifest_row["input_file"]
        output_path = model_root / manifest_row["output_file"]
        if output_path.exists():
            raise FileExistsError(
                f"Refusing to overwrite consolidated prediction: {output_path}"
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = output_path.with_suffix(
            output_path.suffix + f".tmp-{os.getpid()}"
        )
        file_pairs = 0
        with ExitStack() as stack:
            shard_handles = [
                stack.enter_context(
                    (shard_root / manifest_row["output_file"]).open(
                        encoding="utf-8"
                    )
                )
                for shard_root in shard_roots
            ]
            input_handle = stack.enter_context(input_path.open(encoding="utf-8"))
            output_handle = stack.enter_context(
                temporary.open("w", encoding="utf-8")
            )
            selected_index = 0
            for input_line in input_handle:
                input_record = json.loads(input_line)
                if where_equals and any(input_record.get(k) != v for k, v in where_equals.items()):
                    continue
                if limit is not None and selected_index >= int(limit):
                    break
                shard_index = selected_index % num_shards
                selected_index += 1
                prediction_line = shard_handles[shard_index].readline()
                if not prediction_line:
                    raise ValueError(
                        f"Shard {shard_index} ended early for "
                        f"{manifest_row['input_file']}"
                    )
                prediction = json.loads(prediction_line)
                if str(prediction.get("id")) != str(input_record.get("id")):
                    raise ValueError(
                        f"Prediction/input ID mismatch in {manifest_row['input_file']} "
                        f"at row {index}."
                    )
                output_handle.write(
                    prediction_line.rstrip("\n") + "\n"
                )
                file_pairs += 1
            for shard_index, shard_handle in enumerate(shard_handles):
                if shard_handle.readline():
                    raise ValueError(
                        f"Shard {shard_index} has extra rows for "
                        f"{manifest_row['input_file']}"
                    )
        expected = int(manifest_row["selected_pairs"])
        if file_pairs != expected:
            raise ValueError(
                f"Consolidated {file_pairs} rows for {manifest_row['input_file']}; "
                f"expected {expected}."
            )
        os.replace(temporary, output_path)
        total_pairs += file_pairs
        output_rows.append(
            {
                "input_file": manifest_row["input_file"],
                "output_file": manifest_row["output_file"],
                "pairs": file_pairs,
                "output_sha256": sha256(output_path),
            }
        )

    expected_total = resolved.requested_config.get("expected_pairs")
    if expected_total is not None and total_pairs != int(expected_total):
        raise ValueError(
            f"Consolidated {total_pairs} pairs; expected {expected_total}."
        )

    completed_at = datetime.now(timezone.utc).isoformat()
    aggregate = dict(shard_configs[0])
    aggregate.update(
        {
            "schema": "feats-phase3-sharded-run-v1",
            "status": "complete",
            "shard": None,
            "shard_count": num_shards,
            "completed_at": completed_at,
            "processed_pairs": total_pairs,
            "timings": {
                key: sum(
                    float(config.get("timings", {}).get(key, 0.0))
                    for config in shard_configs
                )
                for key in (
                    "prepare_seconds",
                    "model_load_seconds",
                    "inference_seconds",
                )
            },
            "elapsed_seconds": sum(
                float(config.get("elapsed_seconds", 0.0))
                for config in shard_configs
            ),
            "outputs": output_rows,
            "hardware": {
                "mode": "slurm_array",
                "shard_count": num_shards,
                "devices": sorted(
                    {
                        str(config.get("hardware", {}).get("cuda_device_name"))
                        for config in shard_configs
                    }
                ),
            },
        }
    )
    atomic_json(model_root / "run_config.json", aggregate)

    report = {
        "schema": "feats-phase3-shard-consolidation-v1",
        "experiment_id": resolved.experiment_id,
        "model_alias": model_alias,
        "num_shards": num_shards,
        "processed_pairs": total_pairs,
        "binary_decisions": total_pairs * 6,
        "completed_at": completed_at,
        "input_manifest_sha256": sha256(manifest_path),
        "shard_pairs": [
            int(validation["observed_pairs"]) for validation in shard_reports
        ],
        "outputs": output_rows,
    }
    report_path = model_root / "reports" / "shard_consolidation.json"
    atomic_json(report_path, report)
    atomic_json(
        model_root / "reports" / "run_summary.json",
        {
            **report,
            "inference_seconds": aggregate["timings"]["inference_seconds"],
            "inference_seconds_per_pair": (
                aggregate["timings"]["inference_seconds"] / total_pairs
            ),
        },
    )
    return report_path, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--model-alias", required=True)
    parser.add_argument("--num-shards", type=int, required=True)
    args = parser.parse_args()
    path, report = consolidate(
        args.config.resolve(),
        model_alias=args.model_alias,
        num_shards=args.num_shards,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Consolidation report: {path}")


if __name__ == "__main__":
    main()
