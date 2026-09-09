"""Report Phase 5 metric distributions across FEATS audit strata."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from analyze_metrics import load_predictions, summary
from common import atomic_csv, atomic_json, read_jsonl
from prepare_inputs import bin_labse, bin_length, load_decisions, load_strategies


def audit_values(record: dict[str, Any], decisions: dict[str, dict[str, Any]]) -> tuple[float | None, str]:
    occurrence_ids = [str(item.get("id")) for item in record.get("provenance", [])]
    rows = [decisions[value] for value in occurrence_ids if value in decisions]
    labse_values = [float(row["labse_similarity"]) for row in rows if row.get("labse_similarity") is not None]
    labse = sum(labse_values) / len(labse_values) if labse_values else None
    directions = []
    for row in rows:
        complexity = row.get("complexity", {})
        original = complexity.get("original", {}).get("prob_simple")
        simple = complexity.get("simple", {}).get("prob_simple")
        if original is not None and simple is not None:
            directions.append(float(simple) - float(original))
    if not directions:
        complexity_bin = "missing"
    else:
        delta = sum(directions) / len(directions)
        complexity_bin = "target_simpler" if delta > .1 else "flat" if delta >= -.1 else "target_more_complex"
    return labse, complexity_bin


def analyze(
    input_path: Path, lens_path: Path, referee_path: Path,
    decisions_root: Path, strategies_path: Path, output_dir: Path,
) -> dict[str, Any]:
    lens, referee = load_predictions(lens_path), load_predictions(referee_path)
    decisions, strategies = load_decisions(decisions_root), load_strategies(strategies_path)
    grouped: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
    originals: dict[str, list[tuple[str, float, float]]] = defaultdict(list)
    count = 0
    for record in read_jsonl(input_path):
        pair_id = str(record["canonical_pair_id"])
        if pair_id not in lens or pair_id not in referee:
            raise ValueError(f"Missing metric prediction for {pair_id}")
        scores = (float(lens[pair_id]["score"]), float(referee[pair_id]["score"]))
        labse, complexity = audit_values(record, decisions)
        corpora = record.get("corpora", []) or [{"source": "unknown", "corpus": "unknown"}]
        dimensions = {
            "length": [bin_length(record)],
            "labse": [bin_labse(labse)],
            "complexity": [complexity],
            "strategy": [strategies.get(pair_id, "missing")],
            "corpus": [f"{item.get('source')}::{item.get('corpus')}" for item in corpora],
        }
        for dimension, values in dimensions.items():
            for value in values:
                grouped[(dimension, value)].append(scores)
        original_id = str(record.get("canonical_original_id") or pair_id)
        originals[original_id].append((pair_id, *scores))
        count += 1
    if set(lens) != set(referee) or len(lens) != count:
        raise ValueError("Prediction ID sets must exactly match the canonical input.")
    rows = []
    for (dimension, value), values in sorted(grouped.items()):
        lens_summary = summary([item[0] for item in values])
        referee_summary = summary([item[1] for item in values])
        rows.append({
            "dimension": dimension, "value": value, "pairs": len(values),
            "lens_mean": lens_summary["mean"], "lens_std": lens_summary["std"],
            "referee_mean": referee_summary["mean"], "referee_std": referee_summary["std"],
        })
    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_csv(output_dir / "metric_distributions_by_stratum.csv", rows)
    multi = [values for values in originals.values() if len(values) > 1]
    multi_report = {
        "canonical_original_groups": len(multi),
        "pairs": sum(len(values) for values in multi),
        "lens_mean_within_original_range": float(np.mean([
            max(item[1] for item in values) - min(item[1] for item in values) for values in multi
        ])) if multi else None,
        "referee_mean_within_original_range": float(np.mean([
            max(item[2] for item in values) - min(item[2] for item in values) for values in multi
        ])) if multi else None,
        "note": "Ranges describe discrimination, not correctness; correctness requires human judgments.",
    }
    report = {
        "schema": "feats-phase5-external-metric-strata-analysis-v1",
        "pairs": count, "strata_rows": len(rows),
        "multiple_simplifications": multi_report,
    }
    atomic_json(output_dir / "strata_analysis.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--lens", required=True, type=Path)
    parser.add_argument("--referee", required=True, type=Path)
    parser.add_argument("--decisions-root", required=True, type=Path)
    parser.add_argument("--strategies", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(args.input, args.lens, args.referee, args.decisions_root, args.strategies, args.output_dir), indent=2))


if __name__ == "__main__":
    main()

