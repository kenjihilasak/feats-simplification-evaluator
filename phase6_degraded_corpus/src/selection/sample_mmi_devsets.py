#!/usr/bin/env python3
"""Sample shared deterministic dev/heldout sets from the nine MMI pools."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict, deque
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl

AXES = ("MEANING", "MOD", "ILLOC")
CORPORA = ("WikiAutoEN", "ASSET", "Wikipedia-Vikidia")


def pool_filename(axis: str, corpus: str) -> str:
    return f"{axis.lower()}_{corpus.lower().replace('-', '_')}.jsonl"


def stratified_order(rows: list[dict], axis: str, seed: int) -> list[dict]:
    rows = sorted(rows, key=lambda row: stable_key(seed, row["canonical_pair_id"]))
    if axis != "MEANING":
        return rows
    groups: dict[str, deque] = defaultdict(deque)
    for row in rows:
        cues = row.get("selection_features", {}).get("cue_types") or ["unknown"]
        cue = min(cues, key=lambda value: stable_key(seed, row["canonical_pair_id"] + value))
        groups[cue].append(row)
    ordered = []
    labels = sorted(groups)
    while any(groups.values()):
        for label in labels:
            if groups[label]:
                ordered.append(groups[label].popleft())
    return ordered


def sample_sets(pool_dir: Path, seed: int, dev_size: int, heldout_size: int) -> tuple[dict, dict]:
    outputs = {"dev": [], "heldout": [], "gemini_pilot": []}
    report = {"schema": "feats-phase6-mmi-splits-v1", "seed": seed, "cells": {}}
    split_by_original = {}
    for axis in AXES:
        for corpus in CORPORA:
            rows = read_jsonl(pool_dir / pool_filename(axis, corpus))
            split_candidates = [row for row in rows if row["allocation_pass"] == 1]
            ordered = stratified_order(split_candidates, axis, seed)
            if len(ordered) < dev_size + heldout_size:
                # Underpowered cell: keep the dev:heldout ratio so the source still reaches the human audit.
                dev_count = round(len(ordered) * dev_size / (dev_size + heldout_size))
            else:
                dev_count = dev_size
            dev = ordered[:dev_count]
            heldout = ordered[dev_count : dev_count + heldout_size]
            pilot = sorted(dev, key=lambda row: stable_key(seed + 1, row["canonical_pair_id"]))[:10]
            for split, selected in (("dev", dev), ("heldout", heldout)):
                for row in selected:
                    original_id = row["canonical_original_id"]
                    previous = split_by_original.setdefault(original_id, split)
                    if previous != split:
                        raise ValueError(f"original crosses dev/heldout: {original_id}")
                    outputs[split].append({**row, "split": split})
            outputs["gemini_pilot"].extend({**row, "split": "gemini_pilot"} for row in pilot)
            report["cells"][f"{axis}_{corpus}"] = {
                "pool": len(rows),
                "dev": len(dev),
                "heldout": len(heldout),
                "gemini_pilot": len(pilot),
                "underpowered": len(split_candidates) < dev_size + heldout_size,
                "dev_gemma_strategy_count": dict(
                    sorted(Counter(str(row["gemma_strategy_count"]) for row in dev).items())
                ),
                "heldout_gemma_strategy_count": dict(
                    sorted(Counter(str(row["gemma_strategy_count"]) for row in heldout).items())
                ),
                "dev_strict_single_strategy_candidate": dict(
                    sorted(Counter(str(row["strict_single_strategy_candidate"]).lower() for row in dev).items())
                ),
                "heldout_strict_single_strategy_candidate": dict(
                    sorted(Counter(str(row["strict_single_strategy_candidate"]).lower() for row in heldout).items())
                ),
                "allocation_pass": dict(
                    sorted(Counter(str(row["allocation_pass"]) for row in dev + heldout).items())
                ),
                "dev_meaning_cues": dict(
                    sorted(
                        Counter(
                            cue
                            for row in dev
                            for cue in row.get("selection_features", {}).get("cue_types", [])
                        ).items()
                    )
                ) if axis == "MEANING" else {},
            }
    for rows in outputs.values():
        rows.sort(key=lambda row: (row["target_axis"], row["corpus"], row["canonical_pair_id"]))
    report["totals"] = {name: len(rows) for name, rows in outputs.items()}
    report["unique_originals"] = {
        name: len({row["canonical_original_id"] for row in rows}) for name, rows in outputs.items()
    }
    return outputs, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    output_dir = Path(config["split_output_dir"])
    outputs, report = sample_sets(
        Path(config["output_dir"]),
        config["seed"],
        config["dev_size"],
        config["heldout_size"],
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in outputs.items():
        write_jsonl(output_dir / f"{name}.jsonl", rows)
    (output_dir / "split_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["totals"], indent=2))


if __name__ == "__main__":
    main()
