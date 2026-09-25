#!/usr/bin/env python3
"""Render a reviewer-friendly Markdown report for a multi-axis pilot."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl
from phase6_degraded_corpus.src.planning.multi_axis import AXES


def clean_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def render(manifest: list[dict], generated: list[dict]) -> str:
    predictions = {row["canonical_pair_id"]: row for row in generated}
    grouped = defaultdict(list)
    for row in manifest:
        grouped[row["target_axis"]].append((row, predictions.get(row["canonical_pair_id"])))
    lines = [
        "# Phase 6 multi-axis pilot", "",
        "Review whether the simplified version is acceptable and whether the generated text contains exactly one degradation of the stated target axis. For every non-Meaning axis, the propositional meaning must remain unchanged.", "",
        "Automatic validation is only a pre-screen; human audit is authoritative.", "",
        "| Axis | Pending audit | Failed automatic checks | Total |", "|---|---:|---:|---:|",
    ]
    for axis in AXES:
        if not grouped[axis]:
            continue
        statuses = Counter((prediction or {}).get("status", "missing") for _, prediction in grouped[axis])
        pending = statuses["generated_pending_audit"]
        failed = sum(count for status, count in statuses.items() if status != "generated_pending_audit")
        lines.append(f"| {axis} | {pending} | {failed} | {len(grouped[axis])} |")
    lines.append("")
    for axis in AXES:
        if not grouped[axis]:
            continue
        lines.extend([f"## {axis}", ""])
        for index, (row, prediction) in enumerate(grouped[axis], 1):
            generation = (prediction or {}).get("generation") or {}
            lines.extend([
                f"### {axis}-{index:02d}", "",
                f"- Pair: `{row['canonical_pair_id']}`",
                f"- Source strategy: `{row['source_strategy']}`",
                f"- Assigned operation: `{row['assigned_operation']}`",
                f"- Automatic status: `{(prediction or {}).get('status', 'missing')}`",
                f"- Original: {clean_cell(row['original'])}",
                f"- Simplified: {clean_cell(row['clean_simplification'])}",
                f"- Degraded: {clean_cell(generation.get('degraded_simplification'))}",
                f"- Model verification: {clean_cell(generation.get('brief_verification'))}",
                "",
            ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--generated", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    text = render(read_jsonl(args.manifest), read_jsonl(args.generated))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
