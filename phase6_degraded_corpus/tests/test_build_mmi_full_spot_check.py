import unittest

from phase6_degraded_corpus.src.reporting.build_mmi_full_spot_check import build


def row(index, axis="ILLOC", source="WikiAutoEN", operation="assertion_to_hedged", valid=True):
    return {
        "canonical_pair_id": f"p{index}", "canonical_original_id": f"o{index}",
        "target_axis": axis, "corpus": source, "operation": operation,
        "yield": valid, "selected_index": 0 if valid else None,
        "candidates": [{"degraded": f"text {index}"}],
    }


class FullSpotCheckTest(unittest.TestCase):
    def test_cell_quota_and_extra_hedged_are_unique(self):
        rows = [row(i) for i in range(80)] + [row(100 + i, axis="MEANING", operation="meaning_entity") for i in range(30)]
        cases, report = build(rows, 20, 40, 3)
        self.assertEqual(report["previous_base_cases_not_reaudited"], 40)
        self.assertEqual(report["extra_hedged_cases"], 40)
        self.assertEqual(len(cases), 40)
        self.assertEqual(len({item["canonical_pair_id"] for item in cases}), 40)
        self.assertTrue(all(item["operation"] == "assertion_to_hedged" for item in cases))


if __name__ == "__main__":
    unittest.main()
