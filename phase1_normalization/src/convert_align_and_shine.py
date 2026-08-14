#!/usr/bin/env python3
"""Convert the selected Align-and-Shine CSV to canonical FEATS JSONL."""

from __future__ import annotations

import csv
import json
from typing import Iterator

from common import DATA_ROOT, INVENTORY_ROOT, PROJECT_ROOT, RAW_ROOT, REPORT_ROOT
from common import sha256, write_json, write_jsonl


REVISION = "2026-02-28_fullCorpus_v1"


def convert() -> dict[str, object]:
    path = (
        RAW_ROOT
        / "align_and_shine"
        / REVISION
        / "data"
        / f"filtered_sentence_pairs_{REVISION}.csv"
    )
    by_language: dict[str, list[dict[str, str]]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            by_language.setdefault(row["language"], []).append(row)

    outputs: list[dict[str, object]] = []
    for language in sorted(by_language):
        rows = by_language[language]

        def records() -> Iterator[dict[str, object]]:
            for source_row, row in enumerate(rows):
                original = row["wiki_text"]
                simple = row["viki_text"]
                if not original or not simple:
                    raise ValueError(f"Empty Align-and-Shine text: {language}:{source_row}")
                original_id = (
                    f"alignandshine:{language}:wikipediavikidia:null:{source_row:09d}"
                )
                yield {
                    "id": f"{original_id}:r00",
                    "original_id": original_id,
                    "language": language,
                    "source": "Align-and-Shine",
                    "corpus": "Wikipedia-Vikidia",
                    "upstream_split": None,
                    "original": original,
                    "simple": simple,
                    "reference_index": 0,
                    "source_dataset": "Align-and-Shine",
                    "source_revision": REVISION,
                    "source_row": source_row,
                }

        output = DATA_ROOT / language / "align_and_shine__Wikipedia-Vikidia.jsonl"
        outputs.append({"language": language, **write_jsonl(output, records())})
    report = {
        "source": "Align-and-Shine",
        "source_revision": REVISION,
        "raw_path": str(path.relative_to(PROJECT_ROOT)),
        "raw_sha256": sha256(path),
        "normalized_pairs": sum(int(row["pairs"]) for row in outputs),
        "outputs": outputs,
    }
    write_json(INVENTORY_ROOT / "align_and_shine_inventory.json", report)
    write_json(REPORT_ROOT / "align_and_shine_conversion_validation.json", report)
    return report


if __name__ == "__main__":
    print(json.dumps(convert(), ensure_ascii=False))

