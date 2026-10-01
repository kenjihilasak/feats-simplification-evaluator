import unittest

import spacy

from phase6_degraded_corpus.src.generation.generate_meaning_graded import (
    balanced, century, major_losses, mild_losses, neutral_trims, tidy,
)

NLP = spacy.load("en_core_web_sm")


class GradedRuleTests(unittest.TestCase):
    def texts(self, items, rule):
        return {c["text"] for c in items if c["rule"] == rule}

    def test_neutral_trims(self):
        self.assertIn("The Firebird is a ballet.", self.texts(neutral_trims("The Firebird ( ; ) is a ballet."), "empty_or_pronunciation_parenthetical"))
        self.assertIn("It is known as CAF.", self.texts(neutral_trims("It is also known as CAF."), "adverb_also"))
        self.assertFalse(neutral_trims("It is just below the circle."))
        text = "They won, but lost later. They won, but lost later."
        self.assertFalse(major_losses(NLP(text), text))

    def test_mild_appositive_and_adjective(self):
        doc = NLP("Great Musgrave is a village in Cumbria, England.")
        self.assertIn("Great Musgrave is a village in Cumbria.", self.texts(mild_losses(doc), "appositive"))
        doc = NLP("César is a Brazilian football player.")
        self.assertIn("César is a football player.", self.texts(mild_losses(doc), "adjective"))

    def test_major_relative_clause_and_sentence(self):
        text = "Dark Horse Comics is an American company that creates comic books."
        self.assertIn("Dark Horse Comics is an American company.", self.texts(mild_losses(NLP(text)), "drop_relative_clause"))
        text = "M83 is a French band. They formed in 2001."
        self.assertIn("M83 is a French band.", self.texts(major_losses(NLP(text), text), "drop_sentence"))
        self.assertIn("M83 is a French band. They formed in the 21st century.", self.texts(mild_losses(NLP(text)), "generalize_year"))
        self.assertEqual({c["rule"] for c in major_losses(NLP(text), text)}, {"drop_sentence"})
        self.assertFalse(self.texts(neutral_trims("It is very old."), "adverb_very"))
        self.assertIn("It is old.", self.texts(mild_losses(NLP("It is very old.")), "intensifier_very"))

    def test_helpers(self):
        self.assertEqual(century(1867), "the 19th century")
        self.assertEqual(century(2001), "the 21st century")
        self.assertFalse(balanced('She played "Wildfire.', 'She played "Wildfire".'))
        self.assertEqual(tidy("He was born in Paris , in 1990 ."), "He was born in Paris, in 1990.")


if __name__ == "__main__":
    unittest.main()
