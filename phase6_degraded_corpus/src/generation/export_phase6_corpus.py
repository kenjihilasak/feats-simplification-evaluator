#!/usr/bin/env python3
"""Export one language's valid Phase 6 items as a scorer-ready corpus.

Each record is one original with its versions and a target score per version for its axis: pairs give the clean
simplification 1.0 and the degraded one 0.0; graded groups give clean 1.0, the mild version 0.5 and the strong one
(both edits) 0.0. Every text gets the same spacing (pre-tokenized sources such as PaCCSS-IT and CLEAR would
otherwise set the clean text apart from LLM rewrites), and a record whose versions differ only in spacing is dropped.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from phase6_degraded_corpus.src.annotation.build_s1_multilingual import uniform_spacing
from phase6_degraded_corpus.src.common.contracts import read_jsonl, write_jsonl

KEEP = ("canonical_pair_id", "canonical_original_id", "language", "corpus", "original")


def read(path: Path) -> list[dict]:
    return read_jsonl(path) if path.exists() else []


def records(run: Path) -> list[dict]:
    out = []
    for r in read(run / "scored/fose_pairs.jsonl"):
        if r["valid"]:
            out.append({**{k: r.get(k) for k in KEEP}, "axis": r["target_axis"], "format": "pair",
                        "operation": f'{r["target_axis"].lower()}_restore' if r["target_axis"] != "EXPL" else "expl_remove",
                        "versions": {"clean": r["clean_simplification"], "degraded": r["degraded_simplification"]},
                        "scores": {"clean": 1.0, "degraded": 0.0}})
    for g in read(run / "scored/fose_groups.jsonl"):
        if g["valid"]:
            mild = g["mild_version"]
            out.append({**{k: g.get(k) for k in KEEP}, "axis": g["target_axis"], "format": "graded",
                        "operation": f'{g["target_axis"].lower()}_graded',
                        "versions": {"clean": g["clean_simplification"], "mild": g["versions"][mild]["degraded"],
                                     "strong": g["versions"]["AB"]["degraded"]},
                        "scores": {"clean": 1.0, "mild": 0.5, "strong": 0.0}})
    for g in read(run / "scored/mod_groups.jsonl"):
        if g["valid"]:
            out.append({**{k: g.get(k) for k in KEEP}, "language": run.name.split("_")[1], "axis": "MOD", "format": "graded",
                        "operation": "mod_front_heavy+mod_sentence_reorder",
                        "versions": {"clean": g["clean_simplification"], "mild": g["versions"]["A"]["degraded"],
                                     "strong": g["versions"]["AB"]["degraded"]},
                        "scores": {"clean": 1.0, "mild": 0.5, "strong": 0.0}})
    for r in read(run / "scored/illoc.jsonl"):
        if r["yield"]:
            out.append({**{k: r.get(k) for k in KEEP}, "axis": "ILLOC", "format": "pair", "operation": r["operation"],
                        "versions": {"clean": r["clean_simplification"], "degraded": r["candidates"][r["selected_index"]]["degraded"]},
                        "scores": {"clean": 1.0, "degraded": 0.0}})
    return out


def spaced(record: dict) -> dict | None:
    high = bool(re.search(r"\w [;:!?]", record["versions"]["clean"]))
    versions = {k: uniform_spacing(v, high) for k, v in record["versions"].items()}
    if len(set(versions.values())) < len(versions):
        return None
    return {**record, "original": uniform_spacing(record["original"], high), "versions": versions,
            "schema": "feats-phase6-corpus-v2"}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-dir", type=Path, action="append", required=True)
    p.add_argument("--output-name", default="phase6_corpus.jsonl")
    args = p.parse_args()
    summary = {}
    for run in args.run_dir:
        raw = records(run)
        kept = [s for s in map(spaced, raw) if s]
        write_jsonl(run / "final" / args.output_name, kept)
        summary[run.name] = {"records": len(kept), "dropped_spacing_only": len(raw) - len(kept),
                             "by_axis_format": dict(sorted(Counter(f'{r["axis"]}:{r["format"]}' for r in kept).items()))}
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
