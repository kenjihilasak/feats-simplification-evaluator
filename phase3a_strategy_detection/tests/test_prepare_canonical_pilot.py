import json
from pathlib import Path
import sys


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from prepare_canonical_pilot import prepare


def record(index, corpora):
    pair_id = f"pair:en:{index}"
    return {
        "id": pair_id,
        "canonical_pair_id": pair_id,
        "canonical_original_id": f"original:en:{index}",
        "language": "en",
        "original": f"Original sentence {index}.",
        "simple": f"Simple sentence {index}.",
        "corpora": [
            {"source": source, "corpus": corpus}
            for source, corpus in corpora
        ],
        "provenance": [],
    }


def test_pilot_stratifies_by_corpus_and_emits_each_canonical_pair_once(tmp_path):
    source = tmp_path / "phase2b" / "en" / "feats_consolidated.jsonl"
    source.parent.mkdir(parents=True)
    rows = [
        record(1, [("A", "Alpha")]),
        record(2, [("B", "Beta")]),
        record(3, [("A", "Alpha"), ("B", "Beta")]),
    ]
    source.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    output = tmp_path / "sample"

    summary = prepare(source.parents[1], output, 10, 1, 2026)

    emitted = [
        json.loads(line)
        for line in (output / "en" / "feats_consolidated.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert summary["source_pairs"] == 3
    assert summary["strata"] == 2
    assert summary["selected_canonical_pairs"] == 3
    assert len(emitted) == 3
    assert len({row["canonical_pair_id"] for row in emitted}) == 3
