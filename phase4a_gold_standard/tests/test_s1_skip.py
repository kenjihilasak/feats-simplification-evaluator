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
        answer = {"choice": "X", "selected_original_words": words, "side_effects": ["strategy_poor"], "side_effect_versions": ["Y"],
                  "note": "Y keeps the passive", "ideal_simplification": "Il gioco non valeva la pena."}
        S1Service._validate_answer({"original": "Il gioco non valeva la candela.", "format": "pair", "versions": {"X": "a", "Y": "b"}}, answer, submit=True)


class IdealSimplificationTests(unittest.TestCase):
    def test_a_skipped_item_may_carry_an_ideal_version(self):
        S1Service._validate_answer({"original": "x", "format": "pair"},
                                   {"skipped": True, "note": "", "ideal_simplification": "Il gioco non valeva la pena."}, submit=True)

    def test_the_ideal_version_has_a_length_limit(self):
        with self.assertRaises(ValidationError):
            S1Service._validate_answer({"original": "x", "format": "pair"}, {"ideal_simplification": "a" * 4001}, submit=False)


class RequiredFieldTests(unittest.TestCase):
    words = [{"index": 0, "start": 0, "end": 2, "text": "Il"}]
    task = {"original": "Il gioco non valeva la candela.", "format": "pair", "versions": {"X": "a", "Y": "b"}}

    def test_rationale_and_ideal_version_are_required_on_submit(self):
        base = {"choice": "X", "selected_original_words": self.words, "side_effects": ["none"], "side_effect_versions": []}
        for missing in ({"ideal_simplification": "Va bene."}, {"note": "X is clearer"}):
            with self.assertRaises(ValidationError):
                S1Service._validate_answer(self.task, {**base, **missing}, submit=True)
        S1Service._validate_answer(self.task, {**base, "note": "X is clearer", "ideal_simplification": "Va bene."}, submit=True)

    def test_drafts_and_skips_need_neither(self):
        S1Service._validate_answer(self.task, {"choice": "X"}, submit=False)
        S1Service._validate_answer(self.task, {"skipped": True, "note": ""}, submit=True)
