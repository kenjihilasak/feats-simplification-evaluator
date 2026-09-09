"""Compare external-metric rankings and optionally evaluate human judgments."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import kendalltau, rankdata, spearmanr
from sklearn.metrics import average_precision_score, roc_auc_score

from common import atomic_csv, atomic_json, read_jsonl


def load_predictions(path: Path) -> dict[str, dict[str, Any]]:
    rows = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            pair_id = str(row["canonical_pair_id"])
            if pair_id in rows:
                raise ValueError(f"Duplicate prediction {pair_id}: {path}")
            rows[pair_id] = row
    return rows


def summary(values: list[float]) -> dict[str, Any]:
    array = np.asarray(values, dtype=float)
    return {
        "count": int(array.size), "mean": float(array.mean()),
        "std": float(array.std()), "min": float(array.min()),
        "p25": float(np.quantile(array, .25)), "median": float(np.median(array)),
        "p75": float(np.quantile(array, .75)), "max": float(array.max()),
    }


def source_groups(inputs: list[dict[str, Any]]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for row in inputs:
        pair_id = str(row["canonical_pair_id"])
        corpora = row.get("corpora", []) or [{"source": "unknown", "corpus": "unknown"}]
        for corpus in corpora:
            groups[f"{corpus.get('source')}::{corpus.get('corpus')}"].append(pair_id)
    return groups


def read_human(path: Path) -> dict[str, str]:
    if path.suffix == ".jsonl":
        with path.open(encoding="utf-8") as handle:
            rows = [json.loads(line) for line in handle]
    else:
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    result = {}
    for row in rows:
        judgment = str(row.get("judgment") or row.get("decision") or "").lower()
        if judgment in {"correct", "incorrect", "uncertain"}:
            result[str(row["canonical_pair_id"])] = judgment
    return result


def grouped_bootstrap_auc(
    y: np.ndarray, scores: np.ndarray, groups: np.ndarray, seed: int, repeats: int
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    unique = np.unique(groups)
    estimates = []
    members = {group: np.flatnonzero(groups == group) for group in unique}
    for _ in range(repeats):
        sampled = rng.choice(unique, size=len(unique), replace=True)
        indices = np.concatenate([members[group] for group in sampled])
        if len(np.unique(y[indices])) == 2:
            estimates.append(roc_auc_score(y[indices], scores[indices]))
    if not estimates:
        return {"low": None, "median": None, "high": None, "valid_repeats": 0}
    return {
        "low": float(np.quantile(estimates, .025)),
        "median": float(np.median(estimates)),
        "high": float(np.quantile(estimates, .975)),
        "valid_repeats": len(estimates),
    }


def analyze(
    input_path: Path, lens_path: Path, referee_path: Path, output_dir: Path,
    human_path: Path | None = None, bootstrap_repeats: int = 1000,
) -> dict[str, Any]:
    inputs = list(read_jsonl(input_path))
    by_id = {str(row["canonical_pair_id"]): row for row in inputs}
    lens, referee = load_predictions(lens_path), load_predictions(referee_path)
    expected = set(by_id)
    if set(lens) != expected or set(referee) != expected:
        raise ValueError("Both metric ID sets must exactly equal the input ID set.")
    ids = [str(row["canonical_pair_id"]) for row in inputs]
    lens_values = np.array([float(lens[value]["score"]) for value in ids])
    referee_values = np.array([float(referee[value]["score"]) for value in ids])
    lens_ranks, referee_ranks = rankdata(lens_values), rankdata(referee_values)
    denom = max(1, len(ids) - 1)
    disagreement = np.abs(lens_ranks - referee_ranks) / denom
    worst = np.argsort(-disagreement)[:100]
    output_dir.mkdir(parents=True, exist_ok=True)
    disagreement_rows = [{
        "canonical_pair_id": ids[index],
        "normalized_rank_gap": float(disagreement[index]),
        "lens_salsa_score": float(lens_values[index]),
        "referee_score": float(referee_values[index]),
        "original": by_id[ids[index]]["original"],
        "simple": by_id[ids[index]]["simple"],
    } for index in worst]
    atomic_csv(output_dir / "largest_rank_disagreements.csv", disagreement_rows)
    report: dict[str, Any] = {
        "schema": "feats-phase5-external-metric-analysis-v1",
        "pairs": len(ids),
        "warning": "Native scores are not directly comparable; agreement uses ranks.",
        "metrics": {
            "lens_salsa": summary(lens_values.tolist()),
            "referee": summary(referee_values.tolist()),
        },
        "rank_agreement": {
            "spearman": float(spearmanr(lens_values, referee_values).statistic),
            "kendall": float(kendalltau(lens_values, referee_values).statistic),
        },
        "by_corpus": {},
    }
    positions = {pair_id: index for index, pair_id in enumerate(ids)}
    for name, group_ids in sorted(source_groups(inputs).items()):
        index = [positions[value] for value in group_ids]
        report["by_corpus"][name] = {
            "lens_salsa": summary(lens_values[index].tolist()),
            "referee": summary(referee_values[index].tolist()),
        }
    if human_path is not None:
        human = read_human(human_path)
        determinate = [value for value in ids if human.get(value) in {"correct", "incorrect"}]
        uncertain = sum(human.get(value) == "uncertain" for value in ids)
        if determinate:
            index = np.array([positions[value] for value in determinate])
            y = np.array([human[value] == "correct" for value in determinate], dtype=int)
            groups = np.array([
                str(by_id[value].get("canonical_original_id") or value) for value in determinate
            ])
            human_report = {"determinate": len(determinate), "uncertain_excluded": uncertain, "metrics": {}}
            has_both_classes = len(np.unique(y)) == 2
            for alias, values in (("lens_salsa", lens_values), ("referee", referee_values)):
                selected = values[index]
                human_report["metrics"][alias] = {
                    "spearman": float(spearmanr(y, selected).statistic),
                    "kendall": float(kendalltau(y, selected).statistic),
                    "auroc": float(roc_auc_score(y, selected)) if has_both_classes else None,
                    "average_precision": float(average_precision_score(y, selected)) if has_both_classes else None,
                    "grouped_bootstrap_auroc_95ci": grouped_bootstrap_auc(
                        y, selected, groups, 20260908, bootstrap_repeats
                    ) if has_both_classes else None,
                }
            report["human_evaluation"] = human_report
        else:
            report["human_evaluation"] = {"determinate": 0, "uncertain_excluded": uncertain}
    atomic_json(output_dir / "analysis.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--lens", required=True, type=Path)
    parser.add_argument("--referee", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--human", type=Path)
    parser.add_argument("--bootstrap-repeats", type=int, default=1000)
    args = parser.parse_args()
    print(json.dumps(analyze(args.input, args.lens, args.referee, args.output_dir, args.human, args.bootstrap_repeats), indent=2))


if __name__ == "__main__":
    main()

