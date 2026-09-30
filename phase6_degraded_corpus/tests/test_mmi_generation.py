import unittest

from phase6_degraded_corpus.src.evaluation.analyze_mmi_comparison import mcnemar_exact, wilson
from phase6_degraded_corpus.src.evaluation.score_mmi_candidates import check_illoc, diff_blocks, tokens
from phase6_degraded_corpus.src.planning.plan_mmi_operations import (
    fix_articles, negate, corrupt_date, corrupt_number, meaning_candidates, plan_meaning, splice, split_sentences,
)


class PlannerTests(unittest.TestCase):
    def test_sentence_split_ignores_initials_and_titles(self):
        self.assertEqual(len(split_sentences('Thomas E. "Tom" Donilon is an official. He was an adviser.')), 2)
        self.assertEqual(len(split_sentences("Dr. Smith lives in St. Louis.")), 1)

    def test_rule_number_keeps_format_and_avoids_original(self):
        new = corrupt_number("45,000", "The city has 45,000 people and 90,000 visitors.", 1, "k")
        self.assertRegex(new, r"^\d{1,3}(,\d{3})+$")
        self.assertNotIn(new, "The city has 45,000 people and 90,000 visitors.")

    def test_rule_date_changes_year_and_month(self):
        self.assertNotEqual(corrupt_date("1963", "born in 1963", 1, "k"), "1963")
        self.assertIn(corrupt_date("March", "in March", 1, "k"), {m for m in (
            "January", "February", "April", "May", "June", "July", "August",
            "September", "October", "November", "December")})

    def test_number_cues_skip_days_names_and_ranges(self):
        for text in ("He was born on 20 March 1963.", "He died on April 26, 1865.",
                     "Voyager 2 visited Neptune.", "It needs 2,000 to 3,000 cocoons."):
            self.assertEqual(meaning_candidates(text)["number"], [], text)
        self.assertEqual([c["text"] for c in meaning_candidates("The city has 45,000 people.")["number"]], ["45,000"])

    def test_property_cues_skip_names(self):
        self.assertEqual(meaning_candidates("She was born in New York City.")["property"], [])

    def test_meaning_span_must_be_supported_by_original(self):
        row = {"canonical_pair_id": "p", "original": "Clara was a pianist.",
               "clean_simplification": "Clara was a pianist born in 1819."}
        planned = plan_meaning([row], 1)[0]
        self.assertNotEqual(planned.get("meaning_type"), "date")

    def test_splice_deletion_keeps_spacing(self):
        text = "The bridge was never completed."
        self.assertEqual(splice(text, 15, 20, ""), "The bridge was completed.")


class NegationRuleTests(unittest.TestCase):
    def neg(self, text, word):
        start = text.index(word)
        return negate(text, {"text": word, "start": start, "end": start + len(word)})

    def test_cases_from_heldout_audit(self):
        self.assertEqual(self.neg("In 1800 there were Russian settlements.", "were"), "In 1800 there were no Russian settlements.")
        self.assertEqual(self.neg("He was also a singer.", "was"), "He was also not a singer.")
        self.assertEqual(self.neg("The flight will leave now.", "will"), "The flight will not leave now.")
        self.assertEqual(self.neg("He has two sons.", "has"), "He does not have two sons.")
        self.assertEqual(self.neg("He has won titles.", "has"), "He has not won titles.")
        self.assertEqual(self.neg("It was never built.", "never"), "It was built.")

    def test_articles(self):
        self.assertEqual(fix_articles("a American and an player, an hour, a university"), "an American and a player, an hour, a university")


class CheckTests(unittest.TestCase):
    row = {"clean_simplification": "Koalas eat eucalyptus leaves.", "clean_acceptability": 0.99}
    feats = {"acceptability": 0.99}
    cfg = {"tau_accept": 0.95, "delta": 0.04}

    def test_directive_and_hedge_lexicon_checks(self):
        ok = check_illoc("assertion_to_directive", self.row, "Remember that koalas eat eucalyptus leaves.", self.feats, self.cfg, None)
        self.assertTrue(all(ok.values()), ok)
        bad = check_illoc("assertion_to_hedged", self.row, "Koalas might eat green leaves.", self.feats, self.cfg, None)
        self.assertFalse(all(bad.values()))

    def test_numbers_are_single_tokens(self):
        blocks = diff_blocks(tokens("It is 191,976 km wide."), tokens("It is 383,952 km wide."))
        self.assertEqual(len(blocks), 1)

    def test_statistics(self):
        lo, hi = wilson(30, 40)
        self.assertTrue(0.59 < lo < 0.62 and 0.85 < hi < 0.87)
        self.assertEqual(mcnemar_exact(0, 0), 1.0)
        self.assertLess(mcnemar_exact(0, 10), 0.01)


if __name__ == "__main__":
    unittest.main()
