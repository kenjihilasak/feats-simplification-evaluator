#!/usr/bin/env python3
"""Expand the audited-original exclusion list from ids to text matches.

Human-audited heldout originals were excluded from the full corpus by
`canonical_original_id`. The same sentence can carry another id (whitespace or
punctuation variants, other Wikipedia revisions), so Phase 7 found leakage. This adds
every allocated original that matches an audited original by strong key or by word
Jaccard >= threshold — the same rule used for reserved evaluation originals.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl
from phase6_degraded_corpus.src.selection.freeze_evaluation_originals import strong_key
from phase6_degraded_corpus.src.selection.select_mmi_pools import ReservedMatcher


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audited-splits", type=Path, nargs="+", required=True)
    parser.add_argument("--allocated", type=Path, required=True, help="all allocated rows of the corpus")
    parser.add_argument("--excluded", type=Path, required=True, help="existing id list; rewritten in place")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.8)
    args = parser.parse_args()

    audited = {}
    for path in args.audited_splits:
        for row in read_jsonl(path):
            audited[row["canonical_original_id"]] = row["original"]
    matcher = ReservedMatcher(
        [{"strong_key": strong_key(text), "original": text} for text in audited.values()], args.threshold
    )
    existing = {line.strip() for line in args.excluded.read_text().splitlines() if line.strip()}
    added = []
    for row in read_jsonl(args.allocated):
        original_id = row["canonical_original_id"]
        if original_id in existing or original_id in audited:
            continue
        hit = matcher.match(row["original"])
        if hit:
            added.append({"canonical_original_id": original_id, "original": row["original"], **hit})
    ids = sorted(existing | set(audited) | {a["canonical_original_id"] for a in added})
    args.excluded.write_text("\n".join(ids) + "\n")
    report = {"audited_originals": len(audited), "previous_exclusions": len(existing),
              "added_text_matches": len(added), "total_exclusions": len(ids), "threshold": args.threshold,
              "matches": added}
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "matches"}, indent=2))


if __name__ == "__main__":
    main()
