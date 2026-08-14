#!/usr/bin/env python3
"""Convert the pinned SimplifyUR text files to canonical FEATS JSONL."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from common import DATA_ROOT, INVENTORY_ROOT, RAW_ROOT, REPORT_ROOT
from common import write_json, write_jsonl


REVISION = "cdb3203d39abfcc365232c8aae1b35afa5d43bd8"


def split_groups(path: Path) -> list[list[str]]:
    groups: list[list[str]] = [[]]
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.rstrip("\r")
        if line == "--":
            groups.append([])
        elif line:
            groups[-1].append(line)
    if groups and not groups[-1]:
        groups.pop()
    return groups


def convert() -> dict[str, object]:
    complex_path = RAW_ROOT / "simplifyur" / "Data" / "Complex.txt"
    simple_path = RAW_ROOT / "simplifyur" / "Data" / "Simplified.txt"
    complex_groups = split_groups(complex_path)
    simple_groups = split_groups(simple_path)
    if len(complex_groups) != len(simple_groups):
        raise ValueError("SimplifyUR group counts differ")

    def records() -> Iterator[dict[str, object]]:
        for source_row, (originals, references) in enumerate(
            zip(complex_groups, simple_groups)
        ):
            if len(originals) != 1 or not references:
                raise ValueError(f"Invalid SimplifyUR group {source_row}")
            original_id = f"simplifyur:simplifyur:null:{source_row:09d}"
            for reference_index, simple in enumerate(references):
                yield {
                    "id": f"{original_id}:r{reference_index:02d}",
                    "original_id": original_id,
                    "language": "ur",
                    "source": "SimplifyUR",
                    "corpus": "SimplifyUR",
                    "upstream_split": None,
                    "original": originals[0],
                    "simple": simple,
                    "reference_index": reference_index,
                    "source_dataset": "harisbinzia/SimplifyUR",
                    "source_revision": REVISION,
                    "source_row": source_row,
                }

    output = DATA_ROOT / "ur" / "simplifyur__SimplifyUR.jsonl"
    output_report = write_jsonl(output, records())
    report = {
        "source": "SimplifyUR",
        "source_revision": REVISION,
        "groups": len(complex_groups),
        "normalized_pairs": output_report["pairs"],
        **output_report,
    }
    write_json(INVENTORY_ROOT / "simplifyur_inventory.json", report)
    write_json(REPORT_ROOT / "simplifyur_conversion_validation.json", report)
    return report


if __name__ == "__main__":
    print(json.dumps(convert(), ensure_ascii=False))

