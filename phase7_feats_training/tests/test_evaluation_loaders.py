import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from evaluation_loaders import load_heldout_review, load_human_likert


class LoaderTests(unittest.TestCase):
    def test_likert_aggregates_by_sentence_system_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ratings.csv"
            fields = ["source", "simplification", "sentence_id", "simplification_type",
                      "system_name", "aspect", "worker_id", "rating", "references"]
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for worker, score in (("a", 20), ("b", 40)):
                    writer.writerow({"source": "Original", "simplification": "Simple", "sentence_id": "1",
                                     "simplification_type": "system", "system_name": "sys", "aspect": "meaning",
                                     "worker_id": worker, "rating": score, "references": "[]"})
            rows = load_human_likert(path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["human_score"], 30)
            self.assertEqual(rows[0]["rating_count"], 2)

    def test_review_key_join_and_unsure_inclusion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            review = root / "review.md"
            review.write_text("""### Case H001
* **Axis:** `MOD` — change
* **Source:** ASSET
* **Original:** Original.
* **Simplified:** Clean.
* **Degraded:** Maybe.
* [ ] Valid
* [ ] Invalid
* [x] Unsure
""", encoding="utf-8")
            key = root / "key.json"
            key.write_text(json.dumps({"H001": {"axis": "MOD", "corpus": "ASSET",
                "canonical_original_id": "o", "canonical_pair_id": "p", "operation": "hedge"}}))
            rows = load_heldout_review(review, key)
            self.assertTrue(rows[0]["included"])


if __name__ == "__main__":
    unittest.main()
