#!/usr/bin/env python3
"""Select manifest rows whose latest generation has a retryable status."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from contracts import read_jsonl, write_jsonl


def select(manifest: list[dict], generated: list[dict], statuses: set[str]) -> tuple[list[dict], dict]:
    plans = {row["canonical_pair_id"]: row for row in manifest}
    if len(plans) != len(manifest):
        raise ValueError("duplicate canonical_pair_id in manifest")
    selected = []
    for record in generated:
        if record.get("status") not in statuses:
            continue
        pair_id = record["canonical_pair_id"]
        if pair_id not in plans:
            raise ValueError(f"unknown canonical_pair_id: {pair_id}")
        selected.append(plans[pair_id])
    ids = [row["canonical_pair_id"] for row in selected]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate retry selection")
    selected.sort(key=lambda row: (row["target_axis"], row["canonical_pair_id"]))
    return selected, {
        "schema": "feats-phase6-retry-selection-report-v1",
        "records": len(selected),
        "statuses": sorted(statuses),
        "by_axis": dict(sorted(Counter(row["target_axis"] for row in selected).items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--generated", type=Path, required=True)
    parser.add_argument("--status", action="append", default=["failed_parse"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    rows, report = select(
        read_jsonl(args.manifest), read_jsonl(args.generated), set(args.status)
    )
    write_jsonl(args.output, rows)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
