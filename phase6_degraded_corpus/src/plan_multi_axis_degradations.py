#!/usr/bin/env python3
"""Detect applicability, assign one target axis per pair, and select pilots."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from contracts import read_jsonl, stable_key, write_jsonl
from multi_axis import AXES, allocate


def plan(config: dict) -> tuple[list[dict], list[dict], dict]:
    rows = read_jsonl(Path(config["input_file"]))
    assignments, allocation_report = allocate(rows, int(config["seed"]))
    frozen = set(config.get("frozen_pilot_axes", []))
    size = int(config["pilot_size_per_axis"])
    pilots = []
    for axis in AXES:
        if axis in frozen:
            continue
        pool = [row for row in assignments if row["target_axis"] == axis]
        chosen = sorted(
            pool,
            key=lambda row: stable_key(config["seed"] + 1, row["canonical_pair_id"]),
        )[:size]
        if len(chosen) < size:
            raise ValueError(f"axis {axis} has {len(chosen)} assignments; need {size} for pilot")
        pilots.extend({**row, "pilot": True} for row in chosen)
    pilots.sort(key=lambda row: (row["target_axis"], row["canonical_pair_id"]))
    report = {
        **allocation_report,
        "experiment_id": config["experiment_id"],
        "pilot_records": len(pilots),
        "pilot_by_axis": dict(sorted(Counter(row["target_axis"] for row in pilots).items())),
        "frozen_pilot_axes": sorted(frozen),
        "assignment_sha256": hashlib.sha256(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in assignments).encode()
        ).hexdigest(),
    }
    return assignments, pilots, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    assignments, pilots, report = plan(config)
    output = Path(config["output_dir"])
    write_jsonl(output / "assignment_manifest.jsonl", assignments)
    write_jsonl(output / "pilot_manifest.jsonl", pilots)
    write_jsonl(output / "pilot_audit.template.jsonl", [{
        "canonical_pair_id": row["canonical_pair_id"], "target_axis": row["target_axis"],
        "reviewer": "", "clean_acceptable": None, "single_target_degradation": None,
        "meaning_preserved_for_non_meaning": None, "decision": "pending", "notes": "",
    } for row in pilots])
    output.mkdir(parents=True, exist_ok=True)
    (output / "assignment_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
