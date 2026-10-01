#!/usr/bin/env python3
"""Blinded review of graded FLUENCY levels (FOSE plan §9 gate).

`build`: 15 members per level (also_trim, minor, major, severe), WikiAutoEN + ASSET pooled,
shuffled, level hidden. `score`: compare answers with the intended level.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key

OPTIONS = ("Not worse", "Somewhat worse", "Much worse", "Broken")
EXPECTED = {"also_trim": {"Not worse"}, "minor": {"Somewhat worse"}, "major": {"Much worse"},
            "severe": {"Much worse", "Broken"}}
THRESHOLD = {"also_trim": 0.9, "minor": 0.8, "major": 0.8, "severe": 0.8}


def build(args) -> None:
    groups = list(read_jsonl(args.groups))
    picked = []
    for level in EXPECTED:
        pool = [(g, m) for g in groups for m in g["members"] if m["level"] == level]
        pool.sort(key=lambda gm: stable_key(args.seed, f'{gm[0]["canonical_pair_id"]}:{level}:{gm[1].get("rule")}'))
        seen, take = set(), []
        for g, m in pool:  # one member per pair
            if g["canonical_pair_id"] not in seen:
                take.append((g, m)); seen.add(g["canonical_pair_id"])
            if len(take) == args.per_level:
                break
        picked += take
    picked.sort(key=lambda gm: stable_key(args.seed, gm[0]["canonical_pair_id"] + gm[1]["text"]))
    clean = lambda g: next(m["text"] for m in g["members"] if m["level"] == "clean")
    lines = ["# FLUENCY graded levels: blinded review", "",
             "Compare **Variant** with **Clean** and mark how much *less fluent* (grammatical, natural) the Variant is. "
             "Ignore meaning. `Not worse` = equally fluent; `Somewhat worse` = one small slip; `Much worse` = a clear "
             "grammatical error; `Broken` = hard to read.", ""]
    key = {}
    for i, (g, m) in enumerate(picked, 1):
        cid = f"L{i:03d}"
        key[cid] = {"level": m["level"], "rule": m.get("rule"), "edits": m.get("edits"), "corpus": g["corpus"],
                    "canonical_pair_id": g["canonical_pair_id"]}
        lines += [f"### Case {cid}", "", f"* **Clean:** {clean(g)}", f"* **Variant:** {m['text']}", ""]
        lines += [f"* [ ] {o}" for o in OPTIONS] + ["* **Note:**", ""]
    args.review.write_text("\n".join(lines), encoding="utf-8")
    args.key.write_text(json.dumps(key, indent=2) + "\n")
    print(json.dumps({"cases": len(picked), "by_level": Counter(v["level"] for v in key.values())}))


def score(args) -> None:
    key = json.loads(args.key.read_text())
    answers = {}
    for block in re.split(r"\n### Case ", args.review.read_text(encoding="utf-8"))[1:]:
        cid = block.split("\n", 1)[0].strip()
        ticked = re.findall(r"^\s*[-*] \[[xX]\] (Not worse|Somewhat worse|Much worse|Broken)", block, flags=re.M)
        answers[cid] = ticked[0] if len(ticked) == 1 else ("MULTIPLE" if ticked else "UNMARKED")
    by_level, by_rule = defaultdict(Counter), defaultdict(Counter)
    for cid, meta in key.items():
        by_level[meta["level"]][answers[cid]] += 1
        by_rule[f'{meta["level"]}:{meta.get("rule")}:{"+".join(meta.get("edits") or [])}'][answers[cid]] += 1
    result = {}
    for level, counts in by_level.items():
        n = sum(v for k, v in counts.items() if k in OPTIONS)
        match = sum(counts[a] for a in EXPECTED[level]) / n if n else 0.0
        result[level] = {"answers": dict(counts), "n": n, "match": match, "threshold": THRESHOLD[level], "pass": match >= THRESHOLD[level]}
    result["by_rule"] = {k: dict(v) for k, v in sorted(by_rule.items())}
    args.results.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "score"))
    run = Path("phase6_degraded_corpus/runs/fluency_graded_en_v1")
    parser.add_argument("--groups", type=Path, default=run / "groups.jsonl")
    parser.add_argument("--review", type=Path, default=Path("phase6_degraded_corpus/docs/reports/current/fluency_graded_review.md"))
    parser.add_argument("--key", type=Path, default=run / "review_key.json")
    parser.add_argument("--results", type=Path, default=run / "review_results.json")
    parser.add_argument("--per-level", type=int, default=15)
    parser.add_argument("--seed", type=int, default=20261002)
    args = parser.parse_args()
    build(args) if args.command == "build" else score(args)


if __name__ == "__main__":
    main()
