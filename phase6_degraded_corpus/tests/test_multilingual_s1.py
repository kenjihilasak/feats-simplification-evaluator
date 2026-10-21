import unittest

from phase6_degraded_corpus.src.generation.generate_fose_rules import (
    detokenize, explanatory_pattern, generate_expl, generate_omit, generate_syn, tokens,
)
from phase6_degraded_corpus.src.planning.plan_mmi_operations import _dependent_second, split_sentences
from phase6_degraded_corpus.src.selection.select_multilingual_pools import TASK_ORDER, mod_host, shape


class RuleTests(unittest.TestCase):
    def test_english_detokenize_unchanged(self):
        self.assertEqual(detokenize(tokens("It is a apple , not an pear .")), "It is an apple, not a pear.")

    def test_french_keeps_number_and_high_punctuation_spacing(self):
        out = generate_omit("Il y a 6,800 insulaires du détroit de Torres sur les îles ?", "Il y a 6,800 insulaires sur les îles ?",
                            "p", 1, lang="fr")
        self.assertEqual(out["degraded"], "Il y a 6,800 insulaires du détroit de Torres sur les îles ?")

    def test_no_english_article_rule_outside_english(self):
        self.assertEqual(detokenize(["Una", "a", "una"], "es", ("Una a una",)), "Una a una")

    def test_spanish_and_french_explanations(self):
        self.assertEqual(explanatory_pattern(["X"], [",", "que", "es", "un", "órgano", ","], ["es"], "es"), "definitional_relative")
        self.assertEqual(explanatory_pattern(["X"], [",", "l'énergie", "de", "l'eau", ","], ["est"], "fr"), "appositive_gloss")
        out = generate_expl("La tachycardie est fréquente.", "La tachycardie, c'est-à-dire un cœur qui bat vite, est fréquente.", "p", 1, lang="fr")
        self.assertEqual((out["degraded"], out["expl_pattern"]), ("La tachycardie est fréquente.", "marker_gloss"))

    def test_pretokenized_spacing_is_kept(self):
        original = "un essai ( publié en chinois ) en cours , et sept essais d' évaluation"
        simple = "un essai en cours , et sept essais d' évaluation"
        self.assertEqual(generate_omit(original, simple, "p", 1, lang="fr")["degraded"], original)
        out = generate_expl("x est un mot .", "x , qui est un mot simple , est un mot .", "p", 1, lang="fr")
        self.assertEqual(out["degraded"], "x est un mot .")

    def test_spanish_synonym_restored(self):
        out = generate_syn("El médico llegó.", "El doctor llegó.", "p", 1, lang="es")
        self.assertEqual(out["degraded"], "El médico llegó.")


class SentenceTests(unittest.TestCase):
    def test_spanish_question_and_abbreviation(self):
        self.assertEqual(split_sentences("Hay una comisión. ¿Por qué debatimos? El Sr. Pérez vino.", "es"),
                         ["Hay una comisión.", "¿Por qué debatimos?", "El Sr. Pérez vino."])

    def test_french_accented_capital(self):
        self.assertEqual(split_sentences("Il pleut. Écoutez bien.", "fr"), ["Il pleut.", "Écoutez bien."])

    def test_dependent_second_sentence(self):
        self.assertTrue(_dependent_second("Il y a une organisation.", "L'organisation aide les gens.", "fr"))
        self.assertTrue(_dependent_second("Hay una comisión.", "Ella pide algo.", "es"))
        self.assertFalse(_dependent_second("Hay una comisión.", "Mañana llueve.", "es"))


class AllocationTests(unittest.TestCase):
    def test_mod_host_needs_dependent_pair_and_long_sentence(self):
        text = "La Comisión Europea presentó ayer en Bruselas una propuesta nueva sobre el presupuesto. Esta propuesta cambia mucho."
        host = mod_host(text, "es")
        self.assertEqual((host["reorder"], host["target_sentence_index"]), ([0], 0))
        self.assertIsNone(mod_host("Hace sol. Mañana llueve.", "es"))

    def test_shape_gives_generators_their_fields(self):
        row = {"canonical_pair_id": "p", "eligible_sites": {"SYN": [(1, 2, 1, 2), (4, 5, 4, 5)]}, "mod_host": None,
               "illoc_host": {"imperative_cue": True}}
        self.assertEqual(set(shape("SYN_graded", row, 1)["sites"]), {"A", "B"})
        self.assertEqual(shape("ILLOC_pair", row, 1)["operation"], "illoc_imperative_swap")
        self.assertEqual(TASK_ORDER[0], "EXPL_pair")


if __name__ == "__main__":
    unittest.main()
