#!/usr/bin/env python3
"""Reallocate the accepted MMI v2 pool for full-corpus generation."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl

AXES = ("MEANING", "MOD", "ILLOC")
SOURCES = ("WikiAutoEN", "ASSET", "Wikipedia-Vikidia")
ILLOC_OPERATIONS = ("assertion_to_question", "assertion_to_directive", "assertion_to_hedged")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_unique_pool_rows(pool_dir: Path) -> tuple[list[dict], list[Path]]:
    paths = sorted(pool_dir.glob("*.jsonl"))
    paths = [path for path in paths if path.stem.split("_")[0].upper() in AXES]
    by_pair: dict[str, dict] = {}
    for path in paths:
        for row in read_jsonl(path):
            pair_id = row["canonical_pair_id"]
            previous = by_pair.get(pair_id)
            if previous is not None and previous != row:
                raise ValueError(f"conflicting pool rows for {pair_id}")
            by_pair[pair_id] = row
    return list(by_pair.values()), paths


def excluded_originals(paths: list[Path]) -> set[str]:
    return {
        row["canonical_original_id"]
        for path in paths
        for row in read_jsonl(path)
    }


def assign_illoc_operations(rows: list[dict], seed: int) -> list[dict]:
    """Balance question/directive/hedged within a source deterministically."""
    counts = Counter()
    assigned = []
    for row in sorted(rows, key=lambda item: stable_key(seed, item["canonical_pair_id"])):
        operation = min(
            ILLOC_OPERATIONS,
            key=lambda value: (counts[value], stable_key(seed, f'{row["canonical_pair_id"]}:{value}')),
        )
        counts[operation] += 1
        assigned.append({**row, "operation": operation})
    return assigned


def allocate(rows: list[dict], audited_original_ids: set[str], seed: int) -> tuple[dict[tuple[str, str], list[dict]], dict]:
    """Assign each original once: MOD first, then balance MEANING and ILLOC per source."""
    eligible = [row for row in rows if row["canonical_original_id"] not in audited_original_ids]
    by_original: dict[str, list[dict]] = defaultdict(list)
    for row in eligible:
        by_original[row["canonical_original_id"]].append(row)

    selected = []
    duplicate_pairs_dropped = 0
    for original_id, variants in by_original.items():
        variants.sort(key=lambda row: stable_key(seed, row["canonical_pair_id"]))
        selected.append(variants[0])
        duplicate_pairs_dropped += len(variants) - 1

    output = {(axis, source): [] for axis in AXES for source in SOURCES}
    for source in SOURCES:
        source_rows = [row for row in selected if row["corpus"] == source]
        mod = [row for row in source_rows if "MOD" in row["eligible_axes"]]
        used = {row["canonical_original_id"] for row in mod}
        output[("MOD", source)] = [{**row, "target_axis": "MOD"} for row in mod]

        remaining = [row for row in source_rows if row["canonical_original_id"] not in used]
        only_meaning = [row for row in remaining if "MEANING" in row["eligible_axes"] and "ILLOC" not in row["eligible_axes"]]
        only_illoc = [row for row in remaining if "ILLOC" in row["eligible_axes"] and "MEANING" not in row["eligible_axes"]]
        both = [row for row in remaining if {"MEANING", "ILLOC"}.issubset(row["eligible_axes"])]
        meaning, illoc = list(only_meaning), list(only_illoc)
        for row in sorted(both, key=lambda item: stable_key(seed, item["canonical_pair_id"])):
            axis = min(
                ("MEANING", "ILLOC"),
                key=lambda value: (
                    len(meaning) if value == "MEANING" else len(illoc),
                    stable_key(seed, f'{row["canonical_pair_id"]}:{value}'),
                ),
            )
            (meaning if axis == "MEANING" else illoc).append(row)
        output[("MEANING", source)] = [{**row, "target_axis": "MEANING"} for row in meaning]
        output[("ILLOC", source)] = assign_illoc_operations(
            [{**row, "target_axis": "ILLOC"} for row in illoc], seed
        )

    assigned = [row for values in output.values() for row in values]
    originals = [row["canonical_original_id"] for row in assigned]
    if len(originals) != len(set(originals)):
        raise ValueError("an original was assigned to more than one axis")
    if audited_original_ids.intersection(originals):
        raise ValueError("audited original leaked into the full allocation")

    report = {
        "schema": "feats-phase6-mmi-full-allocation-v1",
        "seed": seed,
        "input_unique_pairs": len(rows),
        "input_unique_originals": len(by_original) + len({r["canonical_original_id"] for r in rows} & audited_original_ids),
        "excluded_audited_originals": len({r["canonical_original_id"] for r in rows} & audited_original_ids),
        "duplicate_pair_variants_dropped": duplicate_pairs_dropped,
        "assigned_pairs": len(assigned),
        "assigned_originals": len(set(originals)),
        "cells": {},
    }
    for (axis, source), values in output.items():
        report["cells"][f"{axis}_{source}"] = {
            "pairs": len(values),
            "operations": dict(sorted(Counter(row.get("operation", "planned_later") for row in values).items())),
        }
        values.sort(key=lambda row: row["canonical_pair_id"])
    return output, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pool-dir", type=Path, default=Path("phase6_degraded_corpus/runs/mmi_en_v2/pools"))
    parser.add_argument("--heldout", type=Path, nargs="+", default=[
        Path("phase6_degraded_corpus/runs/mmi_en_v2/splits/heldout.jsonl"),
        Path("phase6_degraded_corpus/runs/mmi_en_v2/splits/heldout_meaning_v21.jsonl"),
    ])
    parser.add_argument("--output-dir", type=Path, default=Path("phase6_degraded_corpus/runs/mmi_en_v2_full/allocation"))
    parser.add_argument("--seed", type=int, default=20260930)
    args = parser.parse_args()

    rows, pool_paths = load_unique_pool_rows(args.pool_dir)
    audited = excluded_originals(args.heldout)
    allocation, report = allocate(rows, audited, args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for (axis, source), values in allocation.items():
        slug = source.lower().replace("-", "_")
        write_jsonl(args.output_dir / f"{axis.lower()}_{slug}.jsonl", values)
    all_rows = sorted(
        (row for values in allocation.values() for row in values),
        key=lambda row: row["canonical_pair_id"],
    )
    write_jsonl(args.output_dir / "all.jsonl", all_rows)
    (args.output_dir / "excluded_audited_originals.txt").write_text(
        "".join(f"{value}\n" for value in sorted(audited)), encoding="utf-8"
    )
    report["inputs"] = {
        "pools": {str(path): sha256(path) for path in pool_paths},
        "heldout": {str(path): sha256(path) for path in args.heldout},
    }
    (args.output_dir / "allocation_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
