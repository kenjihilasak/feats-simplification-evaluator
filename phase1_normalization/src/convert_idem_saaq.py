#!/usr/bin/env python3
"""Normalize the received iDEM and Saaq al-Bambuu CSV package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from common import DATA_ROOT, INVENTORY_ROOT, PROJECT_ROOT, RAW_ROOT, REPORT_ROOT
from common import sha256, write_json, write_jsonl


RAW_PACKAGE = RAW_ROOT / "idem_&_saaq_al_bambuu"
INCLUDED_SOURCES = {"iDEM", "Saaq al-Bambuu"}
SOURCE_SLUGS = {"iDEM": "idem", "Saaq al-Bambuu": "saaq_al_bambuu"}
SPLIT_MAP = {"train": "train", "dev": "validation", "test": "test"}
STRATEGIES = (
    "Synonymy", "Modulation", "Compression", "Explanation",
    "Syntactic Change", "Omission",
)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        return list(reader.fieldnames), list(reader)


def source_revision(dataset_path: Path, splits_path: Path) -> str:
    return f"dataset:{sha256(dataset_path)};splits:{sha256(splits_path)}"


def original_key(source: str, language: str, text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]
    return f"{SOURCE_SLUGS[source]}:{language}:original:{digest}"


def convert(output_root: Path = DATA_ROOT) -> dict[str, object]:
    dataset_path = RAW_PACKAGE / "dataset.csv"
    splits_path = RAW_PACKAGE / "splits.csv"
    dataset_fields, dataset_rows = read_csv(dataset_path)
    split_fields, split_rows = read_csv(splits_path)
    required_dataset = {
        "pair_id", "group_id", "language", "source_text", "simplified_text",
        "labels", "is_labelled", "source_corpus", "genre", "domain",
        "annotation_state", "quality_status", *STRATEGIES,
    }
    required_splits = {
        "pair_id", "group_id", "language", "split", "seed", "split_source"
    }
    if missing := required_dataset.difference(dataset_fields):
        raise ValueError(f"dataset.csv missing columns: {sorted(missing)}")
    if missing := required_splits.difference(split_fields):
        raise ValueError(f"splits.csv missing columns: {sorted(missing)}")

    split_by_id: dict[str, dict[str, str]] = {}
    for row in split_rows:
        pair_id = row["pair_id"]
        if pair_id in split_by_id:
            raise ValueError(f"Duplicate pair_id in splits.csv: {pair_id}")
        split_by_id[pair_id] = row
    dataset_ids = {row["pair_id"] for row in dataset_rows}
    if len(dataset_ids) != len(dataset_rows):
        raise ValueError("Duplicate pair_id in dataset.csv")
    if dataset_ids != set(split_by_id):
        raise ValueError("dataset.csv and splits.csv pair_id sets differ")

    revision = source_revision(dataset_path, splits_path)
    selected = [row for row in dataset_rows if row["source_corpus"] in INCLUDED_SOURCES]
    reference_counts: defaultdict[str, int] = defaultdict(int)
    records_by_output: defaultdict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)

    for source_row, row in enumerate(dataset_rows):
        source = row["source_corpus"]
        if source not in INCLUDED_SOURCES:
            continue
        pair_id = row["pair_id"]
        split = split_by_id[pair_id]
        if split["group_id"] != row["group_id"] or split["language"] != row["language"]:
            raise ValueError(f"Metadata mismatch for pair_id {pair_id}")
        if split["split"] not in SPLIT_MAP:
            raise ValueError(f"Unknown split {split['split']!r} for pair_id {pair_id}")
        labels = json.loads(row["labels"])
        active = [strategy for strategy in STRATEGIES if row[strategy] == "1"]
        if set(labels) != set(active):
            raise ValueError(f"Strategy labels/flags disagree for pair_id {pair_id}")
        original_id = original_key(source, row["language"], row["source_text"])
        reference_index = reference_counts[original_id]
        reference_counts[original_id] += 1
        record = {
            "id": f"{SOURCE_SLUGS[source]}:{row['language']}:{pair_id}",
            "original_id": original_id,
            "language": row["language"],
            "source": source,
            "corpus": source,
            "upstream_split": SPLIT_MAP[split["split"]],
            "original": row["source_text"],
            "simple": row["simplified_text"],
            "reference_index": reference_index,
            "source_dataset": "multilingual_sentence_alignment_v2",
            "source_revision": revision,
            "source_row": source_row,
            "upstream_pair_id": pair_id,
            "upstream_group_id": row["group_id"],
            "upstream_split_original": split["split"],
            "upstream_split_seed": int(split["seed"]),
            "upstream_split_source": split["split_source"],
            "strategy_labels": labels,
            "strategy_flags": {strategy: int(row[strategy]) for strategy in STRATEGIES},
            "is_labelled": row["is_labelled"].casefold() == "true",
            "genre": row["genre"],
            "domain": row["domain"],
            "annotation_state": row["annotation_state"],
            "quality_status": row["quality_status"],
        }
        records_by_output[(row["language"], source)].append(record)

    outputs = []
    for (language, source), records in sorted(records_by_output.items()):
        filename = f"{SOURCE_SLUGS[source]}__{source.replace(' ', '-')}.jsonl"
        result = write_jsonl(output_root / language / filename, records)
        outputs.append({"language": language, "source": source, **result})

    included_counts = Counter(row["source_corpus"] for row in selected)
    excluded_counts = Counter(
        row["source_corpus"] for row in dataset_rows
        if row["source_corpus"] not in INCLUDED_SOURCES
    )
    report = {
        "raw_package": str(RAW_PACKAGE.relative_to(PROJECT_ROOT)),
        "dataset_sha256": sha256(dataset_path),
        "splits_sha256": sha256(splits_path),
        "raw_pairs": len(dataset_rows),
        "normalized_pairs": sum(int(row["pairs"]) for row in outputs),
        "included_sources": dict(sorted(included_counts.items())),
        "excluded_sources": dict(sorted(excluded_counts.items())),
        "outputs": outputs,
    }
    write_json(
        INVENTORY_ROOT / "idem_saaq_inventory.json", report
    )
    write_json(
        REPORT_ROOT / "idem_saaq_conversion_validation.json",
        report,
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(convert(), ensure_ascii=False))


if __name__ == "__main__":
    main()
