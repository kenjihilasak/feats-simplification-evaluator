import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phase6_degraded_corpus.src.evaluation.analyze_pilot_quality import analyze, classify, render_markdown


def row(pair_id, status, different=True, operation=True, generation=True):
    return {
        "canonical_pair_id": pair_id, "target_axis": "FLUENCY",
        "original": "Original.", "clean_simplification": "Simplified.",
        "status": status,
        "generation": {"degraded_simplification": "Degraded."} if generation else None,
        "automatic_checks": {
            "different_from_clean": different,
            "operation_matches_assignment": operation,
        },
    }


class PilotQualityTests(unittest.TestCase):
    def test_classification_boundaries(self):
        self.assertEqual(classify(row("p1", "generated_pending_audit"))[0], "good")
        self.assertEqual(classify(row("p2", "failed_validation"))[0], "medium")
        self.assertEqual(classify(row("p3", "failed_validation", different=False))[0], "failed")
        self.assertEqual(classify(row("p4", "failed_parse", generation=False))[0], "failed")
        format_only = row("p5", "generated_pending_audit")
        format_only["clean_simplification"] = "Sentence.One"
        format_only["generation"]["degraded_simplification"] = "Sentence. One"
        self.assertEqual(classify(format_only), ("failed", "no_substantive_change"))

    def test_summary_and_markdown(self):
        result = analyze([
            row("p1", "generated_pending_audit"),
            row("p2", "failed_validation"),
            row("p3", "failed_validation", different=False),
        ])
        self.assertEqual(result["by_axis"]["FLUENCY"]["good"], 1)
        self.assertEqual(result["by_axis"]["FLUENCY"]["medium"], 1)
        self.assertEqual(result["by_axis"]["FLUENCY"]["failed"], 1)
        text = render_markdown(result, examples_per_tier=1)
        self.assertIn("| FLUENCY | 1 | 1 | 1 | 33% |", text)
        self.assertIn("- Simplified: Simplified.", text)

    def test_duplicate_ids_fail(self):
        duplicate = row("p1", "generated_pending_audit")
        with self.assertRaisesRegex(ValueError, "duplicate canonical_pair_id"):
            analyze([duplicate, duplicate])


if __name__ == "__main__":
    unittest.main()
