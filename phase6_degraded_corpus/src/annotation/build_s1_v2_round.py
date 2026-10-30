#!/usr/bin/env python3
"""Build an S1 round from a v2 examples file (`runs/annotation_v2/s1_<lang>_examples_*.csv`).

Case ids are those of the examples file, so a selection made on the CSV (Serge's) maps to the loaded items. The
interface shows two or three versions, so each case keeps the clean text and at most two degraded versions:
- OMIT, SYN, MOD graded groups: mild and strong; pairs: the degraded version.
- MEANING and FLUENCY: the mildest and the most severe level (e.g. mild loss and contradiction); the neutral trim
  (score 1.0) is left out.
- ILLOC: the degradation and, where present, the direct paraphrase (score 1.0, expected tie with the clean text).
Labels X/Y/Z are shuffled, items are shuffled across axes, and controls are identical pairs, as in the v1 rounds.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, OrderedDict
from pathlib import Path

from phase6_degraded_corpus.src.annotation.build_s1_meta import corpus_index, dataset
from phase6_degraded_corpus.src.annotation.build_s1_multilingual import SEED, controls, displayed
from phase6_degraded_corpus.src.annotation.build_s1_round import item
from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl

AXIS_CODES = {"Meaning": "MEANING", "Fluency": "FLUENCY", "Omission": "OMIT", "Synonymy": "SYN",
              "Explanation": "EXPL", "Modulation": "MOD", "Illocution": "ILLOC"}


def cases(path: Path) -> OrderedDict:
    out = OrderedDict()
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            out.setdefault(row["case_id"], []).append(row)
    return out


def versions(axis: str, rows: list[dict]) -> list[tuple[float, str, str]]:
    found = [(float(r["target_score"]), r["degradation_operation"], r["automatic_degradation"]) for r in rows
             if not (axis == "MEANING" and float(r["target_score"]) >= 1.0)]
    found.sort(key=lambda v: -v[0])
    chosen = found if len(found) <= 2 else [found[0], found[-1]]
    return [(1.0, "clean", rows[0]["human_simplification"])] + chosen


def build(examples: Path, run: Path, lang: str) -> tuple[list[dict], list[dict], dict]:
    originals = {r["canonical_pair_id"]: r["canonical_original_id"] for r in read_jsonl(run / "final/phase6_corpus.jsonl")}
    built = []
    for case_id, rows in cases(examples).items():
        axis = AXIS_CODES[rows[0]["feats_axis"]]
        vs = versions(axis, rows)
        row = {"clean_simplification": rows[0]["human_simplification"], "original": rows[0]["source"],
               "canonical_pair_id": rows[0]["canonical_pair_id"], "canonical_original_id": originals[rows[0]["canonical_pair_id"]],
               "corpus": rows[0]["dataset"]}
        public, key = displayed(item(axis, row, vs, "pair" if len(vs) == 2 else "rank3"))
        built.append(({"case_id": case_id, "language": lang, **public}, {"case_id": case_id, "language": lang, **key}))
    built.sort(key=lambda pk: stable_key(SEED, f"shuffle:{pk[1]['axis']}:{pk[1]['canonical_pair_id']}"))
    public, key = [p for p, _ in built], [k for _, k in built]
    summary = {"items": dict(Counter(f"{k['axis']}/{k['format']}" for k in key))}
    return public, key, summary


def meta(lang: str, key: list[dict], ctrl_key: list[dict], ctrl: list[dict]) -> list[dict]:
    by_id, by_text = corpus_index(lang)
    rows = [{"case_id": k["case_id"], "dataset": dataset(by_id.get(k["canonical_original_id"], (None,))[0], k["corpus"]),
             "human_versions": [label for label, op in k["operations"].items() if op == "clean"]} for k in key]
    for c, h in zip(ctrl, ctrl_key):
        source, corpus = by_id.get(h["source_id"], by_text.get(c["original"].strip(), (None, None)))
        rows.append({"case_id": c["case_id"], "dataset": dataset(source, corpus), "human_versions": ["X", "Y"]})
    return rows


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--language", required=True)
    p.add_argument("--examples", type=Path, required=True)
    args = p.parse_args()
    root = Path("phase6_degraded_corpus/runs")
    run, out = root / f"s1_{args.language}_v2", root / f"annotation_{args.language}_v2"
    public, key, summary = build(args.examples, run, args.language)
    ctrl, ctrl_key = controls(run, key, args.language, max(6, round(len(public) * 0.1)))
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "s1_items.jsonl", public)
    (out / "s1_key.json").write_text(json.dumps(key, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    write_jsonl(out / "s1_controls.jsonl", ctrl)
    (out / "s1_controls_key.json").write_text(json.dumps(ctrl_key, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    write_jsonl(out / "s1_meta.jsonl", meta(args.language, key, ctrl_key, ctrl))
    summary["controls"] = len(ctrl)
    (out / "build_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
