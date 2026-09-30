import unittest

from phase6_degraded_corpus.src.selection.allocate_mmi_full import allocate


def row(pair, original, source, axes):
    return {
        "canonical_pair_id": pair,
        "canonical_original_id": original,
        "corpus": source,
        "eligible_axes": axes,
    }


class AllocateMmiFullTest(unittest.TestCase):
    def test_deterministic_unique_and_audited_excluded(self):
        rows = [
            row("p1", "o1", "WikiAutoEN", ["MOD", "MEANING", "ILLOC"]),
            row("p2", "o2", "WikiAutoEN", ["MEANING", "ILLOC"]),
            row("p3", "o3", "WikiAutoEN", ["MEANING", "ILLOC"]),
            row("p4", "o4", "WikiAutoEN", ["MEANING"]),
            row("p5", "o5", "WikiAutoEN", ["ILLOC"]),
            row("p6", "audited", "WikiAutoEN", ["MEANING", "ILLOC"]),
        ]
        first, report = allocate(rows, {"audited"}, 7)
        second, _ = allocate(list(reversed(rows)), {"audited"}, 7)
        flatten = lambda value: sorted((r["canonical_pair_id"], r["target_axis"], r.get("operation")) for rs in value.values() for r in rs)
        self.assertEqual(flatten(first), flatten(second))
        assigned = [r for rs in first.values() for r in rs]
        self.assertEqual(len(assigned), 5)
        self.assertEqual(len({r["canonical_original_id"] for r in assigned}), 5)
        self.assertNotIn("audited", {r["canonical_original_id"] for r in assigned})
        self.assertEqual([r["canonical_pair_id"] for r in first[("MOD", "WikiAutoEN")]], ["p1"])
        self.assertEqual(report["excluded_audited_originals"], 1)

    def test_balances_axes_and_illoc_operations(self):
        rows = [row(f"p{i}", f"o{i}", "ASSET", ["MEANING", "ILLOC"]) for i in range(12)]
        allocation, _ = allocate(rows, set(), 11)
        self.assertEqual(len(allocation[("MEANING", "ASSET")]), 6)
        self.assertEqual(len(allocation[("ILLOC", "ASSET")]), 6)
        operations = [r["operation"] for r in allocation[("ILLOC", "ASSET")]]
        self.assertEqual(sorted(operations).count("assertion_to_question"), 2)
        self.assertEqual(sorted(operations).count("assertion_to_directive"), 2)
        self.assertEqual(sorted(operations).count("assertion_to_hedged"), 2)


if __name__ == "__main__":
    unittest.main()
