#!/usr/bin/env python3
"""Apply and check the OMIT/SYN/EXPL rules on a language's S1 allocation.

Pairs (one undone edit) go through the same generation and checks as FOSE v2; graded groups (sites A, B and
AB) through the same code as the English graded groups. Thresholds come from the run's `checker_config.json`.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, write_jsonl
from phase6_degraded_corpus.src.evaluation.score_fose_candidates import generate, score
from phase6_degraded_corpus.src.generation.generate_graded_rule_groups import score_groups

PAIR_TASKS = ("omit_pair", "syn_pair", "expl_pair")
GRADED_TASKS = ("omit_graded", "syn_graded")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--device", default="cuda")
    args = p.parse_args()
    cfg = json.loads((args.run_dir / "checker_config.json").read_text(encoding="utf-8"))
    pairs = [r for t in PAIR_TASKS for r in read_jsonl(args.run_dir / f"allocation/{t}.jsonl")]
    groups = [r for t in GRADED_TASKS for r in read_jsonl(args.run_dir / f"allocation/{t}.jsonl")]
    scored_pairs = score(generate(pairs, cfg), cfg, args.device) if pairs else []
    write_jsonl(args.run_dir / "scored/fose_pairs.jsonl", scored_pairs)
    scored_groups = score_groups(groups, cfg, args.device) if groups else []
    write_jsonl(args.run_dir / "scored/fose_groups.jsonl", scored_groups)
    print(json.dumps({"pairs": Counter(f'{r["target_axis"]}:{r["valid"]}' for r in scored_pairs),
                      "groups": Counter(f'{g["target_axis"]}:{g["valid"]}' for g in scored_groups)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
