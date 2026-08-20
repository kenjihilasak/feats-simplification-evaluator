#!/usr/bin/env python3
"""Group post-cleaning originals that retain alternatives across corpora."""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "phase2b_consolidation" / "data"
DEFAULT_OUTPUT = (
    PROJECT_ROOT / "phase2b_consolidation" / "groups"
    / "cross_corpus_multi_simplifications.jsonl"
)
DEFAULT_SUMMARY = (
    PROJECT_ROOT / "phase2b_consolidation" / "groups"
    / "cross_corpus_multi_simplifications_summary.md"
)
SPACE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    """Match the conservative text identity used by Phase 1."""
    if not isinstance(value, str):
        raise TypeError("Identity fields must be strings")
    return SPACE.sub(" ", unicodedata.normalize("NFC", value)).strip()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON {path}:{line_number}") from error


def input_files(input_root: Path) -> list[Path]:
    files = sorted(input_root.glob("*/feats_consolidated.jsonl"))
    if not files:
        raise FileNotFoundError(
            f"No Phase 2b JSONL files under {input_root}/<language>/"
        )
    return files


def initialise_database(path: Path) -> sqlite3.Connection:
    database = sqlite3.connect(path)
    database.execute("PRAGMA journal_mode=OFF")
    database.execute("PRAGMA synchronous=OFF")
    database.execute("PRAGMA temp_store=FILE")
    database.execute(
        "CREATE TABLE pairs (canonical_pair_id TEXT PRIMARY KEY, "
        "canonical_original_id TEXT NOT NULL, language TEXT NOT NULL)"
    )
    database.execute(
        "CREATE TABLE pair_corpora (canonical_pair_id TEXT NOT NULL, "
        "source TEXT NOT NULL, corpus TEXT NOT NULL, "
        "PRIMARY KEY (canonical_pair_id, source, corpus))"
    )
    return database


def index_pairs(database: sqlite3.Connection, files: list[Path]) -> int:
    total = 0
    for path in files:
        path_language = path.parent.name
        for record in iter_jsonl(path):
            language = record["language"]
            if language != path_language:
                raise ValueError(
                    f"Language/path mismatch in {path}: {record.get('id')}"
                )
            pair_id = record["canonical_pair_id"]
            original_id = record["canonical_original_id"]
            database.execute(
                "INSERT INTO pairs VALUES (?,?,?)",
                (pair_id, original_id, language),
            )
            corpora = {
                (item["source"], item["corpus"])
                for item in record.get("corpora", [])
            }
            if not corpora:
                corpora = {
                    (item["source"], item["corpus"])
                    for item in record.get("provenance", [])
                }
            if not corpora:
                raise ValueError(f"Pair has no corpus provenance: {pair_id}")
            database.executemany(
                "INSERT INTO pair_corpora VALUES (?,?,?)",
                ((pair_id, source, corpus) for source, corpus in sorted(corpora)),
            )
            total += 1
        database.commit()
    database.execute(
        "CREATE INDEX pairs_original ON pairs(canonical_original_id)"
    )
    database.execute(
        "CREATE INDEX pair_corpora_pair ON pair_corpora(canonical_pair_id)"
    )
    database.commit()
    return total


def eligible_originals(database: sqlite3.Connection) -> dict[str, tuple[str, int, int]]:
    query = """
        SELECT p.canonical_original_id, MIN(p.language),
               COUNT(DISTINCT p.canonical_pair_id),
               COUNT(DISTINCT pc.source || char(31) || pc.corpus)
        FROM pairs p
        JOIN pair_corpora pc USING (canonical_pair_id)
        GROUP BY p.canonical_original_id
        HAVING COUNT(DISTINCT p.canonical_pair_id) > 1
           AND COUNT(DISTINCT pc.source || char(31) || pc.corpus) > 1
    """
    return {
        original_id: (language, pair_count, corpus_count)
        for original_id, language, pair_count, corpus_count
        in database.execute(query)
    }


def simplification(record: dict) -> dict:
    return {
        "canonical_pair_id": record["canonical_pair_id"],
        "simple": record["simple"],
        "phase1_occurrence_count": record["phase1_occurrence_count"],
        "phase2_retained_occurrence_count": record[
            "phase2_retained_occurrence_count"
        ],
        "partially_retained": record["partially_retained"],
        "sources": record["sources"],
        "corpora": record["corpora"],
        "upstream_splits": record["upstream_splits"],
        "provenance": record["provenance"],
    }


def grouped_record(records: list[dict]) -> dict:
    records.sort(key=lambda item: item["canonical_pair_id"])
    first = records[0]
    original_ids = {item["canonical_original_id"] for item in records}
    languages = {item["language"] for item in records}
    originals = {normalize_text(item["original"]) for item in records}
    if len(original_ids) != 1 or len(languages) != 1 or len(originals) != 1:
        raise ValueError(f"Inconsistent canonical original group: {sorted(original_ids)}")

    corpora = sorted({
        (item["source"], item["corpus"])
        for record in records for item in record["corpora"]
    })
    sources = sorted({source for source, _ in corpora})
    return {
        "group_id": first["canonical_original_id"],
        "canonical_original_id": first["canonical_original_id"],
        "language": first["language"],
        "original": next(iter(originals)),
        "distinct_simplification_count": len(records),
        "source_count": len(sources),
        "corpus_count": len(corpora),
        "sources": sources,
        "corpora": [
            {"source": source, "corpus": corpus}
            for source, corpus in corpora
        ],
        "simplifications": [simplification(record) for record in records],
    }


def write_summary(
    path: Path,
    input_root: Path,
    input_pair_count: int,
    groups: list[dict],
) -> None:
    language_groups = Counter(group["language"] for group in groups)
    language_pairs = Counter()
    for group in groups:
        language_pairs[group["language"]] += group["distinct_simplification_count"]

    lines = [
        "# Cross-corpus originals with multiple simplifications",
        "",
        f"Input: `{display_path(input_root)}` (post-cleaning Phase 2b data).",
        "",
        "A group is included when the same `canonical_original_id` retains at least two distinct",
        "`canonical_pair_id` values and provenance from at least two distinct `(source, corpus)`",
        "combinations after Phase 2 cleaning.",
        "",
        f"- Phase 2b pairs scanned: **{input_pair_count:,}**",
        f"- Qualifying canonical originals: **{len(groups):,}**",
        f"- Distinct simplifications in those groups: **{sum(language_pairs.values()):,}**",
        "",
        "| Language | Canonical originals | Distinct simplifications |",
        "|---|---:|---:|",
    ]
    for language in sorted(language_groups):
        lines.append(
            f"| {language} | {language_groups[language]:,} | "
            f"{language_pairs[language]:,} |"
        )
    lines += [
        "",
        "## Fields",
        "",
        "| Field | Description |",
        "|---|---|",
        "| `group_id` | Alias of `canonical_original_id`. |",
        "| `canonical_original_id` | Shared ID of the original sentence. |",
        "| `language` | Language code. |",
        "| `original` | Canonicalized original sentence. |",
        "| `distinct_simplification_count` | Number of retained simplifications in the group. |",
        "| `source_count` | Number of distinct sources represented. |",
        "| `corpus_count` | Number of distinct `(source, corpus)` combinations. |",
        "| `sources` | Sources represented in the group. |",
        "| `corpora` | Corpus combinations represented in the group. |",
        "| `simplifications` | Simplified texts, pair IDs, retention counts, and provenance. |",
        "",
        "Each `simplifications[]` item contains `canonical_pair_id`, `simple`, the two",
        "occurrence counts, `partially_retained`, `sources`, `corpora`,",
        "`upstream_splits`, and `provenance` with the meanings documented in",
        "`phase2b_consolidation/README.md`.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("\n".join(lines), encoding="utf-8")
    os.replace(temporary, path)


def validate_groups(groups: list[dict]) -> None:
    seen = set()
    for group in groups:
        original_id = group["canonical_original_id"]
        if original_id in seen:
            raise ValueError(f"Duplicate group: {original_id}")
        seen.add(original_id)
        simplifications = group["simplifications"]
        pair_ids = {item["canonical_pair_id"] for item in simplifications}
        corpora = {
            (item["source"], item["corpus"])
            for item in group["corpora"]
        }
        if len(pair_ids) < 2 or len(corpora) < 2:
            raise ValueError(f"Ineligible group emitted: {original_id}")
        if group["distinct_simplification_count"] != len(pair_ids):
            raise ValueError(f"Incorrect simplification count: {original_id}")
        if group["corpus_count"] != len(corpora):
            raise ValueError(f"Incorrect corpus count: {original_id}")


def build_groups(
    input_root: Path,
    output_path: Path,
    summary_path: Path,
    temp_root: Path | None = None,
) -> dict:
    files = input_files(input_root)
    with tempfile.TemporaryDirectory(prefix="feats_cross_corpus_", dir=temp_root) as temp:
        database = initialise_database(Path(temp) / "groups.sqlite")
        try:
            input_pair_count = index_pairs(database, files)
            eligible = eligible_originals(database)
        finally:
            database.close()

    grouped: dict[str, list[dict]] = {original_id: [] for original_id in eligible}
    for path in files:
        for record in iter_jsonl(path):
            original_id = record["canonical_original_id"]
            if original_id in grouped:
                grouped[original_id].append(record)

    groups = [grouped_record(records) for records in grouped.values()]
    groups.sort(key=lambda item: (item["language"], item["canonical_original_id"]))
    validate_groups(groups)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for group in groups:
            handle.write(json.dumps(group, ensure_ascii=False, separators=(",", ":")) + "\n")
    os.replace(temporary, output_path)
    write_summary(summary_path, input_root, input_pair_count, groups)

    return {
        "input_files": len(files),
        "input_pairs": input_pair_count,
        "groups": len(groups),
        "grouped_pairs": sum(group["distinct_simplification_count"] for group in groups),
        "output": str(output_path),
        "summary": str(summary_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--temp-root", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_groups(
        args.input_root,
        args.output,
        args.summary,
        args.temp_root,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
