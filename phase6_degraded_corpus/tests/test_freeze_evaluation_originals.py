import unittest

from phase6_degraded_corpus.src.selection.freeze_evaluation_originals import (
    strong_key,
    weak_key,
)


class EvaluationOriginalKeyTest(unittest.TestCase):
    def test_tokenized_and_detokenized_punctuation_match(self):
        self.assertNotEqual(weak_key("built later ."), weak_key("built later."))
        self.assertEqual(strong_key("built later ."), strong_key("built later."))

    def test_nfkc_casefold_ptb_and_underscore(self):
        self.assertEqual(
            strong_key("Ｃafé_FOO -LRB- Test -RRB-"),
            strong_key("café foo (test)"),
        )

    def test_punctuation_only_is_empty(self):
        self.assertEqual(strong_key("._!?"), "")


if __name__ == "__main__":
    unittest.main()
