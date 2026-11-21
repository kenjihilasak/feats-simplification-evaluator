import unittest

from phase4a_gold_standard.backend.s1_service import S1Service, ValidationError

TASK = {"original": "Il gioco non valeva la candela.", "format": "pair", "versions": {"X": "a", "Y": "b"}}
BASE = {"choice": "Same", "side_effects": ["none"], "side_effect_versions": [], "note": "r", "ideal_simplification": "i"}
WORD = [{"index": 0, "start": 0, "end": 2, "text": "Il"}]


class NoAffectedWordsTests(unittest.TestCase):
    def test_ticking_no_affected_word_replaces_the_selection(self):
        S1Service._validate_answer(TASK, BASE | {"selected_original_words": [], "no_affected_words": True}, submit=True)

    def test_without_the_box_a_word_is_still_required(self):
        for answer in (BASE | {"selected_original_words": []}, BASE | {"selected_original_words": [], "no_affected_words": False}):
            with self.assertRaises(ValidationError):
                S1Service._validate_answer(TASK, answer, submit=True)

    def test_words_and_the_box_are_exclusive(self):
        with self.assertRaises(ValidationError):
            S1Service._validate_answer(TASK, BASE | {"selected_original_words": WORD, "no_affected_words": True}, submit=True)

    def test_the_box_is_a_boolean(self):
        with self.assertRaises(ValidationError):
            S1Service._validate_answer(TASK, BASE | {"selected_original_words": [], "no_affected_words": "yes"}, submit=True)

    def test_answers_from_the_old_page_still_validate(self):
        S1Service._validate_answer(TASK, BASE | {"selected_original_words": WORD}, submit=True)


if __name__ == "__main__":
    unittest.main()
