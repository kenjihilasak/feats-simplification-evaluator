import unittest

from phase4a_gold_standard.backend.s1_service import S1Service, ValidationError, original_words

# "José" and "Kraków" with decomposed accents (letter + U+0301), as in EN-S342 and S006.
DECOMPOSED = "Juan José visited Kraków and Ariège in May."


class OriginalWordTests(unittest.TestCase):
    def test_a_decomposed_accent_stays_inside_its_word(self):
        self.assertEqual([w[2] for w in original_words(DECOMPOSED)],
                         ["Juan", "José", "visited", "Kraków", "and", "Ariège", "in", "May"])

    def test_apostrophes_and_hyphens_join_words_as_in_the_page(self):
        self.assertEqual([w[2] for w in original_words("l’homme well-known rock'n'roll -x y- _z")],
                         ["l’homme", "well-known", "rock'n'roll", "x", "y", "z"])

    def test_a_word_after_a_decomposed_accent_can_be_submitted(self):
        start = DECOMPOSED.index("May")
        words = [{"index": 7, "start": start, "end": start + 3, "text": "May"},
                 {"index": 3, "start": DECOMPOSED.index("Krako"), "end": DECOMPOSED.index("Krako") + 7, "text": "Kraków"}]
        answer = {"choice": "X", "selected_original_words": words, "side_effects": ["none"], "side_effect_versions": [],
                  "note": "r", "ideal_simplification": "i"}
        S1Service._validate_answer({"original": DECOMPOSED, "format": "pair", "versions": {"X": "a", "Y": "b"}}, answer, submit=True)

    def test_a_split_accent_is_still_rejected(self):
        answer = {"choice": "X", "selected_original_words": [{"index": 1, "start": 5, "end": 9, "text": "Jose"}],
                  "side_effects": ["none"], "side_effect_versions": [], "note": "r", "ideal_simplification": "i"}
        with self.assertRaises(ValidationError):
            S1Service._validate_answer({"original": DECOMPOSED, "format": "pair", "versions": {"X": "a", "Y": "b"}}, answer, submit=True)


if __name__ == "__main__":
    unittest.main()
