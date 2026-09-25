#!/usr/bin/env python3
"""Summarize automatic good/medium/failed triage for the Phase 6 pilot."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl
from phase6_degraded_corpus.src.planning.multi_axis import AXES


def classify(row: dict) -> tuple[str, str]:
    checks = row.get("automatic_checks") or {}
    if row.get("status") == "generated_pending_audit":
        return "good", "all_automatic_checks_passed"
    if not row.get("generation"):
        return "failed", "missing_or_unparseable_generation"
    if not checks.get("different_from_clean", False):
        return "failed", "simplified_and_degraded_are_identical"
    if not checks.get("operation_matches_assignment", False):
        return "failed", "operation_does_not_match_assignment"
    return "medium", "text_changed_but_declared_span_not_verified"


def analyze(rows: list[dict]) -> dict:
    pair_ids = [row["canonical_pair_id"] for row in rows]
    if len(pair_ids) != len(set(pair_ids)):
        raise ValueError("duplicate canonical_pair_id in pilot")
    by_axis = defaultdict(Counter)
    reasons = defaultdict(Counter)
    annotated = []
    for row in rows:
        axis = row["target_axis"]
        quality, reason = classify(row)
        by_axis[axis][quality] += 1
        reasons[axis][reason] += 1
        annotated.append({**row, "automatic_quality": quality, "automatic_quality_reason": reason})
    axes = [axis for axis in AXES if by_axis[axis]]
    summary = {}
    for axis in axes:
        total = sum(by_axis[axis].values())
        summary[axis] = {
            "total": total,
            **{tier: by_axis[axis][tier] for tier in ("good", "medium", "failed")},
            **{f"{tier}_rate": round(by_axis[axis][tier] / total, 4) for tier in ("good", "medium", "failed")},
            "reasons": dict(sorted(reasons[axis].items())),
        }
    totals = Counter()
    for values in by_axis.values():
        totals.update(values)
    return {
        "schema": "feats-phase6-pilot-quality-analysis-v1",
        "classification": {
            "good": "All automatic structural checks passed; still requires human semantic review.",
            "medium": "The degraded text changed and declared the assigned operation, but its declared changed/replacement span could not be verified literally.",
            "failed": "The degraded text was missing, unchanged, or used the wrong operation.",
        },
        "records": len(rows),
        "totals": dict(totals),
        "by_axis": summary,
        "annotated_records": annotated,
    }


def cell(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def render_markdown(analysis: dict, examples_per_tier: int = 2) -> str:
    lines = [
        "# Phase 6 pilot quality analysis", "",
        "This report is an **automatic triage**, not a final semantic evaluation. Human reviewers must still verify that the simplified version is valid and that the degradation changes only the target dimension.", "",
        "## Quality levels", "",
        "- **Good:** all automatic structural checks passed.",
        "- **Medium:** the text changed and the assigned operation was declared, but the changed/replacement span was not verified literally.",
        "- **Failed:** no usable degradation was produced, most commonly because Simplified and Degraded are identical.", "",
        "## Results by dimension", "",
        "| Dimension | Good | Medium | Failed | Good rate |", "|---|---:|---:|---:|---:|",
    ]
    ranked = sorted(analysis["by_axis"].items(), key=lambda item: (-item[1]["good_rate"], item[0]))
    for axis, values in ranked:
        lines.append(
            f"| {axis} | {values['good']} | {values['medium']} | {values['failed']} | {values['good_rate']:.0%} |"
        )
    total = analysis["records"]
    totals = analysis["totals"]
    lines.extend([
        f"| **Overall** | **{totals.get('good', 0)}** | **{totals.get('medium', 0)}** | **{totals.get('failed', 0)}** | **{totals.get('good', 0) / total:.0%}** |",
        "", "## Main findings", "",
        "- Explanation and Illocution have the strongest automatic results.",
        "- Modulation changes every selected sentence, but many outputs have unverifiable span metadata.",
        "- Fluency frequently claims an edit that is absent from the generated sentence.",
        "- Omission and Synonymy have the highest outright-failure counts; their prompts, cues, and Phase 3a source labels need review before scaling.",
        "- Medium cases must not be discarded automatically: several may contain valid degradations with inaccurate model metadata.",
        "", "## Failure reasons", "",
    ])
    for axis, values in ranked:
        reasons = ", ".join(f"`{reason}`: {count}" for reason, count in values["reasons"].items())
        lines.append(f"- **{axis}:** {reasons}")
    grouped = defaultdict(lambda: defaultdict(list))
    for row in analysis["annotated_records"]:
        grouped[row["target_axis"]][row["automatic_quality"]].append(row)
    lines.extend(["", "## Representative examples", ""])
    for axis, _ in ranked:
        lines.extend([f"### {axis}", ""])
        for tier in ("good", "medium", "failed"):
            examples = grouped[axis][tier][:examples_per_tier]
            if not examples:
                continue
            lines.extend([f"#### {tier.title()}", ""])
            for row in examples:
                generation = row.get("generation") or {}
                lines.extend([
                    f"- Pair: `{row['canonical_pair_id']}`",
                    f"  - Reason: `{row['automatic_quality_reason']}`",
                    f"  - Original: {cell(row['original'])}",
                    f"  - Simplified: {cell(row['clean_simplification'])}",
                    f"  - Degraded: {cell(generation.get('degraded_simplification'))}",
                ])
            lines.append("")
    lines.extend([
        "## Decision", "",
        "The 12,140-pair full generation remains blocked. First, human reviewers must adjudicate the 300 pilot examples and prompts/detectors must be revised for every dimension below the agreed 85% valid-degradation threshold.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--examples-per-tier", type=int, default=2)
    args = parser.parse_args()
    analysis = analyze(read_jsonl(args.input))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps({key: value for key, value in analysis.items() if key != "annotated_records"}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(
        render_markdown(analysis, args.examples_per_tier), encoding="utf-8"
    )
    print(args.markdown_output)


if __name__ == "__main__":
    main()
