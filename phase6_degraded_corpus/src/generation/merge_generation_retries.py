#!/usr/bin/env python3
"""Overlay retry generations on a complete base pilot while preserving order."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, write_jsonl


def merge(base: list[dict], retries: list[dict]) -> tuple[list[dict], dict]:
    base_ids = [row["canonical_pair_id"] for row in base]
    if len(base_ids) != len(set(base_ids)):
        raise ValueError("duplicate canonical_pair_id in base generations")
    retry_map = {}
    for row in retries:
        pair_id = row["canonical_pair_id"]
        if pair_id in retry_map:
            raise ValueError(f"duplicate canonical_pair_id in retries: {pair_id}")
        if pair_id not in set(base_ids):
            raise ValueError(f"retry not present in base: {pair_id}")
        retry_map[pair_id] = row
    transitions = Counter()
    output = []
    for row in base:
        retry = retry_map.get(row["canonical_pair_id"])
        if not retry:
            output.append(row)
            continue
        transitions[f'{row["status"]}->{retry["status"]}'] += 1
        output.append({**retry, "retry_of_status": row["status"]})
    return output, {
        "schema": "feats-phase6-retry-merge-report-v1",
        "base_records": len(base),
        "retry_records": len(retries),
        "output_records": len(output),
        "transitions": dict(sorted(transitions.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--retries", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    rows, report = merge(read_jsonl(args.base), read_jsonl(args.retries))
    write_jsonl(args.output, rows)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
