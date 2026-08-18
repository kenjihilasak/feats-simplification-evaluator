import json
from pathlib import Path
import sys


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from prepare_pilot_sample import file_seed, select_records  # noqa: E402


def write_records(path, lengths):
    with path.open("w", encoding="utf-8") as handle:
        for index, length in enumerate(lengths):
            record = {
                "id": f"pair-{index}",
                "language": "en",
                "source": "test",
                "corpus": "test",
                "original": "a" * length,
                "simple": "b",
            }
            handle.write(json.dumps(record) + "\n")


def test_selection_is_deterministic_and_keeps_longest(tmp_path):
    source = tmp_path / "sample.jsonl"
    write_records(source, range(1, 21))

    first, total = select_records(source, random_count=5, longest_count=2, seed=7)
    second, _ = select_records(source, random_count=5, longest_count=2, seed=7)

    assert total == 20
    assert [(row[0], row[2]) for row in first] == [
        (row[0], row[2]) for row in second
    ]
    selected_ids = {row[1]["id"] for row in first}
    assert {"pair-18", "pair-19"} <= selected_ids
    assert len(selected_ids) <= 7


def test_file_seed_depends_on_path():
    assert file_seed(2026, "en/a.jsonl") == file_seed(2026, "en/a.jsonl")
    assert file_seed(2026, "en/a.jsonl") != file_seed(2026, "es/a.jsonl")
