#!/usr/bin/env python3
"""Record the fixed manual checker calibration sample and derived thresholds."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl

REJECTED = {
    "pair:en:e43b79139e521498a5fe4e3db73d762d4bcf9a0ac7e1152187fe5a7f585afd35":
        "Ungrammatical fragments: 'Performing as ...' and 'They the children ...'.",
    "pair:en:d7f44da803a3d1d7c4a946cc777d1f9e35239c7bcc657e9d89846243705ca5a5":
        "Ungrammatical phrase: 'the eldest surviving the daughter'.",
}


def quantile(values: list[float], probability: float) -> float:
    values = sorted(values)
    position = (len(values) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    pool_dir = Path(config["output_dir"])
    candidates = [
        row
        for row in read_jsonl(pool_dir / "structural_candidates.jsonl")
        if row["corpus"] == "WikiAutoEN"
    ]
    candidates.sort(
        key=lambda row: hashlib.sha256(
            f"{config['seed']}:calibration:{row['canonical_pair_id']}".encode()
        ).hexdigest()
    )
    sample = candidates[:20]
    scores = {
        row["canonical_pair_id"]: row
        for row in read_jsonl(Path(config["quality_scores_file"]))
    }
    cases = []
    accepted_scores = []
    for row in sample:
        rejected_reason = REJECTED.get(row["canonical_pair_id"])
        accepted = rejected_reason is None
        score = scores[row["canonical_pair_id"]]
        if accepted:
            accepted_scores.append(score["acceptability"])
        cases.append(
            {
                "canonical_pair_id": row["canonical_pair_id"],
                "original": row["original"],
                "clean_simplification": row["clean_simplification"],
                "human_fluency_acceptable": accepted,
                "note": rejected_reason or "Acceptable in the manual fluency spot-check.",
                "acceptability": score["acceptability"],
                "entailment": score["entailment"],
            }
        )
    tau = round(quantile(accepted_scores, 0.10), 8)
    median = quantile(accepted_scores, 0.50)
    delta = round(median - tau, 8)
    if tau != config["tau_accept"] or delta != config["delta"]:
        raise ValueError(
            f"config thresholds differ: derived tau={tau}, delta={delta}; "
            f"config tau={config['tau_accept']}, delta={config['delta']}"
        )
    report = {
        "schema": "feats-phase6-mmi-checker-calibration-v1",
        "sample_rule": "20 WikiAutoEN structural candidates ordered by stable SHA-256 calibration key",
        "human_audit": {"accepted": len(accepted_scores), "rejected": len(cases) - len(accepted_scores)},
        "tau_accept": {
            "value": tau,
            "definition": "10th percentile of CoLA acceptable-class probability among manually accepted cases",
        },
        "delta": {
            "value": delta,
            "definition": "median minus 10th percentile among the same accepted clean cases",
        },
        "acceptability_class_index": 0,
        "cases": cases,
    }
    output = pool_dir / "checker_calibration.json"
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in ("human_audit", "tau_accept", "delta")}, indent=2))


if __name__ == "__main__":
    main()
