#!/usr/bin/env python3
"""Build exact-text identities for all normalized Phase 1 observations."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import unicodedata
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from common import DATA_ROOT, PROJECT_ROOT, iter_jsonl


DEFAULT_OUTPUT = PROJECT_ROOT / "phase1_normalization" / "deduplication"
CANONICALIZATION_VERSION = "feats-text-identity-v1"
SPACE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    """Apply conservative normalization without changing lexical content."""
    if not isinstance(value, str):
        raise TypeError("Identity fields must be strings")
    return SPACE.sub(" ", unicodedata.normalize("NFC", value)).strip()


def canonical_ids(language: str, original: str, simple: str) -> tuple[str, str]:
    original_key = normalize_text(original)
    simple_key = normalize_text(simple)
    original_hash = hashlib.sha256(
        f"{language}\0{original_key}".encode("utf-8")
    ).hexdigest()
    pair_hash = hashlib.sha256(
        f"{language}\0{original_key}\0{simple_key}".encode("utf-8")
    ).hexdigest()
    return f"original:{language}:{original_hash}", f"pair:{language}:{pair_hash}"


def database(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=OFF")
    connection.execute("PRAGMA synchronous=OFF")
    connection.execute("PRAGMA temp_store=FILE")
    connection.execute(
        """
        CREATE TABLE observations (
            id TEXT PRIMARY KEY,
            original_id TEXT NOT NULL,
            canonical_original_id TEXT NOT NULL,
            canonical_pair_id TEXT NOT NULL,
            language TEXT NOT NULL,
            source TEXT NOT NULL,
            corpus TEXT NOT NULL,
            upstream_split TEXT,
            reference_index INTEGER NOT NULL,
            source_file TEXT NOT NULL,
            original TEXT NOT NULL,
            simple TEXT NOT NULL
        )
        """
    )
    return connection


def ingest(connection: sqlite3.Connection, data_root: Path) -> tuple[int, int]:
    files = sorted(data_root.glob("*/*.jsonl"))
    if not files:
        raise FileNotFoundError(f"No JSONL files under {data_root}/<language>/")
    total = 0
    for path in files:
        language = path.parent.name
        source_file = str(path.relative_to(data_root))
        rows = []
        for record in iter_jsonl(path):
            if record.get("language") != language:
                raise ValueError(f"Language/path mismatch in {source_file}: {record.get('id')}")
            canonical_original_id, canonical_pair_id = canonical_ids(
                language, record["original"], record["simple"]
            )
            rows.append(
                (
                    record["id"], record["original_id"], canonical_original_id,
                    canonical_pair_id, language, record["source"], record["corpus"],
                    record.get("upstream_split"), int(record["reference_index"]),
                    source_file, record["original"], record["simple"],
                )
            )
            if len(rows) == 10_000:
                connection.executemany("INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
                total += len(rows)
                rows.clear()
        if rows:
            connection.executemany("INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
            total += len(rows)
        connection.commit()

    connection.executescript(
        """
        CREATE INDEX observations_pair ON observations(canonical_pair_id);
        CREATE INDEX observations_original ON observations(canonical_original_id);
        CREATE INDEX observations_scope ON observations(language, source, corpus);

        CREATE TABLE pair_stats AS
        SELECT canonical_pair_id, canonical_original_id, MIN(language) AS language,
               COUNT(*) AS occurrence_count,
               COUNT(DISTINCT source) AS source_count,
               COUNT(DISTINCT source || char(31) || corpus) AS corpus_count
        FROM observations GROUP BY canonical_pair_id;
        CREATE UNIQUE INDEX pair_stats_id ON pair_stats(canonical_pair_id);
        CREATE INDEX pair_stats_original ON pair_stats(canonical_original_id);

        CREATE TABLE original_stats AS
        SELECT canonical_original_id, MIN(language) AS language,
               COUNT(*) AS occurrence_count,
               COUNT(DISTINCT canonical_pair_id) AS distinct_pair_count,
               COUNT(DISTINCT source) AS source_count,
               COUNT(DISTINCT source || char(31) || corpus) AS corpus_count
        FROM observations GROUP BY canonical_original_id;
        CREATE UNIQUE INDEX original_stats_id ON original_stats(canonical_original_id);
        """
    )
    connection.commit()
    return len(files), total


PARQUET_SCHEMA = pa.schema(
    [
        ("id", pa.string()), ("original_id", pa.string()),
        ("canonical_original_id", pa.string()), ("canonical_pair_id", pa.string()),
        ("language", pa.string()), ("source", pa.string()), ("corpus", pa.string()),
        ("upstream_split", pa.string()), ("reference_index", pa.int64()),
        ("source_file", pa.string()), ("pair_occurrence_count", pa.int64()),
        ("original_occurrence_count", pa.int64()),
        ("original_distinct_pair_count", pa.int64()),
        ("is_exact_pair_duplicate", pa.bool_()),
        ("has_multiple_simplifications", pa.bool_()),
    ],
    metadata={b"canonicalization_version": CANONICALIZATION_VERSION.encode()},
)


def write_identity_parquet(connection: sqlite3.Connection, path: Path) -> int:
    query = """
        SELECT o.id, o.original_id, o.canonical_original_id, o.canonical_pair_id,
               o.language, o.source, o.corpus, o.upstream_split, o.reference_index,
               o.source_file, p.occurrence_count, s.occurrence_count,
               s.distinct_pair_count, p.occurrence_count > 1,
               s.distinct_pair_count > 1
        FROM observations o
        JOIN pair_stats p USING (canonical_pair_id)
        JOIN original_stats s USING (canonical_original_id)
        ORDER BY o.language, o.source, o.corpus, o.source_file, o.id
    """
    temporary = path.with_suffix(path.suffix + ".tmp")
    writer = pq.ParquetWriter(temporary, PARQUET_SCHEMA, compression="zstd")
    count = 0
    try:
        cursor = connection.execute(query)
        while rows := cursor.fetchmany(25_000):
            columns = list(zip(*rows))
            arrays = []
            for column, field in zip(columns, PARQUET_SCHEMA):
                values = [bool(value) for value in column] if pa.types.is_boolean(field.type) else column
                arrays.append(pa.array(values, type=field.type))
            table = pa.Table.from_arrays(
                arrays, schema=PARQUET_SCHEMA,
            )
            writer.write_table(table)
            count += len(rows)
    finally:
        writer.close()
    os.replace(temporary, path)
    return count


def group_type(distinct_pairs: int, duplicate_pair_groups: int) -> str:
    if distinct_pairs > 1 and duplicate_pair_groups:
        return "mixed"
    if distinct_pairs > 1:
        return "multiple_simplifications"
    return "exact_pair_duplicates"


def write_duplicate_groups(connection: sqlite3.Connection, path: Path) -> int:
    query = """
        SELECT o.canonical_original_id, o.canonical_pair_id, o.id, o.original_id,
               o.language, o.source, o.corpus, o.upstream_split, o.reference_index,
               o.source_file, o.original, o.simple, p.occurrence_count,
               s.occurrence_count, s.distinct_pair_count,
               (SELECT COUNT(*) FROM pair_stats d
                WHERE d.canonical_original_id=o.canonical_original_id
                  AND d.occurrence_count > 1) AS duplicate_pair_groups
        FROM observations o
        JOIN pair_stats p USING (canonical_pair_id)
        JOIN original_stats s USING (canonical_original_id)
        WHERE s.occurrence_count > 1
        ORDER BY o.canonical_original_id, o.canonical_pair_id, o.id
    """
    temporary = path.with_suffix(path.suffix + ".tmp")
    written = 0

    def emit(handle, rows: list[tuple]) -> None:
        nonlocal written
        first = rows[0]
        pairs = []
        for pair_id in dict.fromkeys(row[1] for row in rows):
            members = [row for row in rows if row[1] == pair_id]
            pairs.append(
                {
                    "canonical_pair_id": pair_id,
                    "simple": normalize_text(members[0][11]),
                    "occurrence_count": members[0][12],
                    "occurrences": [
                        {
                            "id": row[2], "original_id": row[3], "source": row[5],
                            "corpus": row[6], "upstream_split": row[7],
                            "reference_index": row[8], "source_file": row[9],
                        }
                        for row in members
                    ],
                }
            )
        value = {
            "canonical_original_id": first[0], "language": first[4],
            "original": normalize_text(first[10]), "group_type": group_type(first[14], first[15]),
            "occurrence_count": first[13], "distinct_pair_count": first[14],
            "duplicate_pair_group_count": first[15], "pairs": pairs,
        }
        handle.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")
        written += 1

    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        current_id = None
        group = []
        for row in connection.execute(query):
            if current_id is not None and row[0] != current_id:
                emit(handle, group)
                group = []
            current_id = row[0]
            group.append(row)
        if group:
            emit(handle, group)
    os.replace(temporary, path)
    return written


SUMMARY_FIELDS = [
    "scope", "language", "source", "corpus", "observations", "unique_originals",
    "unique_pairs", "redundant_pair_observations", "redundant_pair_pct",
    "exact_duplicate_pair_groups", "multiple_simplification_original_groups",
    "cross_source_pair_groups", "cross_corpus_pair_groups",
]


def summary_row(connection, scope, where="", parameters=(), **labels):
    clause = f" WHERE {where}" if where else ""
    observations, originals, pairs = connection.execute(
        f"SELECT COUNT(*), COUNT(DISTINCT canonical_original_id), "
        f"COUNT(DISTINCT canonical_pair_id) FROM observations{clause}", parameters
    ).fetchone()
    duplicate_groups = connection.execute(
        f"SELECT COUNT(*) FROM (SELECT canonical_pair_id FROM observations{clause} "
        "GROUP BY canonical_pair_id HAVING COUNT(*) > 1)", parameters
    ).fetchone()[0]
    multi_originals = connection.execute(
        f"SELECT COUNT(*) FROM (SELECT canonical_original_id FROM observations{clause} "
        "GROUP BY canonical_original_id HAVING COUNT(DISTINCT canonical_pair_id) > 1)", parameters
    ).fetchone()[0]
    cross_source, cross_corpus = connection.execute(
        f"SELECT COALESCE(SUM(source_count > 1),0), COALESCE(SUM(corpus_count > 1),0) FROM ("
        f"SELECT COUNT(DISTINCT source) source_count, "
        f"COUNT(DISTINCT source || char(31) || corpus) corpus_count "
        f"FROM observations{clause} GROUP BY canonical_pair_id)", parameters
    ).fetchone()
    redundant = observations - pairs
    return {
        "scope": scope, "language": labels.get("language", ""),
        "source": labels.get("source", ""), "corpus": labels.get("corpus", ""),
        "observations": observations, "unique_originals": originals, "unique_pairs": pairs,
        "redundant_pair_observations": redundant,
        "redundant_pair_pct": round(redundant / observations * 100, 6) if observations else 0.0,
        "exact_duplicate_pair_groups": duplicate_groups,
        "multiple_simplification_original_groups": multi_originals,
        "cross_source_pair_groups": cross_source, "cross_corpus_pair_groups": cross_corpus,
    }


def build_summary(connection: sqlite3.Connection) -> list[dict]:
    rows = [summary_row(connection, "global")]
    for (language,) in connection.execute("SELECT DISTINCT language FROM observations ORDER BY language"):
        rows.append(summary_row(connection, "language", "language=?", (language,), language=language))
    for language, source, corpus in connection.execute(
        "SELECT DISTINCT language, source, corpus FROM observations ORDER BY language, source, corpus"
    ):
        rows.append(summary_row(
            connection, "corpus", "language=? AND source=? AND corpus=?",
            (language, source, corpus), language=language, source=source, corpus=corpus,
        ))
    return rows


def write_summary(rows: list[dict], csv_path: Path, md_path: Path) -> None:
    csv_tmp = csv_path.with_suffix(".csv.tmp")
    with csv_tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=SUMMARY_FIELDS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    os.replace(csv_tmp, csv_path)

    global_row = rows[0]
    language_rows = [row for row in rows if row["scope"] == "language"]
    lines = [
        "# Phase 1 deduplication summary", "",
        f"Canonicalization: `{CANONICALIZATION_VERSION}` "
        "(Unicode NFC, collapsed whitespace, and trimming).",
        "Case, punctuation, and lexical content are preserved.", "",
        "| Measure | Count |", "|---|---:|",
        f"| Source observations | {global_row['observations']:,} |",
        f"| Unique original texts | {global_row['unique_originals']:,} |",
        f"| Unique original–simplification pairs | {global_row['unique_pairs']:,} |",
        f"| Redundant exact-pair observations | "
        f"{global_row['redundant_pair_observations']:,} "
        f"({global_row['redundant_pair_pct']:.2f}%) |",
        f"| Exact duplicate pair groups | {global_row['exact_duplicate_pair_groups']:,} |",
        f"| Originals with multiple simplifications | {global_row['multiple_simplification_original_groups']:,} |",
        f"| Exact pair groups spanning sources | {global_row['cross_source_pair_groups']:,} |",
        f"| Exact pair groups spanning corpora | {global_row['cross_corpus_pair_groups']:,} |",
        "", "## By language", "",
        "| Language | Observations | Unique pairs | Redundant observations | "
        "Redundant % | Multi-simplification originals |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in language_rows:
        lines.append(
            f"| {row['language']} | {row['observations']:,} | {row['unique_pairs']:,} | "
            f"{row['redundant_pair_observations']:,} | {row['redundant_pair_pct']:.2f}% | "
            f"{row['multiple_simplification_original_groups']:,} |"
        )
    lines += [
        "", "`pair_identity.parquet` maps every Phase 1 observation to canonical IDs.",
        "`duplicate_groups.jsonl` contains only originals occurring more than "
        "once and lists all source occurrences.", "",
    ]
    md_tmp = md_path.with_suffix(".md.tmp")
    md_tmp.write_text("\n".join(lines), encoding="utf-8")
    os.replace(md_tmp, md_path)


def build_registry(data_root: Path = DATA_ROOT, output_root: Path = DEFAULT_OUTPUT) -> dict:
    output_root.mkdir(parents=True, exist_ok=True)
    database_path = output_root / f".deduplication-build-{os.getpid()}.sqlite3"
    connection = database(database_path)
    try:
        files, observations = ingest(connection, data_root)
        parquet_rows = write_identity_parquet(connection, output_root / "pair_identity.parquet")
        duplicate_groups = write_duplicate_groups(connection, output_root / "duplicate_groups.jsonl")
        rows = build_summary(connection)
        write_summary(
            rows, output_root / "deduplication_summary.csv",
            output_root / "deduplication_summary.md",
        )
    finally:
        connection.close()
        database_path.unlink(missing_ok=True)
    if parquet_rows != observations:
        raise RuntimeError(f"Parquet row count {parquet_rows} != observations {observations}")
    return {
        "files": files, "observations": observations,
        "unique_originals": rows[0]["unique_originals"], "unique_pairs": rows[0]["unique_pairs"],
        "duplicate_groups": duplicate_groups, "output_root": str(output_root),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(build_registry(args.data_root, args.output_root), indent=2))


if __name__ == "__main__":
    main()
