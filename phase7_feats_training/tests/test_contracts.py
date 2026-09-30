import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from contracts import AxisExample, jaccard, strong_key


class ContractTests(unittest.TestCase):
    def test_strong_key_normalizes_case_punctuation_and_compatibility(self):
        self.assertEqual(strong_key("Café—Ａ!"), strong_key("café a"))

    def test_jaccard(self):
        self.assertEqual(jaccard("one two", "one two"), 1.0)
        self.assertAlmostEqual(jaccard("one two", "two three"), 1 / 3)

    def test_axis_example_rejects_unknown_axis(self):
        row = AxisExample("e", "p", "o", "en", "a", "b", None, "BAD", 1.0,
                          "binary_0_1", "synthetic", None, "train", {})
        with self.assertRaises(ValueError):
            row.to_dict()


if __name__ == "__main__":
    unittest.main()
