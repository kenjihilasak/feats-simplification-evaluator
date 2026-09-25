#!/usr/bin/env python3
"""Validate audited degradations and materialize grouped train/validation instances."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, write_jsonl
from phase6_degraded_corpus.src.planning.multi_axis import AXES


def split_for_original(original_id: str, seed: int, validation_fraction: float) -> str:
    value = int(hashlib.sha256(f"{seed}:{original_id}".encode()).hexdigest(), 16) / (2**256)
    return "validation" if value < validation_fraction else "train"


def validate_and_build(
    manifest: list[dict], generated: list[dict], audits: list[dict], seed: int,
    validation_fraction: float = 0.1,
) -> tuple[list[dict], dict]:
    def unique(rows: list[dict], name: str) -> dict[str, dict]:
        result = {}
        for row in rows:
            pair_id = row["canonical_pair_id"]
            if pair_id in result:
                raise ValueError(f"duplicate canonical_pair_id in {name}: {pair_id}")
            result[pair_id] = row
        return result

    expected = unique(manifest, "manifest")
    predictions = unique(generated, "generated output")
    decisions = unique(audits, "audit decisions")
    unknown = (set(predictions) | set(decisions)) - set(expected)
    if unknown:
        raise ValueError(f"unknown canonical_pair_id: {sorted(unknown)[:3]}")

    accepted = []
    quality = defaultdict(lambda: Counter(total=0, clean_acceptable=0, degradation_acceptable=0, accepted=0))
    for pair_id, audit in decisions.items():
        row = expected[pair_id]
        axis = row["target_axis"]
        quality[axis]["total"] += 1
        quality[axis]["clean_acceptable"] += bool(audit.get("clean_acceptable"))
        quality[axis]["degradation_acceptable"] += bool(audit.get("single_target_degradation"))
        prediction = predictions.get(pair_id)
        if audit.get("decision") != "accepted":
            continue
        if not prediction or prediction.get("status") != "generated_pending_audit":
            raise ValueError(f"accepted audit lacks valid generation: {pair_id}")
        if prediction["target_axis"] != axis or prediction["source_strategy"] != row["source_strategy"]:
            raise ValueError(f"generation metadata mismatch: {pair_id}")
        if not audit.get("clean_acceptable") or not audit.get("single_target_degradation"):
            raise ValueError(f"accepted audit failed required checks: {pair_id}")
        if axis != "MEANING" and not audit.get("meaning_preserved_for_non_meaning"):
            raise ValueError(f"non-meaning degradation changes meaning: {pair_id}")
        quality[axis]["accepted"] += 1
        accepted.append((row, prediction))

    instances = []
    original_splits = {}
    for row, prediction in accepted:
        original_id = row["canonical_original_id"]
        split = split_for_original(original_id, seed, validation_fraction)
        previous = original_splits.setdefault(original_id, split)
        if previous != split:
            raise AssertionError("canonical original crossed splits")
        base = {
            "schema": "feats-phase6-training-instance-v1",
            "canonical_pair_id": row["canonical_pair_id"],
            "canonical_original_id": original_id,
            "original": row["original"],
            "source_strategy": row["source_strategy"],
            "target_axis": row["target_axis"],
            "split": split,
            "generation_model_revision": prediction["model_revision"],
            "prompt_id": prediction["prompt_id"],
        }
        instances.append({**base, "variant": "clean", "simplification": row["clean_simplification"], "score": 1.0})
        instances.append({
            **base,
            "variant": "degraded",
            "simplification": prediction["generation"]["degraded_simplification"],
            "score": 0.0,
        })
    instances.sort(key=lambda row: (row["canonical_pair_id"], row["variant"]))
    per_axis = {}
    for axis in AXES:
        values = quality[axis]
        total = values["total"]
        per_axis[axis] = {
            **dict(values),
            "clean_acceptance_rate": values["clean_acceptable"] / total if total else None,
            "degradation_acceptance_rate": values["degradation_acceptable"] / total if total else None,
        }
    report = {
        "schema": "feats-phase6-materialization-report-v1",
        "manifest_pairs": len(expected),
        "generated_pairs": len(predictions),
        "audited_pairs": len(decisions),
        "accepted_pairs": len(accepted),
        "training_instances": len(instances),
        "instances_by_split": dict(sorted(Counter(row["split"] for row in instances).items())),
        "instances_by_axis": dict(sorted(Counter(row["target_axis"] for row in instances).items())),
        "quality_by_axis": per_axis,
    }
    return instances, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--generated", type=Path, required=True)
    parser.add_argument("--audits", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260925)
    parser.add_argument("--validation-fraction", type=float, default=0.1)
    parser.add_argument("--require-pilot-thresholds", action="store_true")
    args = parser.parse_args()
    if not 0 < args.validation_fraction < 1:
        raise ValueError("validation fraction must be between zero and one")
    instances, report = validate_and_build(
        read_jsonl(args.manifest), read_jsonl(args.generated), read_jsonl(args.audits),
        args.seed, args.validation_fraction,
    )
    if args.require_pilot_thresholds:
        failures = []
        for axis, values in report["quality_by_axis"].items():
            if not values["total"]:
                continue
            if values["clean_acceptance_rate"] < 0.90:
                failures.append(f"{axis}: clean acceptance below 0.90")
            if values["degradation_acceptance_rate"] < 0.85:
                failures.append(f"{axis}: degradation acceptance below 0.85")
        if failures:
            raise ValueError("pilot quality gate failed: " + "; ".join(failures))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "training_instances.jsonl", instances)
    for split in ("train", "validation"):
        write_jsonl(args.output_dir / f"{split}.jsonl", [row for row in instances if row["split"] == split])
    (args.output_dir / "manifest.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
