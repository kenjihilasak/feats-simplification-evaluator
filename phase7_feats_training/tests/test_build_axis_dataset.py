import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from build_axis_dataset import leakage_audit


class LeakageTests(unittest.TestCase):
    def test_exact_and_near_duplicates_fail(self):
        training = [{"canonical_original_id": "one", "original": "Alpha, beta gamma."},
                    {"canonical_original_id": "two", "original": "red blue green yellow"}]
        evaluations = {"test": [{"original": "ALPHA beta gamma!"},
                                  {"original": "red blue green yellow black"}]}
        report = leakage_audit(training, evaluations, 0.8)
        self.assertFalse(report["passed"])
        self.assertEqual(len(report["exact_hits"]), 1)
        self.assertEqual(len(report["near_duplicate_hits"]), 1)


if __name__ == "__main__":
    unittest.main()
