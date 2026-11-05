#!/usr/bin/env python3
"""Strategies confirmed by at least `--min-models` of the Phase 3a classifiers, per pair, for one language.

Labels are non-exclusive, so a pair keeps every strategy that enough models predict (one, two or three), unlike the
strict single-strategy gold candidates. Output rows: `canonical_pair_id`, `consensus_codes` (sorted) and
`supporting_models` (strategy -> models). Pairs with no confirmed strategy are left out.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, write_jsonl

MODELS = ("gemma3_12b_pairwise_qlora", "qwen2p5_7b_pairwise_qlora", "xlmr_large_focal", "multilingual_e5_large_bce")


def consensus(run: Path, lang: str, min_models: int) -> tuple[list[dict], dict]:
    votes: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for model in MODELS:
        for r in read_jsonl(run / f"models/{model}/predictions/{lang}/feats_consolidated.jsonl"):
            for code in r["predicted_codes"]:
                votes[r["canonical_pair_id"]][code].append(model)
    rows = []
    for pair, by_code in votes.items():
        codes = sorted(c for c, ms in by_code.items() if len(ms) >= min_models)
        if codes:
            rows.append({"canonical_pair_id": pair, "consensus_codes": codes,
                         "supporting_models": {c: sorted(by_code[c]) for c in codes}})
    rows.sort(key=lambda r: r["canonical_pair_id"])
    report = {"language": lang, "min_models": min_models, "pairs_with_votes": len(votes), "pairs_confirmed": len(rows),
              "by_strategy": dict(Counter(c for r in rows for c in r["consensus_codes"])),
              "by_count": dict(Counter(len(r["consensus_codes"]) for r in rows))}
    return rows, report


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--phase3a-run", type=Path,
                   default=Path("phase3a_strategy_detection/runs/2026-09-30_four_models_textrepair_effective_v1"))
    p.add_argument("--language", required=True)
    p.add_argument("--min-models", type=int, default=2)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    rows, report = consensus(args.phase3a_run, args.language, args.min_models)
    write_jsonl(args.output, rows)
    args.output.with_suffix(".report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
