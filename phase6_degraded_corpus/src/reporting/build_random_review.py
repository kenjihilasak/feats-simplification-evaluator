#!/usr/bin/env python3
"""Build a deterministic stratified random Markdown review of the Phase 6 pilot."""

from __future__ import annotations

import argparse
import random
from collections import Counter, defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl
from phase6_degraded_corpus.src.evaluation.analyze_pilot_quality import classify
from phase6_degraded_corpus.src.planning.multi_axis import AXES


def sample_rows(rows: list[dict], per_stratum: int, seed: int) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        quality, reason = classify(row)
        groups[(row["target_axis"], quality)].append(
            {**row, "automatic_quality": quality, "automatic_reason": reason}
        )
    rng = random.Random(seed)
    selected = []
    for key in sorted(groups):
        population = sorted(groups[key], key=lambda row: row["canonical_pair_id"])
        selected.extend(rng.sample(population, min(per_stratum, len(population))))
    rng.shuffle(selected)
    return selected


def clean(value: object) -> str:
    return str(value or "").replace("\n", " ").strip()


def render(rows: list[dict], seed: int, per_stratum: int) -> str:
    counts = Counter((row["target_axis"], row["automatic_quality"]) for row in rows)
    lines = [
        "# Phase 6 random pilot review", "",
        f"Deterministic stratified sample: **{len(rows)} cases**, seed `{seed}`, up to {per_stratum} examples per available dimension × automatic-result stratum.", "",
        "For each case, select one decision. A valid case must contain exactly one degradation in the target dimension and preserve all other dimensions.", "",
        "## Sample coverage", "",
        "| Dimension | Good | Medium | Failed | Total |", "|---|---:|---:|---:|---:|",
    ]
    for axis in AXES:
        if axis == "MEANING":
            continue
        values = [counts[(axis, tier)] for tier in ("good", "medium", "failed")]
        lines.append(f"| {axis} | {values[0]} | {values[1]} | {values[2]} | {sum(values)} |")
    lines.extend(["", "## Review cases", ""])
    for index, row in enumerate(rows, 1):
        generation = row.get("generation") or {}
        lines.extend([
            f"### Case {index:02d}", "",
            f"- **Target dimension:** `{row['target_axis']}`",
            f"- **Automatic result:** `{row['automatic_quality'].upper()}`",
            f"- **Pair:** `{row['canonical_pair_id']}`",
            f"- **Original:** {clean(row['original'])}",
            f"- **Simplified:** {clean(row['clean_simplification'])}",
            f"- **Degraded:** {clean(generation.get('degraded_simplification')) or '— no generated change —'}", "",
            "- [ ] Valid",
            "- [ ] Invalid",
            "- [ ] Unsure",
            "- **Note:**", "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--per-stratum", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260925)
    args = parser.parse_args()
    rows = sample_rows(read_jsonl(args.input), args.per_stratum, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(rows, args.seed, args.per_stratum), encoding="utf-8")
    print(f"{args.output}: {len(rows)} cases")


if __name__ == "__main__":
    main()
