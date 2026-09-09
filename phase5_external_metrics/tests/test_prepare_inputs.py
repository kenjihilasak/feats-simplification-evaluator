import json
import sys
from collections import Counter
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from prepare_inputs import build_pilot, build_smoke


def canonical_rows(count):
    return [{
        "id": f"pair:en:{index}", "canonical_pair_id": f"pair:en:{index}",
        "canonical_original_id": f"orig:{index}", "language": "en",
        "original": f"This is a sufficiently long original sentence number {index}.",
        "simple": f"This is simpler {index}.",
        "corpora": [{"source": "S", "corpus": f"C{index % 2}"}],
        "provenance": [{"id": f"occ:{index}"}],
    } for index in range(count)]


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def test_smoke_has_32_cases_and_required_categories(tmp_path):
    source, output = tmp_path / "source.jsonl", tmp_path / "smoke.jsonl"
    write_jsonl(source, canonical_rows(40))
    report = build_smoke(source, output)
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert report["pairs"] == 32
    assert Counter(row["smoke_case_type"] for row in rows) == {
        "valid_simplification": 7, "identity": 7, "strong_omission": 6,
        "contradiction": 6, "long_input": 6,
    }
    assert len({row["canonical_pair_id"] for row in rows}) == 32


def test_pilot_is_deterministic_and_preserves_strata(tmp_path):
    source = tmp_path / "source.jsonl"
    rows = canonical_rows(20)
    write_jsonl(source, rows)
    decisions = tmp_path / "decisions/en/test.jsonl"
    write_jsonl(decisions, [{"id": f"occ:{i}", "labse_similarity": .7 + (i % 3) * .1} for i in range(20)])
    strategies = tmp_path / "strategies.jsonl"
    write_jsonl(strategies, [{"canonical_pair_id": f"pair:en:{i}", "predicted_codes": ["SYN" if i % 2 else "OMIT"]} for i in range(20)])
    first, second = tmp_path / "pilot1.jsonl", tmp_path / "pilot2.jsonl"
    report = build_pilot(source, first, 12, 42, tmp_path / "decisions", strategies)
    build_pilot(source, second, 12, 42, tmp_path / "decisions", strategies)
    assert report["pairs"] == 12
    assert first.read_bytes() == second.read_bytes()
    assert all("pilot_stratum" in json.loads(line) for line in first.read_text().splitlines())

