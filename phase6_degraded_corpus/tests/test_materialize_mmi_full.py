import json
import unittest

from phase6_degraded_corpus.src.evaluation.materialize_mmi_full import materialize


def planned(pair, original, operation="meaning_entity"):
    return {
        "canonical_pair_id": pair, "canonical_original_id": original, "plan_status": "ready",
        "usage": "pipeline_selection", "original": "Original.", "clean_simplification": "Simple.",
        "target_axis": "ILLOC" if operation.startswith("assertion") else "MEANING",
        "operation": operation, "corpus": "WikiAutoEN", "source": "test",
        "gemma_strategy_count": 1, "phase3a_predicted_codes": {"gemma": ["SYN"]},
        "strict_single_strategy_candidate": True,
    }


def scored(pair):
    return {
        "canonical_pair_id": pair, "selected_index": 0, "config_id": "C1", "model": "model",
        "model_revision": "revision", "prompt_id": "prompt", "prompt_sha256": "hash",
        "candidates": [{"valid": True, "degraded": "Degraded.", "checks": {"ok": True}}],
    }


class MaterializeMmiFullTest(unittest.TestCase):
    def test_two_rows_per_pair_and_hedged_withheld(self):
        plan = [planned("p1", "o1"), planned("p2", "o2", "assertion_to_hedged")]
        instances, withheld, report = materialize(plan, [scored("p1"), scored("p2")], set(), 3)
        self.assertEqual(len(instances), 2)
        self.assertEqual({row["variant"] for row in instances}, {"simplified", "degraded"})
        self.assertEqual(len(withheld), 1)
        self.assertEqual(report["withheld_hedged_pairs"], 1)
        self.assertTrue(instances[0]["strict_single_strategy_candidate"])

    def test_audited_original_is_dropped_and_counted(self):
        instances, _, report = materialize([planned("p1", "o1"), planned("p2", "o2")], [scored("p1"), scored("p2")], {"o1"}, 3)
        self.assertEqual({row["canonical_original_id"] for row in instances}, {"o2"})
        self.assertIn("excluded_audited_original", json.dumps(report))

    def test_hedged_can_be_included_after_gate(self):
        plan = [planned("p2", "o2", "assertion_to_hedged")]
        instances, withheld, report = materialize(plan, [scored("p2")], set(), 3, include_hedged=True)
        self.assertEqual(len(instances), 2)
        self.assertFalse(withheld)
        self.assertEqual(report["hedged_policy"], "included_after_human_gate")


if __name__ == "__main__":
    unittest.main()
