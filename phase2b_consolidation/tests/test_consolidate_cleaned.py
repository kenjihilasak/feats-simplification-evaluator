import json
from pathlib import Path
import sys

PHASE1_SRC = Path(__file__).resolve().parents[2] / "phase1_normalization" / "src"
PHASE2B_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(PHASE1_SRC))
sys.path.insert(0, str(PHASE2B_SRC))

from build_deduplication_registry import build_registry
from consolidate_cleaned import consolidate
from validate_consolidation import validate


def row(pair_id, original_id, source, corpus, simple):
    return {
        "id": pair_id, "original_id": original_id, "language": "en",
        "source": source, "corpus": corpus, "upstream_split": "train",
        "original": "A long sentence.", "simple": simple, "reference_index": 0,
        "source_dataset": source, "source_revision": "abc", "source_row": 0,
    }


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(item) + "\n" for item in rows), encoding="utf-8")


def test_consolidation_deduplicates_pairs_and_preserves_references(tmp_path):
    first = row("a1", "oa", "A", "One", "A short sentence.")
    duplicate = row("b1", "ob", "B", "Two", "A short sentence.")
    alternative = row("a2", "oa", "A", "One", "Another sentence.")
    removed_duplicate = row("c1", "oc", "C", "Three", "Another sentence.")

    phase1 = tmp_path / "phase1"
    write(phase1 / "en/a__One.jsonl", [first, alternative])
    write(phase1 / "en/b__Two.jsonl", [duplicate])
    write(phase1 / "en/c__Three.jsonl", [removed_duplicate])
    deduplication = tmp_path / "deduplication"
    build_registry(phase1, deduplication)

    cleaned = tmp_path / "cleaned"
    write(cleaned / "en/a__One.jsonl", [first, alternative])
    write(cleaned / "en/b__Two.jsonl", [duplicate])
    output = tmp_path / "output"
    reports = tmp_path / "reports"
    result = consolidate(cleaned, deduplication / "pair_identity.parquet", output, reports)

    assert result["cleaned_observations"] == 3
    assert result["consolidated_pairs"] == 2
    records = [json.loads(line) for line in (output / "en/feats_consolidated.jsonl").read_text().splitlines()]
    assert len(records) == 2
    assert len({record["canonical_original_id"] for record in records}) == 1
    exact = next(record for record in records if record["simple"] == "A short sentence.")
    assert exact["phase2_retained_occurrence_count"] == 2
    assert {item["source"] for item in exact["provenance"]} == {"A", "B"}
    partial = next(record for record in records if record["simple"] == "Another sentence.")
    assert partial["phase1_occurrence_count"] == 2
    assert partial["phase2_retained_occurrence_count"] == 1
    assert partial["partially_retained"] is True

    validation = validate(
        cleaned,
        deduplication / "pair_identity.parquet",
        output,
        reports / "consolidation_summary.csv",
    )
    assert validation["valid"] is True
    assert validation["cleaned_observations"] == 3
    assert validation["consolidated_pairs"] == 2
