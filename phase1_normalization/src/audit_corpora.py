#!/usr/bin/env python3
"""Audit the complete canonical Phase 1 corpus."""

from __future__ import annotations

import json
from collections import Counter

from common import DATA_ROOT, REPORT_ROOT, iter_jsonl, write_json


REQUIRED_FIELDS = {
    "id", "original_id", "language", "source", "corpus", "upstream_split",
    "original", "simple", "reference_index", "source_dataset",
    "source_revision", "source_row",
}
VALID_SPLITS = {"train", "validation", "test", None}
EXPECTED_FILES = 29
EXPECTED_PAIRS = 1_454_003


def audit() -> dict[str, object]:
    files = sorted(DATA_ROOT.glob("*/*.jsonl"))
    ids: set[str] = set()
    by_source: Counter[str] = Counter()
    by_language: Counter[str] = Counter()
    by_split: Counter[str] = Counter()
    missing = empty = invalid_split = invalid_layout = duplicates = total = 0

    for path in files:
        if path.parent.parent != DATA_ROOT:
            invalid_layout += 1
        for record in iter_jsonl(path):
            total += 1
            missing += bool(REQUIRED_FIELDS.difference(record))
            empty += not bool(record.get("original")) or not bool(record.get("simple"))
            invalid_split += record.get("upstream_split") not in VALID_SPLITS
            pair_id = str(record.get("id", ""))
            if pair_id in ids:
                duplicates += 1
            ids.add(pair_id)
            by_source[str(record.get("source"))] += 1
            by_language[str(record.get("language"))] += 1
            split = record.get("upstream_split")
            by_split["null" if split is None else str(split)] += 1

    valid = (
        len(files) == EXPECTED_FILES
        and total == EXPECTED_PAIRS
        and len(ids) == total
        and missing == empty == invalid_split == invalid_layout == duplicates == 0
    )
    report = {
        "valid": valid,
        "jsonl_files": len(files),
        "normalized_pairs": total,
        "normalized_bytes": sum(path.stat().st_size for path in files),
        "unique_ids": len(ids),
        "duplicate_ids": duplicates,
        "missing_field_records": missing,
        "empty_text_records": empty,
        "invalid_upstream_split_records": invalid_split,
        "invalid_layout_records": invalid_layout,
        "records_by_source": dict(sorted(by_source.items())),
        "records_by_language": dict(sorted(by_language.items())),
        "records_by_upstream_split": dict(sorted(by_split.items())),
    }
    write_json(REPORT_ROOT / "overall_validation.json", report)
    if not valid:
        raise RuntimeError(json.dumps(report, ensure_ascii=False))
    return report


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False))
