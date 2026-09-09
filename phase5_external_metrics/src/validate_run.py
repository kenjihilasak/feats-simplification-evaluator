"""Validate a Phase 5 metric output against its exact source records."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from itertools import zip_longest
from typing import Any

from common import OUTPUT_SCHEMA, atomic_json, load_json, selected_records, sha256, shard_root, text_sha256, validate_shards
from run_external_metrics import resolve


def validate(
    config_path: Path,
    metric_alias: str,
    shard_index: int | None = None,
    num_shards: int | None = None,
) -> tuple[Path, dict[str, Any]]:
    validate_shards(shard_index, num_shards)
    resolved = resolve(config_path.resolve(), metric_alias)
    root = shard_root(resolved["metric_root"], shard_index, num_shards)
    output_path = root / "predictions.jsonl"
    config = load_json(root / "run_config.json")
    if config.get("status") != "complete":
        raise ValueError("Run is not complete.")
    if config.get("output_sha256") != sha256(output_path):
        raise ValueError("Output checksum differs from run_config.json.")
    inputs = selected_records(resolved["input_path"], shard_index, num_shards)
    seen: set[str] = set()
    observed = 0
    score_field = str(resolved["model"]["score_field"])
    truncated = 0
    sentinel = object()
    with output_path.open(encoding="utf-8") as predictions:
        for source, line in zip_longest(inputs, predictions, fillvalue=sentinel):
            if source is sentinel:
                raise ValueError("Output contains extra predictions.")
            if line is sentinel:
                raise ValueError("Output ended before the selected input.")
            row = json.loads(line)
            pair_id = str(source["canonical_pair_id"])
            if row.get("schema") != OUTPUT_SCHEMA or row.get("canonical_pair_id") != pair_id:
                raise ValueError(f"Prediction/input contract mismatch at {pair_id}.")
            if pair_id in seen:
                raise ValueError(f"Duplicate prediction: {pair_id}")
            seen.add(pair_id)
            if row.get("metric_alias") != metric_alias or row.get("language") != "en":
                raise ValueError(f"Metric/language mismatch at {pair_id}.")
            score = row.get("score")
            if not isinstance(score, (int, float)) or not math.isfinite(float(score)):
                raise ValueError(f"Invalid score at {pair_id}.")
            if row.get(score_field) != score:
                raise ValueError(f"Native score field mismatch at {pair_id}.")
            if row.get("original_sha256") != text_sha256(str(source["original"])) or row.get("simple_sha256") != text_sha256(str(source["simple"])):
                raise ValueError(f"Text hash mismatch at {pair_id}.")
            truncated += bool(row.get("diagnostics", {}).get("truncated", False))
            observed += 1
    report = {
        "schema": "feats-phase5-external-metric-validation-v1",
        "valid": True,
        "metric_alias": metric_alias,
        "observed_pairs": observed,
        "truncated_pairs": truncated,
        "output_sha256": sha256(output_path),
    }
    report_path = root / "reports" / "validation.json"
    atomic_json(report_path, report)
    return report_path, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--metric-alias", required=True)
    parser.add_argument("--shard-index", type=int)
    parser.add_argument("--num-shards", type=int)
    args = parser.parse_args()
    path, report = validate(args.config, args.metric_alias, args.shard_index, args.num_shards)
    print(json.dumps(report, indent=2))
    print(path)


if __name__ == "__main__":
    main()

