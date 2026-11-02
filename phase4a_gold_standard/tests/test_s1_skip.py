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


class StrategyPoorTests(unittest.TestCase):
    def test_strategy_not_well_applied_is_a_reportable_issue(self):
        words = [{"index": 0, "start": 0, "end": 2, "text": "Il"}]
        answer = {"choice": "X", "selected_original_words": words, "side_effects": ["strategy_poor"], "side_effect_versions": ["Y"]}
        S1Service._validate_answer({"original": "Il gioco non valeva la candela.", "format": "pair", "versions": {"X": "a", "Y": "b"}}, answer, submit=True)
