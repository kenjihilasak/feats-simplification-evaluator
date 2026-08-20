import json
from pathlib import Path
import sys


PHASE2B_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(PHASE2B_SRC))

from build_cross_corpus_groups import build_groups


def pair(pair_id, original_id, simple, corpora, original="A long sentence."):
    sources = sorted({source for source, _ in corpora})
    return {
        "id": pair_id,
        "original_id": original_id,
        "canonical_original_id": original_id,
        "canonical_pair_id": pair_id,
        "language": "en",
        "original": original,
        "simple": simple,
        "phase1_occurrence_count": 1,
        "phase2_retained_occurrence_count": 1,
        "partially_retained": False,
        "sources": sources,
        "corpora": [
            {"source": source, "corpus": corpus}
            for source, corpus in corpora
        ],
        "upstream_splits": ["train"],
        "provenance": [
            {"id": f"upstream-{pair_id}-{index}", "source": source, "corpus": corpus}
            for index, (source, corpus) in enumerate(corpora)
        ],
    }


def write(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


def test_builds_only_post_clean_cross_corpus_multi_simplification_groups(tmp_path):
    eligible_original = "original:en:eligible"
    same_corpus_original = "original:en:same-corpus"
    exact_only_original = "original:en:exact-only"
    records = [
        pair(
            "pair:en:1", eligible_original, "Short one.", [("A", "Alpha")],
            original="A long sentence about Santo Anta\u0303o.",
        ),
        pair(
            "pair:en:2", eligible_original, "Short two.", [("B", "Beta")],
            original="A  long sentence about Santo Antão.",
        ),
        pair("pair:en:3", same_corpus_original, "Alternative one.", [("A", "Alpha")]),
        pair("pair:en:4", same_corpus_original, "Alternative two.", [("A", "Alpha")]),
        pair(
            "pair:en:5",
            exact_only_original,
            "Only one simplification.",
            [("A", "Alpha"), ("B", "Beta")],
        ),
    ]
    input_root = tmp_path / "data"
    write(input_root / "en" / "feats_consolidated.jsonl", records)
    output = tmp_path / "groups" / "cross_corpus_multi_simplifications.jsonl"
    summary = tmp_path / "groups" / "summary.md"

    result = build_groups(input_root, output, summary, tmp_path)

    assert result["input_pairs"] == 5
    assert result["groups"] == 1
    group = json.loads(output.read_text(encoding="utf-8").strip())
    assert group["group_id"] == eligible_original
    assert group["original"] == "A long sentence about Santo Antão."
    assert group["distinct_simplification_count"] == 2
    assert group["corpus_count"] == 2
    assert [item["simple"] for item in group["simplifications"]] == [
        "Short one.",
        "Short two.",
    ]
    assert "post-cleaning Phase 2b data" in summary.read_text(encoding="utf-8")
