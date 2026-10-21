#!/usr/bin/env python3
"""Plan graded MOD groups: texts with a dependent adjacent sentence pair (for the reorder rule) and a long sentence
for the LLM fronting edit. Level 0.5 is one of the two operations, level 0.0 both."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl
from phase6_degraded_corpus.src.planning.plan_mmi_operations import _dependent_second, split_sentences
from phase6_degraded_corpus.src.planning.plan_mmi_v3_review import CORPORA, reviewed_originals


def plan(allocation: list[dict], excluded: set[str], seed: int, size: int) -> list[dict]:
    out = []
    for row in allocation:
        if row["target_axis"] != "MOD" or row["corpus"] not in CORPORA or row["canonical_original_id"] in excluded:
            continue
        sentences = split_sentences(row["clean_simplification"])
        reorder = [i for i in range(len(sentences) - 1) if _dependent_second(sentences[i], sentences[i + 1])]
        if not reorder:
            continue
        target = max(range(len(sentences)), key=lambda i: len(sentences[i].split()))
        if len(sentences[target].split()) < 10:
            continue  # too short to front a phrase of four or more tokens
        index = min(reorder, key=lambda i: stable_key(seed, f'{row["canonical_pair_id"]}:{i}'))
        out.append({**row, "operation": "mod_front_heavy", "generator_kind": "llm", "sentences": sentences,
                    "target_sentence_index": target, "reorder_index": index, "rule_output": None,
                    "plan_status": "ready", "plan_schema": "feats-phase6-mod-graded-plan-v1"})
    return sorted(out, key=lambda r: stable_key(seed, "graded:" + r["canonical_pair_id"]))[:size]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--allocation", type=Path, required=True)
    p.add_argument("--exclude", type=Path, action="append", default=[])
    p.add_argument("--exclude-ids", type=Path, action="append", default=[])
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--size", type=int, default=300)
    p.add_argument("--seed", type=int, default=20261002)
    args = p.parse_args()
    rows = plan(read_jsonl(args.allocation), reviewed_originals(args.exclude, args.exclude_ids), args.seed, args.size)
    write_jsonl(args.output, rows)
    print(json.dumps({"planned": len(rows)}))


if __name__ == "__main__":
    main()
