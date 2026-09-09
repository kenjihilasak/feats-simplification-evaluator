"""Evaluate Phase 5 metrics against the Phase 4a binary decision policy."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

from sklearn.metrics import average_precision_score, roc_auc_score


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_predictions(path: Path) -> dict[str, float]:
    rows = read_jsonl(path)
    result = {str(row["canonical_pair_id"]): float(row["score"]) for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"Duplicate canonical_pair_id in {path}")
    return result


def percentile_ranks(values: list[float]) -> list[float]:
    if len(values) == 1:
        return [0.5]
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        rank = (start + end - 1) / 2 / (len(values) - 1)
        for position in range(start, end):
            ranks[order[position]] = rank
        start = end
    return ranks


def summary(values: list[float]) -> dict:
    return {
        "count": len(values),
        "mean": mean(values) if values else None,
        "median": median(values) if values else None,
        "min": min(values) if values else None,
        "max": max(values) if values else None,
    }


def analyze(human_path: Path, lens_path: Path, referee_path: Path, output_dir: Path) -> dict:
    human = read_jsonl(human_path)
    if any(row.get("human_label") not in {"positive", "negative"} for row in human):
        raise ValueError("Every included row must have a positive/negative human_label")
    by_id = {str(row["canonical_pair_id"]): row for row in human}
    if len(by_id) != len(human):
        raise ValueError("Duplicate human decision")
    lens = load_predictions(lens_path)
    referee = load_predictions(referee_path)
    expected = set(by_id)
    if set(lens) != expected or set(referee) != expected:
        raise ValueError("Human and metric canonical_pair_id sets differ")

    ids = [str(row["canonical_pair_id"]) for row in human]
    labels = [1 if by_id[pair_id]["human_label"] == "positive" else 0 for pair_id in ids]
    lens_scores = [lens[pair_id] for pair_id in ids]
    referee_scores = [referee[pair_id] for pair_id in ids]
    lens_pct = percentile_ranks(lens_scores)
    referee_pct = percentile_ranks(referee_scores)
    rows = []
    for index, pair_id in enumerate(ids):
        judgment = by_id[pair_id]
        positive = labels[index] == 1
        lens_disagreement = 1 - lens_pct[index] if positive else lens_pct[index]
        referee_disagreement = 1 - referee_pct[index] if positive else referee_pct[index]
        rows.append({
            "canonical_pair_id": pair_id,
            "phase4a_task_id": judgment["task_id"],
            "human_label": judgment["human_label"],
            "decision_type": judgment["decision_type"],
            "candidate_strategy": judgment["candidate_strategy"],
            "corrected_strategy": judgment.get("corrected_strategy") or "",
            "lens_salsa_score": lens_scores[index],
            "lens_percentile": lens_pct[index],
            "lens_rank_disagreement": lens_disagreement,
            "referee_score": referee_scores[index],
            "referee_percentile": referee_pct[index],
            "referee_rank_disagreement": referee_disagreement,
            "mean_rank_disagreement": (lens_disagreement + referee_disagreement) / 2,
            "original": judgment["original"],
            "simple": judgment["simple"],
            "reviewer_notes": judgment.get("notes") or "",
        })
    rows.sort(key=lambda row: (-row["mean_rank_disagreement"], row["canonical_pair_id"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "human_metric_disagreements.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    groups: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(human):
        groups[row["human_label"]].append(index)
    report = {
        "schema": "feats-phase5-phase4a-binary-evaluation-v1",
        "pairs": len(ids),
        "policy": {
            "positive": ["submitted:correct"],
            "negative": ["submitted:incorrect", "submitted:uncertain", "later"],
            "excluded": ["draft"],
        },
        "labels": dict(Counter(row["human_label"] for row in human)),
        "decision_types": dict(Counter(row["decision_type"] for row in human)),
        "metrics": {
            "lens_salsa": {
                "auroc": roc_auc_score(labels, lens_scores),
                "average_precision": average_precision_score(labels, lens_scores),
            },
            "referee": {
                "auroc": roc_auc_score(labels, referee_scores),
                "average_precision": average_precision_score(labels, referee_scores),
            },
        },
        "by_label": {},
        "interpretation_warning": (
            "The requested binary policy treats Later as negative. Phase 4a decisions "
            "primarily judge candidate-strategy correctness, while LENS-SALSA and REFEREE "
            "score overall pair quality; results are exploratory until quality labels exist."
        ),
        "top_rank_disagreements": rows[: min(10, len(rows))],
    }
    for label, indices in groups.items():
        report["by_label"][label] = {
            "lens_salsa": summary([lens_scores[index] for index in indices]),
            "referee": summary([referee_scores[index] for index in indices]),
        }
    (output_dir / "binary_evaluation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--human", required=True, type=Path)
    parser.add_argument("--lens", required=True, type=Path)
    parser.add_argument("--referee", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(args.human, args.lens, args.referee, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
