#!/usr/bin/env python3
"""Blinded human review of graded MEANING levels (MEANING recipe v2, plan §3).

`build`: 15 selected variants per level (neutral_trim, mild_loss, major_loss) and source,
shuffled, without the level name. `score`: compare the reviewer's answer
(none / some / a lot / contradiction) with the intended level and apply the gate.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key

LEVELS = ("neutral_trim", "mild_loss", "major_loss")
EXPECTED = {"neutral_trim": "None", "mild_loss": "Some", "major_loss": "A lot"}
OPTIONS = ("None", "Some", "A lot", "Contradiction", "Broken")


def build(args) -> None:
    groups = [g for g in read_jsonl(args.groups) if g["corpus"] in {"WikiAutoEN", "ASSET"}]
    picked = []
    for level in LEVELS:
        for corpus in ("WikiAutoEN", "ASSET"):
            pool = [(g, m) for g in groups if g["corpus"] == corpus for m in g["members"] if m["level"] == level]
            pool.sort(key=lambda gm: stable_key(args.seed, f'{gm[0]["canonical_pair_id"]}:{level}'))
            picked += [(g, m) for g, m in pool[: args.per_cell]]
    picked.sort(key=lambda gm: stable_key(args.seed, gm[0]["canonical_pair_id"] + gm[1]["text"]))
    clean_of = lambda g: next(m["text"] for m in g["members"] if m["level"] == "clean")
    lines = ["# MEANING graded levels: blinded review", "",
             "For each case, compare **Variant** with **Clean** and mark how much meaning the Variant has lost.",
             "`None` = same meaning; `Some` = a minor detail lost; `A lot` = a central fact or clause lost or made vague; "
             "`Contradiction` = the Variant states something false; `Broken` = ungrammatical or nonsensical.", ""]
    key = {}
    for i, (g, m) in enumerate(picked, 1):
        cid = f"G{i:03d}"
        key[cid] = {"level": m["level"], "corpus": g["corpus"], "canonical_pair_id": g["canonical_pair_id"], "rule": m.get("rule")}
        lines += [f"### Case {cid}", "", f"* **Original:** {g['original']}", f"* **Clean:** {clean_of(g)}",
                  f"* **Variant:** {m['text']}", ""] + [f"* [ ] {o}" for o in OPTIONS] + ["* **Note:**", ""]
    args.review.write_text("\n".join(lines), encoding="utf-8")
    args.key.write_text(json.dumps(key, indent=2) + "\n")
    print(json.dumps({"cases": len(picked), "by_level": Counter(v["level"] for v in key.values())}, indent=2))


def score(args) -> None:
    key = json.loads(args.key.read_text())
    text = args.review.read_text(encoding="utf-8")
    answers = {}
    for block in re.split(r"\n### Case ", text)[1:]:
        cid = block.split("\n", 1)[0].strip()
        ticked = re.findall(r"^\s*[-*] \[[xX]\] (None|Some|A lot|Contradiction|Broken)", block, flags=re.M)
        answers[cid] = ticked[0] if len(ticked) == 1 else ("MULTIPLE" if ticked else "UNMARKED")
    by_level = defaultdict(Counter)
    for cid, meta in key.items():
        by_level[meta["level"]][answers.get(cid, "UNMARKED")] += 1
    result = {}
    for level, counts in by_level.items():
        n = sum(v for k, v in counts.items() if k not in {"UNMARKED", "MULTIPLE"})
        match = counts[EXPECTED[level]] / n if n else 0.0
        threshold = 0.9 if level == "neutral_trim" else 0.8
        result[level] = {"answers": dict(counts), "n": n, "match_rate": match, "threshold": threshold, "pass": match >= threshold}
    args.results.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "score"))
    parser.add_argument("--groups", type=Path, default=Path("phase6_degraded_corpus/runs/meaning_graded_en_v1/groups.jsonl"))
    parser.add_argument("--review", type=Path, default=Path("phase6_degraded_corpus/docs/reports/current/meaning_graded_review.md"))
    parser.add_argument("--key", type=Path, default=Path("phase6_degraded_corpus/runs/meaning_graded_en_v1/review_key.json"))
    parser.add_argument("--results", type=Path, default=Path("phase6_degraded_corpus/runs/meaning_graded_en_v1/review_results.json"))
    parser.add_argument("--per-cell", type=int, default=15)
    parser.add_argument("--seed", type=int, default=20261001)
    args = parser.parse_args()
    build(args) if args.command == "build" else score(args)


if __name__ == "__main__":
    main()
