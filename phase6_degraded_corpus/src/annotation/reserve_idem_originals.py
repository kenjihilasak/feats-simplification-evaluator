#!/usr/bin/env python3
"""Reserve the originals of the iDEM S1 items for evaluation and remove them from the Phase 6 training corpora.

The iDEM items (build_idem_s1_items.py) give human judgements on system outputs, used to evaluate the FEATS scorers,
so no training corpus may contain their originals (as SimpEval-2022 and the other frozen evaluation sources in
English). This script:
- writes `runs/idem_s1_v1/reserved_original_membership.jsonl` (same schema as the English reserved originals:
  `original`, `sources`, `strong_key`), to add to `exclude_files` in the language's experiment configs;
- removes from each `final/phase6_corpus.jsonl` given (`--corpus`) every record whose original matches a reserved one
  (strong key, as ReservedMatcher), keeping the former file as `phase6_corpus.before_idem_reservation.jsonl` and a
  report of what was removed.
"""
from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, write_jsonl
from phase6_degraded_corpus.src.selection.freeze_evaluation_originals import strong_key

RUN = Path("phase6_degraded_corpus/runs/idem_s1_v1")


def reserved(langs: list[str]) -> list[dict]:
    rows = {}
    for lang in langs:
        sel = json.loads((RUN / lang / "selection.json").read_text(encoding="utf-8"))
        for r in sel["items"] + sel["few_shot"]:
            rows.setdefault(strong_key(r["original"]), {"original": r["original"], "sources": [f"idem_s1_items_{lang}"],
                                                        "strong_key": strong_key(r["original"])})
    return sorted(rows.values(), key=lambda r: r["strong_key"])


def filter_corpus(path: Path, keys: set[str]) -> dict:
    rows = read_jsonl(path)
    kept = [r for r in rows if strong_key(r["original"]) not in keys]
    removed = [r for r in rows if strong_key(r["original"]) in keys]
    if removed:
        backup = path.with_name("phase6_corpus.before_idem_reservation.jsonl")
        if not backup.exists():
            shutil.copy2(path, backup)
        write_jsonl(path, kept)
    return {"corpus": str(path), "records": len(rows), "removed": len(removed),
            "removed_by_axis": dict(Counter(r["axis"] for r in removed))}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--language", nargs="+", default=["ca", "es", "it"])
    p.add_argument("--corpus", type=Path, nargs="+", required=True, help="final/phase6_corpus.jsonl files to filter")
    args = p.parse_args()
    rows = reserved(args.language)
    write_jsonl(RUN / "reserved_original_membership.jsonl", rows)
    keys = {r["strong_key"] for r in rows}
    report = {"reserved_originals": len(rows), "corpora": [filter_corpus(c, keys) for c in args.corpus]}
    (RUN / "reservation_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
