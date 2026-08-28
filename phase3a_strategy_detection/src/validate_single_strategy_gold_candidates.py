#!/usr/bin/env python3
"""Validate Phase 3a single-strategy gold-candidate artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from build_single_strategy_gold_candidates import (
    CODES,
    CODE_LABELS,
    QUALITY_TIERS,
    SELECTION_RULE,
    canonical_id,
    sha256,
)
from experiment_config import load_json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CANDIDATE_ROOT = (
    PROJECT_ROOT
    / "phase3a_strategy_detection"
    / "gold_candidates"
    / "2026-08-26_single_strategy_majority_vote_v1"
)


def load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Empty candidate manifest: {path}")
    return rows


def expected_tier(
    predictions: Mapping[str, Mapping[str, Any]], winner: str
) -> tuple[str, list[str]]:
    exact = [
        alias
        for alias, prediction in predictions.items()
        if prediction["predicted_codes"] == [winner]
    ]
    if len(exact) == 3:
        return "unanimous_exact_singleton", exact
    if len(exact) >= 2:
        return "majority_exact_singleton", exact
    return "label_majority_only", exact


def validate_record(
    record: Mapping[str, Any],
    language: str,
    model_aliases: list[str],
    seen_ids: set[str],
) -> tuple[str, int, str]:
    pair_id = canonical_id(record)
    if not pair_id or pair_id in seen_ids:
        raise ValueError(f"Missing or duplicate candidate ID: {pair_id!r}")
    seen_ids.add(pair_id)
    if record.get("language") != language:
        raise ValueError(f"Candidate language/path mismatch for {pair_id}")
    if not isinstance(record.get("original"), str) or not isinstance(
        record.get("simple"), str
    ):
        raise ValueError(f"Missing canonical texts for {pair_id}")
    if record.get("candidate_status") != "unreviewed_model_consensus":
        raise ValueError(f"Unexpected candidate status for {pair_id}")
    if record.get("selection_rule") != SELECTION_RULE:
        raise ValueError(f"Unexpected selection rule for {pair_id}")

    winner = str(record.get("candidate_strategy_code", ""))
    if winner not in CODES:
        raise ValueError(f"Invalid candidate strategy for {pair_id}")
    if record.get("candidate_strategy_label") != CODE_LABELS[winner]:
        raise ValueError(f"Candidate code/label mismatch for {pair_id}")

    predictions = record.get("model_predictions")
    if not isinstance(predictions, dict) or list(predictions) != model_aliases:
        raise ValueError(f"Candidate model inventory/order mismatch for {pair_id}")
    normalized_codes: dict[str, list[str]] = {}
    for alias in model_aliases:
        prediction = predictions[alias]
        if not isinstance(prediction, dict):
            raise ValueError(f"Invalid prediction for {alias}/{pair_id}")
        raw_codes = prediction.get("predicted_codes")
        raw_scores = prediction.get("strategy_scores")
        if not isinstance(raw_codes, list) or not isinstance(raw_scores, dict):
            raise ValueError(f"Invalid strategy fields for {alias}/{pair_id}")
        codes = [str(code) for code in raw_codes]
        if (
            len(set(codes)) != len(codes)
            or any(code not in CODES for code in codes)
            or codes != [code for code in CODES if code in codes]
            or int(prediction.get("strategy_count", -1)) != len(codes)
        ):
            raise ValueError(f"Invalid predicted codes for {alias}/{pair_id}")
        if set(raw_scores) != set(CODES):
            raise ValueError(f"Invalid score inventory for {alias}/{pair_id}")
        scores = [float(raw_scores[code]) for code in CODES]
        if any(
            not math.isfinite(score) or not 0.0 <= score <= 1.0
            for score in scores
        ):
            raise ValueError(f"Invalid strategy score for {alias}/{pair_id}")
        normalized_codes[alias] = codes

    vote_counts = {
        code: sum(code in codes for codes in normalized_codes.values())
        for code in CODES
    }
    if record.get("label_vote_counts") != vote_counts:
        raise ValueError(f"Stored/recomputed votes differ for {pair_id}")
    consensus = [code for code in CODES if vote_counts[code] >= 2]
    if consensus != [winner]:
        raise ValueError(f"Candidate is not a majority singleton: {pair_id}")
    votes = vote_counts[winner]
    if int(record.get("majority_votes", -1)) != votes:
        raise ValueError(f"Incorrect majority strength for {pair_id}")
    supporters = [
        alias for alias in model_aliases if winner in normalized_codes[alias]
    ]
    if record.get("supporting_models") != supporters:
        raise ValueError(f"Incorrect supporting models for {pair_id}")
    tier, exact = expected_tier(predictions, winner)
    if record.get("quality_tier") != tier:
        raise ValueError(f"Incorrect quality tier for {pair_id}")
    if record.get("exact_singleton_supporting_models") != exact:
        raise ValueError(f"Incorrect exact-singleton support for {pair_id}")
    return winner, votes, tier


def validate(candidate_root: Path) -> dict[str, Any]:
    candidate_root = candidate_root.resolve()
    summary = load_json(candidate_root / "reports" / "summary.json")
    config = load_json(candidate_root / "candidate_config.json")
    if summary.get("schema") != "feats-phase3a-single-strategy-summary-v1":
        raise ValueError("Unexpected candidate summary schema")
    if config.get("schema") != "feats-phase3a-gold-candidate-config-v1":
        raise ValueError("Unexpected candidate config schema")
    if summary.get("candidate_id") != config.get("candidate_id"):
        raise ValueError("Candidate config/summary ID mismatch")
    model_aliases = [str(value) for value in summary["required_models"]]
    if model_aliases != [str(value) for value in config["required_models"]]:
        raise ValueError("Candidate config/summary model mismatch")

    manifest = load_manifest(candidate_root / "CANDIDATE_MANIFEST.csv")
    expected_files = {str(row["output_file"]) for row in manifest}
    observed_files = {
        path.relative_to(candidate_root).as_posix()
        for path in (candidate_root / "data").glob("*/*.jsonl")
        if path.is_file()
    }
    if expected_files != observed_files:
        raise ValueError(
            "Candidate data layout differs from manifest; "
            f"missing={sorted(expected_files - observed_files)}, "
            f"extra={sorted(observed_files - expected_files)}"
        )

    seen_ids: set[str] = set()
    language_counts: Counter[str] = Counter()
    strategy_counts: Counter[str] = Counter()
    vote_counts: Counter[int] = Counter()
    tier_counts: Counter[str] = Counter()
    validated_files: list[dict[str, Any]] = []
    for manifest_row in manifest:
        language = str(manifest_row["language"])
        path = candidate_root / str(manifest_row["output_file"])
        if path.stat().st_size != int(manifest_row["bytes"]):
            raise ValueError(f"Candidate byte size differs from manifest: {path}")
        actual_sha256 = sha256(path)
        if actual_sha256 != manifest_row["sha256"]:
            raise ValueError(f"Candidate hash differs from manifest: {path}")
        line_count = 0
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"Invalid JSON at {path}:{line_number}"
                    ) from error
                if not isinstance(record, dict):
                    raise ValueError(f"Expected an object at {path}:{line_number}")
                winner, votes, tier = validate_record(
                    record, language, model_aliases, seen_ids
                )
                line_count += 1
                language_counts[language] += 1
                strategy_counts[winner] += 1
                vote_counts[votes] += 1
                tier_counts[tier] += 1
        if line_count != int(manifest_row["candidate_pairs"]):
            raise ValueError(f"Candidate line count differs from manifest: {path}")
        validated_files.append(
            {
                "language": language,
                "file": manifest_row["output_file"],
                "pairs": line_count,
                "bytes": path.stat().st_size,
                "sha256": actual_sha256,
            }
        )

    observed_pairs = len(seen_ids)
    if observed_pairs != int(summary["candidate_pairs"]):
        raise ValueError("Validated candidate total differs from summary")
    expected_languages = {
        str(row["language"]): int(row["candidate_pairs"])
        for row in summary["languages"]
    }
    if dict(language_counts) != expected_languages:
        raise ValueError("Validated language totals differ from summary")
    expected_strategies = {
        str(row["strategy_code"]): int(row["candidate_pairs"])
        for row in summary["strategies"]
    }
    if dict(strategy_counts) != {
        code: count for code, count in expected_strategies.items() if count
    }:
        raise ValueError("Validated strategy totals differ from summary")
    if vote_counts != Counter(
        {
            2: int(summary["vote_strength"]["majority_2_votes_pairs"]),
            3: int(summary["vote_strength"]["unanimous_3_votes_pairs"]),
        }
    ):
        raise ValueError("Validated vote strengths differ from summary")
    if tier_counts != Counter(
        {tier: int(summary["quality_tiers"][tier]) for tier in QUALITY_TIERS}
    ):
        raise ValueError("Validated quality tiers differ from summary")

    return {
        "schema": "feats-phase3a-single-strategy-validation-v1",
        "candidate_id": summary["candidate_id"],
        "valid": True,
        "candidate_pairs": observed_pairs,
        "unique_canonical_pair_ids": len(seen_ids),
        "languages": dict(sorted(language_counts.items())),
        "strategies": {code: strategy_counts[code] for code in CODES},
        "vote_strength": {str(vote): vote_counts[vote] for vote in (2, 3)},
        "quality_tiers": {tier: tier_counts[tier] for tier in QUALITY_TIERS},
        "files": validated_files,
        "errors": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate-root", type=Path, default=DEFAULT_CANDIDATE_ROOT
    )
    args = parser.parse_args()
    result = validate(args.candidate_root)
    validation_path = args.candidate_root / "reports" / "validation.json"
    validation_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
