import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phase6_degraded_corpus.src.planning.plan_meaning_corruptions import detect, plan


class MeaningCorruptionPlanTests(unittest.TestCase):
    def test_detector_finds_explicit_cues(self):
        found = detect(
            "In March 1999, Alice Smith built 12 small public schools in North Leeds."
        )
        self.assertTrue(found["date_replacement"])
        self.assertTrue(found["number_replacement"])
        self.assertTrue(found["entity_replacement"])
        self.assertTrue(found["property_replacement"])
        self.assertTrue(found["relation_reversal"])
        self.assertTrue(found["event_replacement"])
        self.assertFalse(detect("Someone may work in acoustics.")["date_replacement"])

    def test_assignment_is_deterministic_and_respects_applicability(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            input_path = tmp / "inputs.jsonl"
            rows = [
                {
                    "canonical_pair_id": f"pair:{i}",
                    "canonical_original_id": f"original:{i}",
                    "original": f"The event happened in 20{10 + i}.",
                    "clean_simplification": f"Alice Smith built {i + 2} small schools in 20{10 + i}.",
                    "clean_source_tier": "target_simple_candidate",
                    "clean_review_status": "pending",
                    "predicted_strategy": "SYN",
                }
                for i in range(8)
            ]
            input_path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
            )
            kinds = [
                "entity_replacement", "number_replacement", "date_replacement",
                "negation_reversal", "property_replacement", "relation_reversal",
                "event_replacement",
            ]
            config = {
                "seed": 17,
                "input_file": str(input_path),
                "target_axis": "meaning",
                "target_score": 0.0,
                "corruption_types": kinds,
                "target_counts": {kind: 1 for kind in kinds},
            }
            first, first_report = plan(config)
            second, second_report = plan(config)
            self.assertEqual(first, second)
            self.assertEqual(first_report, second_report)
            self.assertTrue(all(row["assigned_corruption"] in row["applicable_corruptions"] for row in first))
            self.assertTrue(all(row["generation_status"] == "blocked_clean_review" for row in first))


if __name__ == "__main__":
    unittest.main()
