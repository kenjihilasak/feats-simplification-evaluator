#!/usr/bin/env python3
"""Convert the pinned MultiSim CSV files to canonical FEATS JSONL."""

from __future__ import annotations

import csv
import json
import re
import sys
from typing import Iterator

from common import DATA_ROOT, INVENTORY_ROOT, RAW_ROOT, REPORT_ROOT, PROJECT_ROOT
from common import sha256, write_json, write_jsonl


REVISION = "3213620ecd82d5f579b18c58532973442ec3a1b1"
CORPORA = [
    ("en", "ASSET", "English/ASSET"),
    ("it", "AdminIt", "Italian/AdminIT"),
    ("fr", "CLEAR", "French/CLEAR Corpus"),
    ("ja", "EasyJapanese", "Japanese/Easy Japanese Corpus"),
    ("ja", "EasyJapaneseExtended", "Japanese/Easy Japanese Extended"),
    ("de", "GEOLinoTest", "German/GEOLino Corpus"),
    ("it", "PaCCSS-IT", "Italian/PaCCSS-IT Corpus"),
    ("pt-BR", "PorSimples", "Brazilian Portuguese/PorSimples"),
    ("ru", "RSSE", "Russian/RSSE Corpus"),
    ("ru", "RuAdaptEncy", "Russian/RuAdapt Ency"),
    ("ru", "RuAdaptFairytales", "Russian/RuAdapt Fairytales"),
    ("ru", "RuWikiLarge", "Russian/RuWikiLarge"),
    ("it", "SimpitikiWiki", "Italian/Simpitiki Italian Wikipedia"),
    ("sl", "TSSlovene", "Slovene/Text Simplification Slovene"),
    ("it", "Teacher", "Italian/Teacher"),
    ("it", "Terence", "Italian/Terence"),
    ("de", "TextComplexityDE", "German/TextComplexityDE Parallel Corpus"),
    ("en", "WikiAutoEN", "English/WikiAuto"),
    ("fr", "WikiLargeFR", "French/WikiLargeFR Corpus"),
]
SPLITS = (("train", "train"), ("validation", "val"), ("test", "test"))

csv.field_size_limit(sys.maxsize)


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def simple_columns(fieldnames: list[str]) -> list[str]:
    def key(name: str) -> int:
        suffix = name[6:]
        return int(suffix) if suffix else 0

    return sorted(
        (name for name in fieldnames if re.fullmatch(r"simple\d*", name)), key=key
    )


def records_for(language: str, corpus: str, source_base: str, inventories: list):
    for split, filename_split in SPLITS:
        path = RAW_ROOT / "multisim" / f"{source_base}_{filename_split}.csv"
        if not path.is_file():
            raise FileNotFoundError(path)
        row_count = pair_count = 0
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or "original" not in reader.fieldnames:
                raise ValueError(f"Invalid MultiSim schema: {path}")
            columns = simple_columns(reader.fieldnames)
            for source_row, row in enumerate(reader):
                original = row.get("original")
                if not original:
                    raise ValueError(f"Empty original in {path}:{source_row + 2}")
                references = [row[column] for column in columns if row.get(column, "")]
                if not references:
                    raise ValueError(f"No simplification in {path}:{source_row + 2}")
                original_id = f"multisim:{slug(corpus)}:{split}:{source_row:09d}"
                for reference_index, simple in enumerate(references):
                    yield {
                        "id": f"{original_id}:r{reference_index:02d}",
                        "original_id": original_id,
                        "language": language,
                        "source": "MultiSim",
                        "corpus": corpus,
                        "upstream_split": split,
                        "original": original,
                        "simple": simple,
                        "reference_index": reference_index,
                        "source_dataset": "XenonMolecule/MultiSim",
                        "source_revision": REVISION,
                        "source_row": source_row,
                    }
                    pair_count += 1
                row_count += 1
        inventories.append({
            "language": language,
            "corpus": corpus,
            "upstream_split": split,
            "raw_path": str(path.relative_to(PROJECT_ROOT)),
            "raw_bytes": path.stat().st_size,
            "raw_sha256": sha256(path),
            "rows": row_count,
            "pairs": pair_count,
        })


def convert() -> dict[str, object]:
    outputs: list[dict[str, object]] = []
    inventories: list[dict[str, object]] = []
    for language, corpus, source_base in CORPORA:
        output = DATA_ROOT / language / f"multisim__{corpus}.jsonl"
        result = write_jsonl(
            output, records_for(language, corpus, source_base, inventories)
        )
        outputs.append({"language": language, "corpus": corpus, **result})
    report = {
        "source": "MultiSim",
        "source_revision": REVISION,
        "raw_root": "raw/multisim",
        "configurations": len(outputs),
        "raw_split_files": len(inventories),
        "raw_rows": sum(int(row["rows"]) for row in inventories),
        "normalized_pairs": sum(int(row["pairs"]) for row in outputs),
        "outputs": outputs,
    }
    write_json(INVENTORY_ROOT / "multisim_inventory.json", {"files": inventories})
    write_json(REPORT_ROOT / "multisim_conversion_validation.json", report)
    return report


if __name__ == "__main__":
    print(json.dumps(convert(), ensure_ascii=False))

