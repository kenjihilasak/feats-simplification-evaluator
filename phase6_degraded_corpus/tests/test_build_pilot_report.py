import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phase6_degraded_corpus.src.reporting.build_pilot_report import combine, render


class CombinedPilotReportTests(unittest.TestCase):
    def test_combines_meaning_and_other_axis(self):
        meaning = [{
            "canonical_pair_id": "p1", "canonical_original_id": "o1",
            "predicted_strategy": "OMIT", "assigned_corruption": "number_replacement",
            "original": "Original 1.", "clean_simplification": "Simplified 1.",
            "generation": {"distorted_simplification": "Degraded 1.", "brief_verification": "changed"},
            "accepted_source": "qwen_v1",
        }]
        multi = [{
            "canonical_pair_id": "p2", "canonical_original_id": "o2", "target_axis": "FLUENCY",
            "source_strategy": "SYN", "assigned_operation": "agreement_error",
            "original": "Original 2.", "clean_simplification": "Simplified 2.",
            "generation": {"degraded_simplification": "Degraded 2.", "brief_verification": "changed"},
            "status": "generated_pending_audit", "automatic_checks": {},
        }]
        rows = combine(meaning, multi)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["quality"], "accepted")
        report = render(rows)
        self.assertIn("all seven Phase 6 pilots", report)
        self.assertIn("- Simplified: Simplified 1.", report)

    def test_duplicate_pair_axis_fails(self):
        meaning = [{
            "canonical_pair_id": "p1", "canonical_original_id": "o1",
            "predicted_strategy": "SYN", "assigned_corruption": "event_replacement",
            "original": "O", "clean_simplification": "S",
            "generation": {"distorted_simplification": "D"},
        }]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            combine([meaning[0], meaning[0]], [])


if __name__ == "__main__":
    unittest.main()
