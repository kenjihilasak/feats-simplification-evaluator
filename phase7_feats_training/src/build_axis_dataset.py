"""Materialize the Phase 6 synthetic corpus under the Phase 7 contract and audit leakage."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from contracts import AxisExample, atomic_json, read_jsonl, sha256, strong_key, word_set, write_jsonl
from evaluation_loaders import (evaluation_originals, load_heldout_review, load_human_likert,
                                load_simpeval_2022, load_simplicity_da)

ROOT = Path(__file__).resolve().parents[2]


def convert(row: dict, input_path: Path) -> dict:
    example = AxisExample(
        example_id=f"{row['canonical_pair_id']}:{row['axis']}:{row['variant']}",
        canonical_pair_id=row["canonical_pair_id"], canonical_original_id=row["canonical_original_id"],
        language=row["language"], original=row["original"], candidate_simplification=row["text"],
        audience=None, axis=row["axis"], target_score=float(row["score"]), target_scale="binary_0_1",
        label_source="synthetic", distortion_type=row.get("operation"), split=row["split"],
        provenance={"phase": 6, "source_file": str(input_path.relative_to(ROOT)),
                    "corpus": row.get("corpus"), "source": row.get("source"),
                    "variant": row["variant"], "generation": row.get("generation")},
    )
    return example.to_dict()


def load_evaluations(config: dict) -> tuple[dict[str, list[dict]], list[Path]]:
    paths = {name: ROOT / value for name, value in config["evaluation_inputs"].items()}
    sets = {
        "simplicity_da": load_simplicity_da(paths["simplicity_da"]),
        "human_likert": load_human_likert(paths["human_likert"]),
        "simpeval_2022": load_simpeval_2022(paths["simpeval_2022"]),
        "heldout_v2": load_heldout_review(paths["heldout_v2_review"], paths["heldout_v2_key"]),
        "heldout_meaning_v21": load_heldout_review(paths["heldout_meaning_v21_review"], paths["heldout_meaning_v21_key"]),
    }
    return sets, list(paths.values())


def leakage_audit(dataset_rows: list[dict], evaluation_sets: dict[str, list[dict]], threshold: float) -> dict:
    evaluation = []
    for dataset, rows in evaluation_sets.items():
        for key, text in evaluation_originals(rows).items():
            evaluation.append((dataset, key, text, word_set(text)))
    training = {}
    for row in dataset_rows:
        training.setdefault(row["canonical_original_id"], row["original"])
    exact, near = [], []
    eval_keys = {key for _, key, _, _ in evaluation}
    for original_id, text in training.items():
        key = strong_key(text)
        if key in eval_keys:
            exact.append({"canonical_original_id": original_id, "original": text})
            continue
        training_words = word_set(text)
        for dataset, _, other, other_words in evaluation:
            union = training_words | other_words
            score = len(training_words & other_words) / len(union) if union else 1.0
            if score >= threshold:
                near.append({"canonical_original_id": original_id, "evaluation_dataset": dataset,
                             "jaccard": score, "training_original": text, "evaluation_original": other})
    return {"schema": "feats-phase7-leakage-check-v1", "threshold": threshold,
            "training_originals": len(training), "evaluation_originals": len(evaluation),
            "exact_hits": exact, "near_duplicate_hits": near, "passed": not exact and not near}


def build(config_path: Path, output_root: Path) -> None:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    inputs = [ROOT / path for path in config["synthetic_inputs"]]
    rows = [convert(row, path) for path in inputs for row in read_jsonl(path)]
    counts = Counter((row["split"], row["axis"], row["provenance"]["variant"]) for row in rows)
    pair_counts = Counter((row["split"], row["axis"], row["canonical_pair_id"]) for row in rows)
    malformed = [key for key, count in pair_counts.items() if count != 2]
    if malformed:
        raise ValueError(f"Expected exactly two rows per pair; malformed examples: {malformed[:10]}")
    evaluations, evaluation_paths = load_evaluations(config)
    leakage = leakage_audit(rows, evaluations, float(config.get("near_duplicate_threshold", 0.8)))
    output_root.mkdir(parents=True, exist_ok=True)
    atomic_json(output_root / "leakage_check.json", leakage)
    if not leakage["passed"]:
        raise RuntimeError("STOP: training/evaluation leakage detected; see leakage_check.json")
    write_jsonl(output_root / "dataset.jsonl", rows)
    for name, records in evaluations.items():
        write_jsonl(output_root / "evaluation" / f"{name}.jsonl", records)
    all_inputs = inputs + evaluation_paths + [config_path]
    atomic_json(output_root / "data_manifest.json", {
        "schema": "feats-phase7-data-manifest-v1", "experiment_id": config["experiment_id"],
        "inputs": [{"path": str(path.relative_to(ROOT)), "sha256": sha256(path)} for path in all_inputs],
        "output_counts": {"rows": len(rows), "pairs": len(pair_counts),
                          "by_split_axis_variant": {"/".join(key): value for key, value in sorted(counts.items())},
                          "evaluation": {name: len(value) for name, value in evaluations.items()}},
    })


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    build(args.config.resolve(), args.output_root.resolve())


if __name__ == "__main__":
    main()
