"""Validate a completed Phase 3a run against its Phase 2a/2b inputs."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
from typing import Any

from experiment_config import resolve_run
from run_strategy_detection import sharded_run_root, validate_shard_args
from strategy_backend import LABEL_CODES, LABELS


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def read_selected_ids(
    path: Path,
    count: int,
    shard_index: int | None = None,
    num_shards: int | None = None,
    where_equals: dict[str, Any] | None = None,
) -> list[str]:
    ids: list[str] = []
    with path.open(encoding="utf-8") as handle:
        selected_index = 0
        for line in handle:
            record = json.loads(line)
            if where_equals and any(record.get(k) != v for k, v in where_equals.items()):
                continue
            if selected_index >= count:
                break
            current_index = selected_index
            selected_index += 1
            if shard_index is not None and current_index % int(num_shards) != shard_index:
                continue
            ids.append(str(record["id"]))
    return ids


def validate(
    config_path: Path,
    model_alias: str | None = None,
    shard_index: int | None = None,
    num_shards: int | None = None,
) -> tuple[Path, dict[str, Any]]:
    validate_shard_args(shard_index, num_shards)
    resolved = resolve_run(config_path, model_alias=model_alias)
    requested = resolved.requested_config
    input_root = resolved.input_root
    run_root = sharded_run_root(resolved.model_root, shard_index, num_shards)
    run_config_path = run_root / "run_config.json"
    manifest_path = resolved.manifest_path
    errors: list[str] = []

    if not run_config_path.is_file():
        raise FileNotFoundError(f"Missing run config: {run_config_path}")
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing input manifest: {manifest_path}")

    run_config = json.loads(run_config_path.read_text(encoding="utf-8"))
    expected_shard = (
        {"index": shard_index, "count": num_shards}
        if shard_index is not None
        else None
    )
    observed_shard = run_config.get("shard")
    if expected_shard is None:
        shard_matches = observed_shard is None
    else:
        shard_matches = isinstance(observed_shard, dict) and all(
            observed_shard.get(key) == value
            for key, value in expected_shard.items()
        )
    if not shard_matches:
        errors.append(
            f"run_config shard metadata differs from {expected_shard}"
        )
    thresholds = run_config["model"]["thresholds"]
    codes = [LABEL_CODES[label] for label in LABELS]
    threshold_by_code = {
        LABEL_CODES[label]: float(thresholds[label]) for label in LABELS
    }

    with manifest_path.open(encoding="utf-8", newline="") as handle:
        manifest = list(csv.DictReader(handle))
    where_equals = requested["selection"].get("where_equals")

    total_expected = 0
    total_observed = 0
    all_ids: set[str] = set()
    files: list[dict[str, Any]] = []
    for row in manifest:
        selected = int(row["selected_pairs"])
        input_path = input_root / row["input_file"]
        output_path = run_root / row["output_file"]
        expected_ids = read_selected_ids(
            input_path,
            selected,
            shard_index=shard_index,
            num_shards=num_shards,
            where_equals=where_equals,
        )
        total_expected += len(expected_ids)
        observed_ids: list[str] = []

        if not output_path.is_file():
            errors.append(f"Missing output: {row['output_file']}")
            continue
        with output_path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    errors.append(
                        f"{row['output_file']}:{line_number}: "
                        f"invalid JSON: {error}"
                    )
                    continue
                pair_id = str(record.get("id", ""))
                observed_ids.append(pair_id)
                if (
                    requested.get("input_schema") == "feats-phase2b-consolidated"
                    and record.get("canonical_pair_id") != pair_id
                ):
                    errors.append(f"{pair_id}: canonical_pair_id is inconsistent")
                if pair_id in all_ids:
                    errors.append(f"Duplicate prediction ID: {pair_id}")
                all_ids.add(pair_id)
                scores = record.get("strategy_scores", {})
                if list(scores) != codes:
                    errors.append(
                        f"{pair_id}: score codes/order differ from {codes}"
                    )
                    continue
                if any(
                    not isinstance(value, (int, float))
                    or not math.isfinite(float(value))
                    or not 0.0 <= float(value) <= 1.0
                    for value in scores.values()
                ):
                    errors.append(f"{pair_id}: invalid strategy probability")
                    continue
                expected_codes = [
                    code
                    for code in codes
                    if float(scores[code]) >= threshold_by_code[code]
                ]
                if record.get("predicted_codes") != expected_codes:
                    errors.append(
                        f"{pair_id}: predicted codes disagree with thresholds"
                    )
                expected_labels = [
                    label
                    for label in LABELS
                    if LABEL_CODES[label] in expected_codes
                ]
                if record.get("predicted_labels") != expected_labels:
                    errors.append(
                        f"{pair_id}: predicted labels disagree with codes"
                    )
                if record.get("strategy_count") != len(expected_codes):
                    errors.append(
                        f"{pair_id}: strategy_count is inconsistent"
                    )
                if record.get("model_alias") != run_config["model"]["alias"]:
                    errors.append(f"{pair_id}: model alias is inconsistent")

        total_observed += len(observed_ids)
        if observed_ids != expected_ids:
            errors.append(
                f"{row['output_file']}: output IDs/order differ from input"
            )
        files.append(
            {
                "input_file": row["input_file"],
                "output_file": row["output_file"],
                "expected_pairs": len(expected_ids),
                "observed_pairs": len(observed_ids),
            }
        )

    if run_config.get("status") != "complete":
        errors.append("run_config status is not complete")
    if int(run_config.get("processed_pairs", -1)) != total_observed:
        errors.append(
            "run_config processed_pairs differs from observed output"
        )

    report = {
        "schema": "feats-phase3-validation-v1",
        "experiment_id": resolved.experiment_id,
        "legacy_run_id": requested.get("run_id"),
        "model_alias": run_config["model"]["alias"],
        "shard": run_config.get("shard"),
        "valid": not errors,
        "expected_pairs": total_expected,
        "observed_pairs": total_observed,
        "files": files,
        "errors": errors,
    }
    report_path = run_root / "reports" / "validation.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = report_path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, report_path)
    return report_path, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--model-alias")
    parser.add_argument("--shard-index", type=int)
    parser.add_argument("--num-shards", type=int)
    args = parser.parse_args()
    path, report = validate(
        args.config.resolve(),
        model_alias=args.model_alias,
        shard_index=args.shard_index,
        num_shards=args.num_shards,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Validation report: {path}")
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
