#!/usr/bin/env python3
"""Consolidate exact duplicate Phase 2 pairs while preserving provenance."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CLEANED = (
    PROJECT_ROOT / "phase2_cleaning" / "runs"
    / "2026-08-05_complexity_smp01_labse062_095_full_flat_v2" / "cleaned"
)
DEFAULT_IDENTITY = PROJECT_ROOT / "phase1_normalization" / "deduplication" / "pair_identity.parquet"
DEFAULT_OUTPUT = PROJECT_ROOT / "phase2b_consolidation" / "data"
DEFAULT_REPORTS = PROJECT_ROOT / "phase2b_consolidation" / "reports"


def connection(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.execute("PRAGMA journal_mode=OFF")
    db.execute("PRAGMA synchronous=OFF")
    db.execute("PRAGMA temp_store=FILE")
    db.execute(
        "CREATE TABLE identity (id TEXT PRIMARY KEY, canonical_original_id TEXT NOT NULL, "
        "canonical_pair_id TEXT NOT NULL, language TEXT NOT NULL, pair_occurrence_count INTEGER NOT NULL)"
    )
    db.execute(
        "CREATE TABLE cleaned (id TEXT PRIMARY KEY, language TEXT NOT NULL, source TEXT NOT NULL, "
        "corpus TEXT NOT NULL, original TEXT NOT NULL, simple TEXT NOT NULL, payload TEXT NOT NULL)"
    )
    return db


def load_identity(db: sqlite3.Connection, path: Path) -> int:
    parquet = pq.ParquetFile(path)
    total = 0
    columns = ["id", "canonical_original_id", "canonical_pair_id", "language", "pair_occurrence_count"]
    for batch in parquet.iter_batches(batch_size=50_000, columns=columns):
        rows = zip(*(batch.column(index).to_pylist() for index in range(len(columns))))
        db.executemany("INSERT INTO identity VALUES (?,?,?,?,?)", rows)
        total += batch.num_rows
    db.execute("CREATE INDEX identity_pair ON identity(canonical_pair_id)")
    db.commit()
    return total


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"Invalid JSON {path}:{line_number}") from error


def load_cleaned(db: sqlite3.Connection, root: Path) -> tuple[int, int]:
    files = sorted(root.glob("*/*.jsonl"))
    if not files:
        raise FileNotFoundError(f"No cleaned JSONL files under {root}/<language>/")
    total = 0
    for path in files:
        language = path.parent.name
        rows = []
        for record in iter_jsonl(path):
            if record.get("language") != language:
                raise ValueError(f"Language/path mismatch in {path}: {record.get('id')}")
            rows.append((
                record["id"], language, record["source"], record["corpus"],
                record["original"], record["simple"],
                json.dumps(record, ensure_ascii=False, separators=(",", ":")),
            ))
            if len(rows) == 10_000:
                db.executemany("INSERT INTO cleaned VALUES (?,?,?,?,?,?,?)", rows)
                total += len(rows)
                rows.clear()
        if rows:
            db.executemany("INSERT INTO cleaned VALUES (?,?,?,?,?,?,?)", rows)
            total += len(rows)
        db.commit()
    unknown = db.execute(
        "SELECT c.id FROM cleaned c LEFT JOIN identity i USING(id) WHERE i.id IS NULL LIMIT 1"
    ).fetchone()
    if unknown:
        raise ValueError(f"Cleaned observation missing from Phase 1 identity registry: {unknown[0]}")
    mismatch = db.execute(
        "SELECT c.id FROM cleaned c JOIN identity i USING(id) WHERE c.language != i.language LIMIT 1"
    ).fetchone()
    if mismatch:
        raise ValueError(f"Language mismatch with identity registry: {mismatch[0]}")
    db.execute("CREATE INDEX cleaned_language ON cleaned(language)")
    db.commit()
    return len(files), total


def provenance(record: dict) -> dict:
    return {key: value for key, value in record.items() if key not in {"language", "original", "simple"}}


def consolidated_record(rows: list[tuple]) -> dict:
    first = rows[0]
    records = [json.loads(row[6]) for row in rows]
    phase1_count = int(first[9])
    retained_count = len(rows)
    sources = sorted({record["source"] for record in records})
    corpora = sorted(
        {(record["source"], record["corpus"]) for record in records}
    )
    splits = sorted(
        {record.get("upstream_split") for record in records},
        key=lambda value: (value is None, "" if value is None else value),
    )
    return {
        "id": first[8], "original_id": first[7],
        "canonical_original_id": first[7], "canonical_pair_id": first[8],
        "language": first[1], "original": first[4], "simple": first[5],
        "phase1_occurrence_count": phase1_count,
        "phase2_retained_occurrence_count": retained_count,
        "partially_retained": retained_count < phase1_count,
        "sources": sources,
        "corpora": [{"source": source, "corpus": corpus} for source, corpus in corpora],
        "upstream_splits": splits,
        "provenance": [provenance(record) for record in records],
    }


def write_data(db: sqlite3.Connection, output_root: Path) -> dict[str, int]:
    query = """
        SELECT c.id, c.language, c.source, c.corpus, c.original, c.simple, c.payload,
               i.canonical_original_id, i.canonical_pair_id, i.pair_occurrence_count
        FROM cleaned c JOIN identity i USING(id)
        ORDER BY c.language, i.canonical_pair_id, c.id
    """
    output_root.mkdir(parents=True, exist_ok=True)
    counts = defaultdict(int)
    current_pair = current_language = None
    group = []
    handle = temporary = destination = None

    def emit() -> None:
        if group:
            handle.write(json.dumps(consolidated_record(group), ensure_ascii=False, separators=(",", ":")) + "\n")
            counts[current_language] += 1

    for row in db.execute(query):
        language, pair_id = row[1], row[8]
        if current_language is not None and language != current_language:
            emit()
            group = []
            handle.close()
            os.replace(temporary, destination)
            handle = None
        if language != current_language:
            destination = output_root / language / "feats_consolidated.jsonl"
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(".jsonl.tmp")
            handle = temporary.open("w", encoding="utf-8", newline="\n")
            current_language, current_pair = language, None
        if current_pair is not None and pair_id != current_pair:
            emit()
            group = []
        current_pair = pair_id
        group.append(row)
    if handle is not None:
        emit()
        handle.close()
        os.replace(temporary, destination)
    return dict(counts)


SUMMARY_FIELDS = [
    "scope", "language", "cleaned_observations", "consolidated_pairs",
    "redundant_observations_removed", "redundant_pct", "unique_originals",
    "multiple_simplification_original_groups", "partially_retained_pairs",
    "cross_source_pair_groups", "cross_corpus_pair_groups",
]


def summary_row(db, scope, where="", parameters=(), language=""):
    clause = f" WHERE {where}" if where else ""
    observations, pairs, originals = db.execute(
        f"SELECT COUNT(*), COUNT(DISTINCT i.canonical_pair_id), "
        f"COUNT(DISTINCT i.canonical_original_id) FROM cleaned c JOIN identity i USING(id){clause}",
        parameters,
    ).fetchone()
    multi = db.execute(
        f"SELECT COUNT(*) FROM (SELECT i.canonical_original_id FROM cleaned c "
        f"JOIN identity i USING(id){clause} GROUP BY i.canonical_original_id "
        "HAVING COUNT(DISTINCT i.canonical_pair_id) > 1)", parameters,
    ).fetchone()[0]
    partial, cross_source, cross_corpus = db.execute(
        f"SELECT COALESCE(SUM(retained < phase1),0), COALESCE(SUM(sources > 1),0), "
        f"COALESCE(SUM(corpora > 1),0) FROM (SELECT i.canonical_pair_id, COUNT(*) retained, "
        f"MAX(i.pair_occurrence_count) phase1, COUNT(DISTINCT c.source) sources, "
        f"COUNT(DISTINCT c.source || char(31) || c.corpus) corpora FROM cleaned c "
        f"JOIN identity i USING(id){clause} GROUP BY i.canonical_pair_id)", parameters,
    ).fetchone()
    redundant = observations - pairs
    return {
        "scope": scope, "language": language, "cleaned_observations": observations,
        "consolidated_pairs": pairs, "redundant_observations_removed": redundant,
        "redundant_pct": round(redundant / observations * 100, 6) if observations else 0.0,
        "unique_originals": originals, "multiple_simplification_original_groups": multi,
        "partially_retained_pairs": partial, "cross_source_pair_groups": cross_source,
        "cross_corpus_pair_groups": cross_corpus,
    }


def write_reports(db: sqlite3.Connection, reports_root: Path, input_root: Path) -> list[dict]:
    reports_root.mkdir(parents=True, exist_ok=True)
    rows = [summary_row(db, "global")]
    for (language,) in db.execute("SELECT DISTINCT language FROM cleaned ORDER BY language"):
        rows.append(summary_row(db, "language", "c.language=?", (language,), language))
    csv_path = reports_root / "consolidation_summary.csv"
    temporary = csv_path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=SUMMARY_FIELDS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, csv_path)

    overall = rows[0]
    lines = [
        "# Phase 2b consolidation summary", "",
        f"Input: `{input_root}`.", "",
        "| Language | Cleaned observations | Unique pairs | Exact duplicates removed | Partially retained pairs |",
        "|---|---:|---:|---:|---:|",
        f"| **All** | **{overall['cleaned_observations']:,}** | **{overall['consolidated_pairs']:,}** | "
        f"**{overall['redundant_observations_removed']:,}** | **{overall['partially_retained_pairs']:,}** |",
    ]
    for row in rows[1:]:
        lines.append(
            f"| {row['language']} | {row['cleaned_observations']:,} | {row['consolidated_pairs']:,} | "
            f"{row['redundant_observations_removed']:,} | {row['partially_retained_pairs']:,} |"
        )
    lines += [
        "", "Each output row is one canonical original–simplification pair. "
        "Different simplifications",
        "of the same original remain separate and share `canonical_original_id`. "
        "A partially retained",
        "pair survived Phase 2 in at least one, but not all, of its Phase 1 source occurrences.", "",
    ]
    md_path = reports_root / "consolidation_summary.md"
    md_tmp = md_path.with_suffix(".md.tmp")
    md_tmp.write_text("\n".join(lines), encoding="utf-8")
    os.replace(md_tmp, md_path)
    return rows


def consolidate(cleaned_root=DEFAULT_CLEANED, identity_path=DEFAULT_IDENTITY,
                output_root=DEFAULT_OUTPUT, reports_root=DEFAULT_REPORTS) -> dict:
    output_root = Path(output_root)
    reports_root = Path(reports_root)
    reports_root.mkdir(parents=True, exist_ok=True)
    database_path = reports_root / f".consolidation-build-{os.getpid()}.sqlite3"
    db = connection(database_path)
    try:
        identity_rows = load_identity(db, Path(identity_path))
        files, observations = load_cleaned(db, Path(cleaned_root))
        output_counts = write_data(db, output_root)
        summary = write_reports(db, reports_root, Path(cleaned_root))
    finally:
        db.close()
        database_path.unlink(missing_ok=True)
    if sum(output_counts.values()) != summary[0]["consolidated_pairs"]:
        raise RuntimeError("Consolidated output count does not match summary")
    return {
        "identity_rows": identity_rows, "cleaned_files": files,
        "cleaned_observations": observations,
        "consolidated_pairs": summary[0]["consolidated_pairs"],
        "output_files": len(output_counts), "output_root": str(output_root),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleaned-root", type=Path, default=DEFAULT_CLEANED)
    parser.add_argument("--identity", type=Path, default=DEFAULT_IDENTITY)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--reports-root", type=Path, default=DEFAULT_REPORTS)
    args = parser.parse_args()
    print(json.dumps(consolidate(args.cleaned_root, args.identity, args.output_root, args.reports_root), indent=2))


if __name__ == "__main__":
    main()
