"""Rank Phase 5 scores against submitted Phase 4a strategy verdicts."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean, median


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def predictions(path: Path) -> dict[str, dict]:
    rows = read_jsonl(path)
    result = {str(row["canonical_pair_id"]): row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"Duplicate canonical_pair_id in {path}")
    return result


def percentile_ranks(values: list[float]) -> list[float]:
    if len(values) == 1:
        return [0.5]
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        average_rank = (start + end - 1) / 2
        for position in range(start, end):
            ranks[order[position]] = average_rank / (len(values) - 1)
        start = end
    return ranks


def score_summary(values: list[float]) -> dict:
    return {
        "count": len(values),
        "mean": mean(values) if values else None,
        "median": median(values) if values else None,
        "min": min(values) if values else None,
        "max": max(values) if values else None,
    }


def analyze(human_path: Path, lens_path: Path, referee_path: Path, output_dir: Path) -> dict:
    human = read_jsonl(human_path)
    human = [row for row in human if row.get("verdict") in {"correct", "incorrect"}]
    human_by_id = {str(row["canonical_pair_id"]): row for row in human}
    if len(human_by_id) != len(human):
        raise ValueError("Duplicate submitted human judgment")
    lens = predictions(lens_path)
    referee = predictions(referee_path)
    expected = set(human_by_id)
    if set(lens) != expected or set(referee) != expected:
        raise ValueError("Human and metric canonical_pair_id sets differ")

    ids = [str(row["canonical_pair_id"]) for row in human]
    lens_scores = [float(lens[pair_id]["score"]) for pair_id in ids]
    referee_scores = [float(referee[pair_id]["score"]) for pair_id in ids]
    lens_percentiles = percentile_ranks(lens_scores)
    referee_percentiles = percentile_ranks(referee_scores)
    rows = []
    for index, pair_id in enumerate(ids):
        judgment = human_by_id[pair_id]
        verdict = str(judgment["verdict"])
        # This is an exploratory tension indicator, not a classification error:
        # Phase 4a judges strategy detection while the metrics judge pair quality.
        lens_tension = 1 - lens_percentiles[index] if verdict == "correct" else lens_percentiles[index]
        referee_tension = 1 - referee_percentiles[index] if verdict == "correct" else referee_percentiles[index]
        rows.append({
            "canonical_pair_id": pair_id,
            "phase4a_task_id": judgment["task_id"],
            "candidate_strategy": judgment["candidate_strategy"],
            "human_verdict": verdict,
            "corrected_strategy": judgment.get("corrected_strategy") or "",
            "lens_salsa_score": lens_scores[index],
            "lens_percentile": lens_percentiles[index],
            "lens_apparent_tension": lens_tension,
            "referee_score": referee_scores[index],
            "referee_percentile": referee_percentiles[index],
            "referee_apparent_tension": referee_tension,
            "mean_apparent_tension": (lens_tension + referee_tension) / 2,
            "original": judgment["original"],
            "simple": judgment["simple"],
            "reviewer_notes": judgment.get("notes") or "",
        })
    rows.sort(key=lambda row: (-row["mean_apparent_tension"], row["canonical_pair_id"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "phase4a_apparent_tensions.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    report = {
        "schema": "feats-phase5-phase4a-strategy-association-v1",
        "pairs": len(rows),
        "verdicts": dict(Counter(row["human_verdict"] for row in rows)),
        "interpretation_warning": (
            "Phase 4a verdicts judge whether a candidate simplification strategy was detected "
            "correctly; LENS-SALSA and REFEREE score overall pair quality. Apparent tension "
            "is rank-based triage, not metric-vs-human classification disagreement."
        ),
        "tension_definition": (
            "For correct verdicts: 1-score_percentile; for incorrect verdicts: "
            "score_percentile. The two native score scales are never combined; only the two "
            "within-set tension ranks are averaged for triage."
        ),
        "by_verdict": {},
        "top_apparent_tensions": rows[: min(10, len(rows))],
    }
    for verdict in ("correct", "incorrect"):
        selected = [index for index, row in enumerate(human) if row["verdict"] == verdict]
        report["by_verdict"][verdict] = {
            "lens_salsa": score_summary([lens_scores[index] for index in selected]),
            "referee": score_summary([referee_scores[index] for index in selected]),
        }
    json_path = output_dir / "phase4a_strategy_association.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
