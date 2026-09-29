import tempfile
import unittest
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import write_jsonl
from phase6_degraded_corpus.src.selection.freeze_evaluation_originals import strong_key
from phase6_degraded_corpus.src.selection.sample_mmi_devsets import sample_sets
from phase6_degraded_corpus.src.selection.select_mmi_pools import (
    ReservedMatcher,
    assert_materializable,
)


class ReservedMatcherTest(unittest.TestCase):
    def setUp(self):
        text = "The bridge was built later."
        self.matcher = ReservedMatcher(
            [{"strong_key": strong_key(text), "original": text}], threshold=0.8
        )

    def test_exact_match_ignores_tokenized_punctuation(self):
        result = self.matcher.match("The bridge was built later .")
        self.assertEqual(result["type"], "exact")

    def test_near_match_uses_word_jaccard(self):
        result = self.matcher.match("The old bridge was built later.")
        self.assertEqual(result["type"], "near")
        self.assertGreaterEqual(result["score"], 0.8)

    def test_materializer_rejects_reserved_row(self):
        with self.assertRaisesRegex(ValueError, "reserved evaluation"):
            assert_materializable({"usage": "reserved_evaluation"})


class SharedSplitTest(unittest.TestCase):
    def test_sampling_is_deterministic_and_disjoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for axis in ("MEANING", "MOD", "ILLOC"):
                for corpus in ("WikiAutoEN", "ASSET", "Wikipedia-Vikidia"):
                    rows = []
                    for index in range(7):
                        rows.append(
                            {
                                "canonical_pair_id": f"{axis}:{corpus}:{index}",
                                "canonical_original_id": f"{axis}:{corpus}:original:{index}",
                                "target_axis": axis,
                                "corpus": corpus,
                                "source_strategy_count": index % 2,
                                "selection_features": {"cue_types": ["number"]},
                            }
                        )
                    filename = f"{axis.lower()}_{corpus.lower().replace('-', '_')}.jsonl"
                    write_jsonl(root / filename, rows)
            first, _ = sample_sets(root, seed=17, dev_size=4, heldout_size=2)
            second, _ = sample_sets(root, seed=17, dev_size=4, heldout_size=2)
            self.assertEqual(first, second)
            dev_ids = {row["canonical_original_id"] for row in first["dev"]}
            heldout_ids = {row["canonical_original_id"] for row in first["heldout"]}
            self.assertTrue(dev_ids.isdisjoint(heldout_ids))


if __name__ == "__main__":
    unittest.main()
