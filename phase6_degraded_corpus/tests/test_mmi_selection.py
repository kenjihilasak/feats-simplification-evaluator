import tempfile
import unittest
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import write_jsonl
from phase6_degraded_corpus.src.selection.freeze_evaluation_originals import strong_key
from phase6_degraded_corpus.src.selection.sample_mmi_devsets import sample_sets
from phase6_degraded_corpus.src.selection.select_mmi_pools import (
    ReservedMatcher,
    allocate_candidates,
    allocate_source,
    assert_materializable,
)


def candidate(index, axes, corpus="WikiAutoEN"):
    return {
        "canonical_pair_id": f"pair:{index}",
        "canonical_original_id": f"original:{index}",
        "eligible_axes": list(axes),
        "selection_features_by_axis": {axis: {} for axis in axes},
        "corpus": corpus,
        "gemma_strategy_count": 1,
        "strict_single_strategy_candidate": True,
        "phase3a_predicted_codes": {"gemma": ["SYN"]},
    }


class ReservedMatcherTest(unittest.TestCase):
    def setUp(self):
        text = "The bridge was built later."
        self.matcher = ReservedMatcher(
            [{"strong_key": strong_key(text), "original": text}], threshold=0.8
        )

    def test_exact_match_ignores_tokenized_punctuation(self):
        self.assertEqual(self.matcher.match("The bridge was built later .")["type"], "exact")

    def test_near_match_uses_word_jaccard(self):
        result = self.matcher.match("The old bridge was built later.")
        self.assertEqual(result["type"], "near")
        self.assertGreaterEqual(result["score"], 0.8)

    def test_materializer_rejects_reserved_row(self):
        with self.assertRaisesRegex(ValueError, "reserved evaluation"):
            assert_materializable({"usage": "reserved_evaluation"})


class AllocationTest(unittest.TestCase):
    def test_scarce_cell_is_not_drained_by_large_cell(self):
        rows = [
            candidate("meaning-1", ["MEANING"]),
            candidate("meaning-2", ["MEANING"]),
            candidate("shared-1", ["MEANING", "ILLOC"]),
            candidate("shared-2", ["MEANING", "ILLOC"]),
        ]
        allocated, pass1 = allocate_source(rows, seed=4, quota=2)
        self.assertEqual(pass1["MEANING"], 2)
        self.assertEqual(pass1["ILLOC"], 2)
        self.assertEqual({row["allocation_pass"] for row in allocated["ILLOC"]}, {1})

    def test_quality_filters_precede_allocation_and_sampling(self):
        rows = [
            candidate("pass-1", ["MEANING"]),
            candidate("pass-2", ["MEANING"]),
            candidate("reject-cola", ["MEANING"]),
            candidate("reject-nli", ["MEANING"]),
        ]
        scores = {
            "pair:pass-1": {"acceptability": 0.9, "entailment": 0.9},
            "pair:pass-2": {"acceptability": 0.8, "entailment": 0.8},
            "pair:reject-cola": {"acceptability": 0.1, "entailment": 0.9},
            "pair:reject-nli": {"acceptability": 0.9, "entailment": 0.1},
        }
        config = {
            "tau_accept": 0.5,
            "nli_entailment_threshold": 0.5,
            "seed": 3,
            "split_quota": 2,
            "corpora": ["WikiAutoEN", "ASSET", "Wikipedia-Vikidia"],
            "phase3a_prediction_files": {"gemma": "unused"},
            "nli_model": "nli",
            "nli_revision": "nli-rev",
            "acceptability_model": "cola",
            "acceptability_revision": "cola-rev",
            "delta": 0.1,
        }
        pools, _ = allocate_candidates(
            rows,
            scores,
            config,
            {"schema": "test", "reserved": {}, "filters_before_quality": {}},
        )
        selected = {row["canonical_pair_id"] for row in pools[("MEANING", "WikiAutoEN")]}
        self.assertEqual(selected, {"pair:pass-1", "pair:pass-2"})

    def test_sampling_is_deterministic_and_disjoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for axis in ("MEANING", "MOD", "ILLOC"):
                for corpus in ("WikiAutoEN", "ASSET", "Wikipedia-Vikidia"):
                    rows = []
                    for index in range(7):
                        row = candidate(f"{axis}:{corpus}:{index}", [axis], corpus)
                        row.update(
                            {
                                "target_axis": axis,
                                "selection_features": {"cue_types": ["number"]},
                                "allocation_pass": 1,
                            }
                        )
                        rows.append(row)
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
