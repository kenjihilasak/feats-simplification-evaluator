#!/usr/bin/env python3
"""Validate Phase 2b against cleaned observations and canonical identities."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

from consolidate_cleaned import (
    DEFAULT_CLEANED,
    DEFAULT_IDENTITY,
    DEFAULT_OUTPUT,
    DEFAULT_REPORTS,
    iter_jsonl,
)


def add_error(errors: list[str], message: str, maximum: int = 100) -> None:
    if len(errors) < maximum:
        errors.append(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def cleaned_ids(root: Path, errors: list[str]) -> tuple[set[str], Counter]:
    ids: set[str] = set()
    counts = Counter()
    for path in sorted(root.glob("*/*.jsonl")):
        language = path.parent.name
        for record in iter_jsonl(path):
            pair_id = record["id"]
            if pair_id in ids:
                add_error(errors, f"Duplicate cleaned observation ID: {pair_id}")
            ids.add(pair_id)
            counts[language] += 1
    return ids, counts


def identity_map(path: Path, required: set[str]) -> dict[str, tuple[str, str, str, int]]:
    result = {}
    columns = [
        "id", "canonical_original_id", "canonical_pair_id", "language",
        "pair_occurrence_count",
    ]
    for batch in pq.ParquetFile(path).iter_batches(batch_size=50_000, columns=columns):
        for values in zip(*(batch.column(index).to_pylist() for index in range(len(columns)))):
            if values[0] in required:
                result[values[0]] = (values[1], values[2], values[3], int(values[4]))
    return result


def expected_aggregates(provenance: list[dict]) -> tuple[list[str], list[dict], list]:
    sources = sorted({item["source"] for item in provenance})
    corpora = sorted({(item["source"], item["corpus"]) for item in provenance})
    corpus_objects = [{"source": source, "corpus": corpus} for source, corpus in corpora]
    splits = sorted(
        {item.get("upstream_split") for item in provenance},
        key=lambda value: (value is None, "" if value is None else value),
    )
    return sources, corpus_objects, splits


def validate(cleaned_root: Path, identity_path: Path, output_root: Path,
             summary_path: Path) -> dict:
    errors: list[str] = []
    unseen, cleaned_by_language = cleaned_ids(cleaned_root, errors)
    identities = identity_map(identity_path, unseen)
    missing_identity = unseen.difference(identities)
    if missing_identity:
        add_error(errors, f"{len(missing_identity)} cleaned IDs missing from identity registry")

    output_by_language = Counter()
    provenance_by_language = Counter()
    canonical_pairs: set[str] = set()
    file_rows = []
    output_files = sorted(output_root.glob("*/*.jsonl"))
    expected_languages = set(cleaned_by_language)
    observed_languages = {path.parent.name for path in output_files}
    if observed_languages != expected_languages:
        add_error(
            errors,
            f"Language layout mismatch; missing={sorted(expected_languages-observed_languages)}, "
            f"extra={sorted(observed_languages-expected_languages)}",
        )

    for path in output_files:
        language = path.parent.name
        file_pairs = 0
        file_observations = 0
        for line_number, record in enumerate(iter_jsonl(path), 1):
            pair_id = record.get("canonical_pair_id")
            original_id = record.get("canonical_original_id")
            label = f"{language}/{path.name}:{line_number}"
            if pair_id in canonical_pairs:
                add_error(errors, f"Duplicate canonical pair: {pair_id}")
            canonical_pairs.add(pair_id)
            if record.get("id") != pair_id or record.get("original_id") != original_id:
                add_error(errors, f"Compatibility ID mismatch at {label}")
            if record.get("language") != language:
                add_error(errors, f"Language mismatch at {label}")

            provenance = record.get("provenance")
            if not isinstance(provenance, list) or not provenance:
                add_error(errors, f"Missing provenance at {label}")
                continue
            file_observations += len(provenance)
            if record.get("phase2_retained_occurrence_count") != len(provenance):
                add_error(errors, f"Retained count mismatch at {label}")
            sources, corpora, splits = expected_aggregates(provenance)
            if record.get("sources") != sources or record.get("corpora") != corpora:
                add_error(errors, f"Source/corpus aggregate mismatch at {label}")
            if record.get("upstream_splits") != splits:
                add_error(errors, f"Split aggregate mismatch at {label}")

            phase1_counts = set()
            for occurrence in provenance:
                observation_id = occurrence.get("id")
                identity = identities.get(observation_id)
                if identity is None:
                    add_error(errors, f"Unknown provenance ID at {label}: {observation_id}")
                    continue
                expected_original, expected_pair, expected_language, phase1_count = identity
                if (original_id, pair_id, language) != (
                    expected_original, expected_pair, expected_language
                ):
                    add_error(errors, f"Canonical identity mismatch at {label}: {observation_id}")
                if observation_id not in unseen:
                    add_error(errors, f"Repeated provenance ID: {observation_id}")
                else:
                    unseen.remove(observation_id)
                phase1_counts.add(phase1_count)
                provenance_by_language[language] += 1
            if len(phase1_counts) != 1:
                add_error(errors, f"Inconsistent Phase 1 occurrence counts at {label}")
            else:
                phase1_count = next(iter(phase1_counts))
                if record.get("phase1_occurrence_count") != phase1_count:
                    add_error(errors, f"Phase 1 occurrence count mismatch at {label}")
                expected_partial = len(provenance) < phase1_count
                if record.get("partially_retained") is not expected_partial:
                    add_error(errors, f"Partial-retention flag mismatch at {label}")
            output_by_language[language] += 1
            file_pairs += 1
        file_rows.append(
            {
                "language": language,
                "file": path.name,
                "consolidated_pairs": file_pairs,
                "cleaned_observations": file_observations,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )

    if unseen:
        add_error(errors, f"{len(unseen)} cleaned IDs absent from consolidated provenance")

    with summary_path.open(newline="", encoding="utf-8") as handle:
        summary_rows = list(csv.DictReader(handle))
    global_rows = [row for row in summary_rows if row["scope"] == "global"]
    if len(global_rows) != 1:
        add_error(errors, "Summary must contain exactly one global row")
    else:
        global_row = global_rows[0]
        if int(global_row["cleaned_observations"]) != sum(provenance_by_language.values()):
            add_error(errors, "Global cleaned-observation summary mismatch")
        if int(global_row["consolidated_pairs"]) != sum(output_by_language.values()):
            add_error(errors, "Global consolidated-pair summary mismatch")
    for row in (item for item in summary_rows if item["scope"] == "language"):
        language = row["language"]
        if int(row["cleaned_observations"]) != provenance_by_language[language]:
            add_error(errors, f"Cleaned-observation summary mismatch for {language}")
        if int(row["consolidated_pairs"]) != output_by_language[language]:
            add_error(errors, f"Consolidated-pair summary mismatch for {language}")

    return {
        "valid": not errors,
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "cleaned_observations": sum(cleaned_by_language.values()),
        "identity_rows_used": len(identities),
        "consolidated_pairs": len(canonical_pairs),
        "output_files": len(output_files),
        "cleaned_observations_by_language": dict(sorted(cleaned_by_language.items())),
        "consolidated_pairs_by_language": dict(sorted(output_by_language.items())),
        "files": file_rows,
        "errors": errors,
    }


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleaned-root", type=Path, default=DEFAULT_CLEANED)
    parser.add_argument("--identity", type=Path, default=DEFAULT_IDENTITY)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--summary", type=Path, default=DEFAULT_REPORTS / "consolidation_summary.csv"
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORTS / "validation.json")
    args = parser.parse_args()
    result = validate(args.cleaned_root, args.identity, args.output_root, args.summary)
    write_json(args.report, result)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
