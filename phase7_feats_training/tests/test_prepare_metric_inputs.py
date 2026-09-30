import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from prepare_metric_inputs import adapt_rows


class MetricAdapterTests(unittest.TestCase):
    def test_three_items_per_set_are_reference_free(self):
        for dataset in ("simplicity_da", "human_likert", "simpeval_2022"):
            rows = [{"evaluation_id": f"{dataset}:{i}", "dataset": dataset,
                     "original": f"source {i}", "candidate": f"output {i}",
                     "references": ["must", "not", "leak"]} for i in range(3)]
            adapted = adapt_rows(rows)
            self.assertEqual(len(adapted), 3)
            for index, row in enumerate(adapted):
                self.assertEqual(row["original"], f"source {index}")
                self.assertEqual(row["simple"], f"output {index}")
                self.assertNotIn("references", row)


if __name__ == "__main__":
    unittest.main()
