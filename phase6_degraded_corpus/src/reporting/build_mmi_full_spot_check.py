#!/usr/bin/env python3
"""Build the deterministic blinded quality-gate review for mmi_en_v2_full."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key

TASKS = {
    "MEANING": "Exactly one factual detail is false; everything else is unchanged and fluent.",
    "MOD": "Two adjacent sentences are merged into one without changing facts or wording beyond joining words.",
    "assertion_to_question": "The statement becomes a yes/no question about the same proposition, with no other change.",
    "assertion_to_directive": "The statement becomes an instruction to the reader, with no other change.",
    "assertion_to_hedged": "The statement becomes uncertain through one hedge, with no other change.",
}


def selected(row: dict) -> str | None:
    index = row.get("selected_index")
    if index is None:
        return None
    return row["candidates"][index].get("degraded")


def build(rows: list[dict], per_cell: int, extra_hedged: int, seed: int) -> tuple[list[dict], dict]:
    valid = [row for row in rows if row.get("yield") and selected(row)]
    by_cell: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in valid:
        by_cell[(row["target_axis"], row["corpus"])].append(row)
    chosen, used = [], set()
    base_cells = Counter()
    for cell in sorted(by_cell):
        ordered = sorted(by_cell[cell], key=lambda row: stable_key(seed, f'cell:{row["canonical_pair_id"]}'))
        take = ordered[:per_cell]
        base_cells[f"{cell[0]}_{cell[1]}"] += len(take)
        chosen.extend(take)
        used.update(row["canonical_pair_id"] for row in take)
    hedged = sorted(
        (row for row in valid if row.get("operation") == "assertion_to_hedged" and row["canonical_pair_id"] not in used),
        key=lambda row: stable_key(seed, f'hedged:{row["canonical_pair_id"]}'),
    )[:extra_hedged]
    # The other operations reuse their heldout approval; only the independently
    # drawn hedged supplement remains in this full-corpus audit.
    chosen = sorted(hedged, key=lambda row: stable_key(seed, f'shuffle:{row["canonical_pair_id"]}'))
    report = {
        "eligible_selected_outputs": len(valid),
        "previous_base_cases_not_reaudited": sum(base_cells.values()),
        "extra_hedged_cases": len(hedged),
        "cases": len(chosen),
        "cells": dict(sorted(Counter(f'{r["target_axis"]}_{r["corpus"]}' for r in chosen).items())),
        "operations": dict(sorted(Counter(r["operation"] for r in chosen).items())),
    }
    return chosen, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scored-dir", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--per-cell", type=int, default=20)
    parser.add_argument("--extra-hedged", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20260930)
    args = parser.parse_args()
    rows = [row for path in sorted(args.scored_dir.glob("*.jsonl")) for row in read_jsonl(path)]
    cases, report = build(rows, args.per_cell, args.extra_hedged, args.seed)
    lines = [
        "# MMI v2 full-corpus hedged review (blinded)", "",
        "This review contains only the 40 `assertion_to_hedged` cases. MEANING, MOD, question and directive "
        "reuse their heldout approval and are not re-audited. Review without using the automatic-check outcome. "
        "Mark exactly one answer; `Unsure` counts as valid for the 85% gate.", "",
    ]
    key = {}
    for number, row in enumerate(cases, 1):
        case_id = f"F{number:03d}"
        operation = row["operation"] if row["target_axis"] == "ILLOC" else row["target_axis"]
        key[case_id] = {
            "canonical_pair_id": row["canonical_pair_id"],
            "canonical_original_id": row["canonical_original_id"],
            "axis": row["target_axis"], "source": row["corpus"], "operation": row["operation"],
        }
        lines += [
            f"## Case {case_id}", "",
            f"- **Axis:** `{row['target_axis']}`",
            f"- **Required change:** {TASKS[operation]}",
            f"- **Source:** {row['corpus']}",
            f"- **Original:** {row['original']}",
            f"- **Simplified:** {row['clean_simplification']}",
            f"- **Degraded:** {selected(row)}", "",
            "- [ ] Valid", "- [ ] Invalid", "- [ ] Unsure", "- **Note:**", "",
        ]
    args.review.parent.mkdir(parents=True, exist_ok=True)
    args.review.write_text("\n".join(lines), encoding="utf-8")
    args.key.parent.mkdir(parents=True, exist_ok=True)
    args.key.write_text(json.dumps({"cases": key, "report": report}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
