import csv
import json
from pathlib import Path
import sys

import pyarrow.parquet as pq

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from build_deduplication_registry import build_registry, canonical_ids, normalize_text


def write(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")


def record(pair_id, original_id, source, corpus, original, simple, reference=0):
    return {
        "id": pair_id, "original_id": original_id, "language": "en",
        "source": source, "corpus": corpus, "upstream_split": "train",
        "original": original, "simple": simple, "reference_index": reference,
    }


def test_normalization_is_conservative():
    assert normalize_text("  Cafe\u0301\n test ") == "Café test"
    assert canonical_ids("en", " A  sentence ", "Short") == canonical_ids(
        "en", "A sentence", "Short"
    )
    assert canonical_ids("en", "A sentence", "Short") != canonical_ids(
        "en", "a sentence", "Short"
    )


def test_registry_tracks_duplicates_and_multiple_simplifications(tmp_path):
    data = tmp_path / "data"
    write(data / "en/a__One.jsonl", [
        record("a1", "oa", "A", "One", "A  long sentence.", "A short sentence."),
        record("a2", "oa", "A", "One", "A long sentence.", "Another sentence.", 1),
    ])
    write(data / "en/b__Two.jsonl", [
        record("b1", "ob", "B", "Two", " A long sentence. ", "A short sentence."),
    ])
    output = tmp_path / "deduplication"
    result = build_registry(data, output)

    assert result["observations"] == 3
    assert result["unique_originals"] == 1
    assert result["unique_pairs"] == 2
    table = pq.read_table(output / "pair_identity.parquet").to_pylist()
    assert len(table) == 3
    assert len({row["canonical_original_id"] for row in table}) == 1
    assert sorted(row["pair_occurrence_count"] for row in table) == [1, 2, 2]
    assert all(row["has_multiple_simplifications"] for row in table)

    groups = [json.loads(line) for line in (output / "duplicate_groups.jsonl").read_text().splitlines()]
    assert len(groups) == 1
    assert groups[0]["group_type"] == "mixed"
    assert groups[0]["distinct_pair_count"] == 2
    assert {pair["occurrence_count"] for pair in groups[0]["pairs"]} == {1, 2}

    rows = list(csv.DictReader((output / "deduplication_summary.csv").open()))
    global_row = rows[0]
    assert global_row["redundant_pair_observations"] == "1"
    assert global_row["cross_source_pair_groups"] == "1"
