import unittest

from phase4a_gold_standard.backend.s1_service import S1Service, ValidationError


class SkipTests(unittest.TestCase):
    task = {"original": "Il gioco non valeva la candela.", "format": "pair"}

    def test_a_skipped_item_needs_no_judgement(self):
        S1Service._validate_answer(self.task, {"skipped": True, "note": "context missing"}, submit=True)

    def test_a_skipped_item_carries_only_a_note(self):
        with self.assertRaises(ValidationError):
            S1Service._validate_answer(self.task, {"skipped": True, "choice": "X"}, submit=True)

    def test_an_answer_still_needs_selected_words(self):
        with self.assertRaises(ValidationError):
            S1Service._validate_answer(self.task, {"choice": "X"}, submit=True)
