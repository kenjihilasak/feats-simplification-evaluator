#!/usr/bin/env python3
"""Build and audit the canonical FEATS complex-simple JSONL corpus."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = PROJECT_ROOT / "raw"
DATA_ROOT = PROJECT_ROOT / "phase1_normalization" / "data"
METADATA_ROOT = PROJECT_ROOT / "metadata"
INVENTORY_ROOT = METADATA_ROOT / "inventories"
REPORT_ROOT = METADATA_ROOT / "conversion_reports"

MULTISIM_REVISION = "3213620ecd82d5f579b18c58532973442ec3a1b1"
SIMPLIFYUR_REVISION = "cdb3203d39abfcc365232c8aae1b35afa5d43bd8"
ALIGN_REVISION = "2026-02-28_fullCorpus_v1"

MULTISIM_CORPORA = [
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
REQUIRED_FIELDS = {
    "id", "original_id", "language", "source", "corpus",
    "upstream_split", "original", "simple", "reference_index",
    "source_dataset", "source_revision", "source_row",
}
VALID_SPLITS = {"train", "validation", "test", None}

csv.field_size_limit(sys.maxsize)


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def write_jsonl(path: Path, records: Iterable[dict[str, object]]) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    count = 0
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            stream.write("\n")
            count += 1
    os.replace(temporary, path)
    return {
        "output_path": str(path.relative_to(PROJECT_ROOT)),
        "pairs": count,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def simple_columns(fieldnames: list[str]) -> list[str]:
    def key(name: str) -> int:
        suffix = name[6:]
        return int(suffix) if suffix else 0
    return sorted(
        (name for name in fieldnames if re.fullmatch(r"simple\d*", name)), key=key
    )


def multisim_records(
    language: str, corpus: str, source_base: str
) -> tuple[Iterator[dict[str, object]], list[dict[str, object]]]:
    inventories: list[dict[str, object]] = []

    def generate() -> Iterator[dict[str, object]]:
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
                    if original is None or original == "":
                        raise ValueError(f"Empty original in {path}:{source_row + 2}")
                    references = [row[column] for column in columns if row.get(column, "") != ""]
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
                            "source_revision": MULTISIM_REVISION,
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

    return generate(), inventories


def convert_multisim() -> dict[str, object]:
    outputs: list[dict[str, object]] = []
    inventories: list[dict[str, object]] = []
    for language, corpus, source_base in MULTISIM_CORPORA:
        records, corpus_inventory = multisim_records(language, corpus, source_base)
        output = DATA_ROOT / language / f"multisim__{corpus}.jsonl"
        outputs.append({"language": language, "corpus": corpus, **write_jsonl(output, records)})
        inventories.extend(corpus_inventory)
    report = {
        "source": "MultiSim",
        "source_revision": MULTISIM_REVISION,
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


def split_groups(path: Path) -> list[list[str]]:
    text = path.read_text(encoding="utf-8-sig")
    groups: list[list[str]] = [[]]
    for raw_line in text.splitlines():
        line = raw_line.rstrip("\r")
        if line == "--":
            groups.append([])
        elif line != "":
            groups[-1].append(line)
    # The upstream files terminate with ``--``; that delimiter does not
    # represent an additional example.
    if groups and not groups[-1]:
        groups.pop()
    return groups


def convert_simplifyur() -> dict[str, object]:
    complex_path = RAW_ROOT / "simplifyur" / "Data" / "Complex.txt"
    simple_path = RAW_ROOT / "simplifyur" / "Data" / "Simplified.txt"
    complex_groups = split_groups(complex_path)
    simple_groups = split_groups(simple_path)
    if len(complex_groups) != len(simple_groups):
        raise ValueError("SimplifyUR group counts differ")

    def records() -> Iterator[dict[str, object]]:
        for source_row, (originals, references) in enumerate(zip(complex_groups, simple_groups)):
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
                    "source_revision": SIMPLIFYUR_REVISION,
                    "source_row": source_row,
                }

    output = DATA_ROOT / "ur" / "simplifyur__SimplifyUR.jsonl"
    output_report = write_jsonl(output, records())
    report = {
        "source": "SimplifyUR",
        "source_revision": SIMPLIFYUR_REVISION,
        "groups": len(complex_groups),
        "normalized_pairs": output_report["pairs"],
        **output_report,
    }
    write_json(INVENTORY_ROOT / "simplifyur_inventory.json", report)
    write_json(REPORT_ROOT / "simplifyur_conversion_validation.json", report)
    return report


def convert_align_and_shine() -> dict[str, object]:
    path = (
        RAW_ROOT / "align_and_shine" / ALIGN_REVISION / "data"
        / f"filtered_sentence_pairs_{ALIGN_REVISION}.csv"
    )
    by_language: dict[str, list[dict[str, str]]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
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
                    f"alignandshine:{language}:wikipediavikidia:null:"
                    f"{source_row:09d}"
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
                    "source_revision": ALIGN_REVISION,
                    "source_row": source_row,
                }

        output = DATA_ROOT / language / "align_and_shine__Wikipedia-Vikidia.jsonl"
        outputs.append({"language": language, **write_jsonl(output, records())})
    report = {
        "source": "Align-and-Shine",
        "source_revision": ALIGN_REVISION,
        "raw_path": str(path.relative_to(PROJECT_ROOT)),
        "raw_sha256": sha256(path),
        "normalized_pairs": sum(int(row["pairs"]) for row in outputs),
        "outputs": outputs,
    }
    write_json(INVENTORY_ROOT / "align_and_shine_inventory.json", report)
    write_json(REPORT_ROOT / "align_and_shine_conversion_validation.json", report)
    return report


def iter_jsonl(path: Path) -> Iterator[dict[str, object]]:
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON {path}:{line_number}") from error
            if not isinstance(value, dict):
                raise ValueError(f"Non-object JSON {path}:{line_number}")
            yield value


def audit_all() -> dict[str, object]:
    files = sorted(DATA_ROOT.glob("*/*.jsonl"))
    ids: set[str] = set()
    by_source: Counter[str] = Counter()
    by_language: Counter[str] = Counter()
    by_split: Counter[str] = Counter()
    missing = empty = invalid_split = invalid_layout = duplicates = total = 0
    for path in files:
        if path.parent.parent != DATA_ROOT:
            invalid_layout += 1
        for record in iter_jsonl(path):
            total += 1
            absent = REQUIRED_FIELDS.difference(record)
            missing += bool(absent)
            empty += not bool(record.get("original")) or not bool(record.get("simple"))
            invalid_split += record.get("upstream_split") not in VALID_SPLITS
            pair_id = str(record.get("id", ""))
            if pair_id in ids:
                duplicates += 1
            ids.add(pair_id)
            by_source[str(record.get("source"))] += 1
            by_language[str(record.get("language"))] += 1
            split = record.get("upstream_split")
            by_split["null" if split is None else str(split)] += 1
    valid = (
        len(files) == 25 and total == 1_452_597 and len(ids) == total
        and missing == empty == invalid_split == invalid_layout == duplicates == 0
    )
    report = {
        "valid": valid,
        "jsonl_files": len(files),
        "normalized_pairs": total,
        "normalized_bytes": sum(path.stat().st_size for path in files),
        "unique_ids": len(ids),
        "duplicate_ids": duplicates,
        "missing_field_records": missing,
        "empty_text_records": empty,
        "invalid_upstream_split_records": invalid_split,
        "invalid_layout_records": invalid_layout,
        "records_by_source": dict(sorted(by_source.items())),
        "records_by_language": dict(sorted(by_language.items())),
        "records_by_upstream_split": dict(sorted(by_split.items())),
    }
    write_json(REPORT_ROOT / "overall_validation.json", report)
    if not valid:
        raise RuntimeError(json.dumps(report, ensure_ascii=False))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("multisim", "simplifyur", "align-and-shine", "all", "audit-all"),
    )
    args = parser.parse_args()
    if args.command in {"multisim", "all"}:
        print(json.dumps(convert_multisim(), ensure_ascii=False))
    if args.command in {"simplifyur", "all"}:
        print(json.dumps(convert_simplifyur(), ensure_ascii=False))
    if args.command in {"align-and-shine", "all"}:
        print(json.dumps(convert_align_and_shine(), ensure_ascii=False))
    if args.command in {"audit-all", "all"}:
        print(json.dumps(audit_all(), ensure_ascii=False))


if __name__ == "__main__":
    main()
