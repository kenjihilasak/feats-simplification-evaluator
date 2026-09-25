#!/usr/bin/env python3
"""Build the single Phase 6 report covering all seven degradation pilots."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl
from phase6_degraded_corpus.src.evaluation.analyze_pilot_quality import classify
from phase6_degraded_corpus.src.planning.multi_axis import AXES


def normalize_meaning(row: dict) -> dict:
    generation = row["generation"]
    return {
        "canonical_pair_id": row["canonical_pair_id"],
        "canonical_original_id": row["canonical_original_id"],
        "target_axis": "MEANING",
        "source_strategy": row.get("predicted_strategy"),
        "assigned_operation": row["assigned_corruption"],
        "original": row["original"],
        "clean_simplification": row["clean_simplification"],
        "generation": {
            "degraded_simplification": generation["distorted_simplification"],
            "brief_verification": generation.get("brief_verification", ""),
        },
        "quality": "accepted",
        "quality_reason": "human_audited_meaning_degradation",
        "quality_basis": "human_audit",
        "accepted_source": row.get("accepted_source"),
    }


def normalize_multi_axis(row: dict) -> dict:
    quality, reason = classify(row)
    return {
        **row,
        "quality": quality,
        "quality_reason": reason,
        "quality_basis": "automatic_triage_pending_human_audit",
    }


def combine(meaning_rows: list[dict], multi_rows: list[dict]) -> list[dict]:
    rows = [normalize_meaning(row) for row in meaning_rows]
    rows.extend(normalize_multi_axis(row) for row in multi_rows)
    keys = [(row["canonical_pair_id"], row["target_axis"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate canonical_pair_id and target_axis in combined pilot")
    return sorted(rows, key=lambda row: (AXES.index(row["target_axis"]), row["canonical_pair_id"]))


def text(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def render(rows: list[dict]) -> str:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["target_axis"]].append(row)
    lines = [
        "# Phase 6 pilot report", "",
        "This is the single report for all seven Phase 6 pilots: 50 human-audited Meaning degradations and 300 generated examples covering the other six dimensions.", "",
        "## Interpretation", "",
        "- **Accepted:** the Meaning degradation was manually audited and accepted.",
        "- **Good:** all automatic structural checks passed, but semantic human review is still required.",
        "- **Medium:** the text changed, but the declared changed/replacement span was not verified literally.",
        "- **Failed:** no usable degradation was produced, usually because Simplified and Degraded are identical.", "",
        "The Meaning acceptance rate and the automatic rates for the other dimensions are not directly comparable because their review bases differ.", "",
        "## Summary", "",
        "| Dimension | Accepted | Good | Medium | Failed | Review basis |", "|---|---:|---:|---:|---:|---|",
    ]
    for axis in AXES:
        values = Counter(row["quality"] for row in grouped[axis])
        basis = "human audit" if axis == "MEANING" else "automatic triage"
        lines.append(
            f"| {axis} | {values['accepted']} | {values['good']} | {values['medium']} | {values['failed']} | {basis} |"
        )
    total = Counter(row["quality"] for row in rows)
    lines.extend([
        f"| **Total** | **{total['accepted']}** | **{total['good']}** | **{total['medium']}** | **{total['failed']}** | mixed |",
        "", "## Main findings", "",
        "- All 50 Meaning cases were manually audited; 19 required manual correction after both Qwen passes failed semantic audit.",
        "- Explanation and Illocution have the strongest automatic results among the six new dimensions.",
        "- Modulation changes every selected sentence, but many outputs have unverifiable span metadata.",
        "- Fluency often claims an edit that is absent from the generated sentence.",
        "- Omission and Synonymy have the most outright failures and require prompt, cue, and source-label review before scaling.",
        "- The 12,140-pair full generation remains blocked until human review validates the six new dimensions.", "",
        "## All 350 pilot examples", "",
    ])
    for axis in AXES:
        lines.extend([f"### {axis}", ""])
        for index, row in enumerate(grouped[axis], 1):
            generation = row.get("generation") or {}
            lines.extend([
                f"#### {axis}-{index:02d}", "",
                f"- Pair: `{row['canonical_pair_id']}`",
                f"- Source strategy: `{row.get('source_strategy') or 'n/a'}`",
                f"- Assigned operation: `{row.get('assigned_operation') or 'n/a'}`",
                f"- Quality: **{row['quality'].title()}** (`{row['quality_reason']}`; {row['quality_basis']})",
                f"- Original: {text(row['original'])}",
                f"- Simplified: {text(row['clean_simplification'])}",
                f"- Degraded: {text(generation.get('degraded_simplification'))}",
                f"- Verification: {text(generation.get('brief_verification'))}", "",
            ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--meaning", type=Path, required=True)
    parser.add_argument("--multi-axis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = combine(read_jsonl(args.meaning), read_jsonl(args.multi_axis))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(rows), encoding="utf-8")
    print(f"{args.output}: {len(rows)} records")


if __name__ == "__main__":
    main()
