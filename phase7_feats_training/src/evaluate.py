"""Grouped-bootstrap correlations, paired comparisons, and pairwise accuracy."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import kendalltau, pearsonr, spearmanr

from contracts import atomic_json, read_jsonl


def correlation(rows: list[dict], score: str, method: str = "spearman") -> float:
    functions = {"spearman": spearmanr, "kendall": kendalltau, "pearson": pearsonr}
    value = functions[method]([row[score] for row in rows], [row["human_score"] for row in rows]).statistic
    return float(value)


def grouped_bootstrap(rows: list[dict], score: str, reps: int, seed: int,
                      comparison: str | None = None) -> dict:
    by_original: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_original[row["original_id"]].append(row)
    keys = sorted(by_original)
    rng, values = np.random.default_rng(seed), []
    for _ in range(reps):
        sampled = rng.choice(keys, size=len(keys), replace=True)
        sample = [row for key in sampled for row in by_original[key]]
        estimate = correlation(sample, score)
        if comparison:
            estimate -= correlation(sample, comparison)
        if np.isfinite(estimate):
            values.append(estimate)
    point = correlation(rows, score) - (correlation(rows, comparison) if comparison else 0.0)
    return {"estimate": point, "ci95": [float(x) for x in np.quantile(values, [0.025, 0.975])],
            "bootstrap_reps": reps, "group_count": len(keys), "comparison": comparison}


def evaluate_ratings(rows: list[dict], score_fields: list[str], reps: int, seed: int) -> dict:
    result = {}
    for score in score_fields:
        result[score] = {"spearman": grouped_bootstrap(rows, score, reps, seed),
                         "kendall": correlation(rows, score, "kendall")}
    return result


def pairwise(rows: list[dict], score: str) -> dict:
    included = [row for row in rows if row.get("included", True)]
    wins = [float(row[f"clean_{score}"] > row[f"degraded_{score}"]) for row in included]
    by_source: dict[str, list[float]] = defaultdict(list)
    by_operation: dict[str, list[float]] = defaultdict(list)
    for row, win in zip(included, wins):
        by_source[row["source"]].append(win)
        by_operation[row["operation"]].append(win)
    return {"accuracy": float(np.mean(wins)), "n": len(wins),
            "by_source": {key: float(np.mean(value)) for key, value in sorted(by_source.items())},
            "by_operation": {key: float(np.mean(value)) for key, value in sorted(by_operation.items())}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--score-fields", nargs="+", required=True)
    parser.add_argument("--kind", choices=("ratings", "pairwise"), required=True)
    parser.add_argument("--bootstrap-reps", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260930)
    args = parser.parse_args()
    rows = list(read_jsonl(args.input))
    result = (evaluate_ratings(rows, args.score_fields, args.bootstrap_reps, args.seed)
              if args.kind == "ratings" else {score: pairwise(rows, score) for score in args.score_fields})
    atomic_json(args.output, {"schema": "feats-phase7-evaluation-v1", "kind": args.kind,
                              "input": str(args.input), "metrics": result})


if __name__ == "__main__":
    main()
