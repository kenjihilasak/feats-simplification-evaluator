import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "phase6_degraded_corpus" / "src"))

from consolidate_generations import consolidate


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


class ConsolidationTests(unittest.TestCase):
    def test_restores_manifest_order_and_records_hashes(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            first, second = tmp / "a.jsonl", tmp / "b.jsonl"
            write_jsonl(first, [{"canonical_pair_id": "pair:2"}])
            write_jsonl(second, [{"canonical_pair_id": "pair:1"}])
            rows, report = consolidate(
                [{"canonical_pair_id": "pair:1"}, {"canonical_pair_id": "pair:2"}],
                [first, second],
            )
            self.assertEqual([row["canonical_pair_id"] for row in rows], ["pair:1", "pair:2"])
            self.assertTrue(all(len(row["sha256"]) == 64 for row in report["shards"]))

    def test_rejects_duplicates_and_incomplete_shards(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            first, second = tmp / "a.jsonl", tmp / "b.jsonl"
            write_jsonl(first, [{"canonical_pair_id": "pair:1"}])
            write_jsonl(second, [{"canonical_pair_id": "pair:1"}])
            with self.assertRaisesRegex(ValueError, "duplicate prediction"):
                consolidate([{"canonical_pair_id": "pair:1"}], [first, second])
            write_jsonl(second, [])
            with self.assertRaisesRegex(ValueError, "incomplete shards"):
                consolidate(
                    [{"canonical_pair_id": "pair:1"}, {"canonical_pair_id": "pair:2"}],
                    [first, second],
                )


if __name__ == "__main__":
    unittest.main()
