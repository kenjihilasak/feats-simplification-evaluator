#!/usr/bin/env python3
"""Render audited Phase 6 degradations as a readable Markdown report."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

SOURCE_LABELS = {
    "qwen_v1": "Qwen pass 1",
    "qwen_v2_retry": "Qwen pass 2",
    "manual_correction": "Manual correction after Qwen audit failure",
}


def emphasize(text: str, span: str) -> str:
    return text.replace(span, f"**{span}**", 1) if span and span in text else text


def render(rows: list[dict]) -> str:
    rows = sorted(rows, key=lambda row: (row["generation"]["corruption_type"], row["canonical_pair_id"]))
    counts = Counter(row["generation"]["corruption_type"] for row in rows)
    sources = Counter(row["accepted_source"] for row in rows)
    lines = [
        "# Phase 6 meaning-degradation pilot: 50 audited pairs", "",
        "[Automation and methodology](DEGRADATION_AUTOMATION.md) · [Phase 6 README](../README.md)", "",
        "Each example contains a source sentence, an accepted clean simplification, and a deliberately incorrect simplification with one severe meaning error. Bold text marks the recorded change when the span occurs literally.", "",
        "## Summary", "", f"- Pairs: **{len(rows)}**",
        f"- Qwen pass 1: **{sources['qwen_v1']}**",
        f"- Qwen pass 2: **{sources['qwen_v2_retry']}**",
        f"- Manual corrections after model audit failure: **{sources['manual_correction']}**", "",
        "| Corruption | Count |", "|---|---:|",
    ]
    lines.extend(f"| {kind.replace('_', ' ')} | {counts[kind]} |" for kind in sorted(counts))
    lines.extend(["", "## Pairs", ""])
    for index, row in enumerate(rows, 1):
        generation = row["generation"]
        clean = emphasize(row["clean_simplification"], generation["changed_clean_span"])
        distorted = emphasize(generation["distorted_simplification"], generation["replacement_span"])
        lines.extend([
            f"### {index}. {generation['corruption_type'].replace('_', ' ').title()}", "",
            f"- **Pair ID:** `{row['canonical_pair_id']}`",
            f"- **Simplification strategy:** `{row['predicted_strategy']}`",
            f"- **Accepted from:** {SOURCE_LABELS[row['accepted_source']]}",
            f"- **Original:** {row['original']}",
            f"- **Clean simplification:** {clean}",
            f"- **Degraded simplification:** {distorted}",
            f"- **Recorded change:** `{generation['changed_clean_span']}` → `{generation['replacement_span']}`", "",
        ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 50:
        raise ValueError(f"expected 50 audited pairs, found {len(rows)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
