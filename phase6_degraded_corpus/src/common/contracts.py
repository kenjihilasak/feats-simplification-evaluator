"""Contracts shared by Phase 6 selection and generation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

SCHEMA = "feats-phase6-clean-candidate-v1"


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def stable_key(seed: int, value: str) -> str:
    return hashlib.sha256(f"{seed}:{value}".encode()).hexdigest()


def validate_candidate(row: dict) -> None:
    required = {
        "schema", "selection_tier", "canonical_pair_id", "canonical_original_id",
        "language", "original", "clean_simplification", "source", "corpus",
        "length_bin", "predicted_strategy", "clean_review_status",
        "clean_source_tier", "target_simple_pass", "phase2a_run_id",
        "phase2b_variant_id", "predicted_strategy_count",
        "predicted_strategy_codes",
    }
    missing = sorted(required - row.keys())
    if missing:
        raise ValueError(f"missing fields: {missing}")
    if row["schema"] != SCHEMA:
        raise ValueError(f"unexpected schema: {row['schema']}")
    if row["selection_tier"] not in {"reviewed_anchor", "candidate", "backup"}:
        raise ValueError("invalid selection_tier")
    if row["clean_review_status"] not in {"accepted", "pending", "rejected"}:
        raise ValueError("invalid clean_review_status")
    if not row["original"].strip() or not row["clean_simplification"].strip():
        raise ValueError("texts must be non-empty")
