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
               "illoc_host": {"kind": "directive", "sentences": ["A.", "Bring it."], "target_sentence_index": 1}}
        self.assertEqual(set(shape("SYN_graded", row, 1)["sites"]), {"A", "B"})
        illoc = shape("ILLOC_pair", row, 1)
        self.assertEqual((illoc["operation"], illoc["target_sentence_index"]), ("illoc_directive_to_impersonal", 1))
        self.assertEqual(TASK_ORDER[0], "ILLOC_pair")  # direct acts are the scarcest hosts


class IllocV4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from phase6_degraded_corpus.src.common.languages import load_nlp
        cls.nlp = {lang: load_nlp(lang) for lang in ("en", "ca")}

    def host(self, text, lang="en"):
        from phase6_degraded_corpus.src.selection.select_multilingual_pools import illoc_host
        found = illoc_host(text, lang, self.nlp[lang])
        return found and (found["kind"], found["target_sentence_index"])

    def test_direct_acts_on_the_reader(self):
        self.assertEqual(self.host("Bring your ID to the appointment."), ("directive", 0))
        self.assertEqual(self.host("The shop is small. Have you used these services before?"), ("question", 1))
        self.assertEqual(self.host("You can only find it on Christmas Island."), ("address", 0))
        self.assertEqual(self.host("Envieu la sol·licitud per internet abans del dia 9.", "ca"), ("directive", 0))

    def test_statements_titles_and_quotes_host_nothing(self):
        self.assertIsNone(self.host("The city was founded in 1820 by Smith."))
        self.assertIsNone(self.host("There can also be several articles on the same topic."))
        self.assertIsNone(self.host("In other words, z should be a multiple of a number m."))
        self.assertEqual(self.host("If you need to pick a font size, use a relative size."), ("directive", 0))
        self.assertIsNone(self.host("Bring Me the Horizon are a British metalcore band."))
        self.assertIsNone(self.host('Susie Essman plays Susie Greene in "Curb Your Enthusiasm".'))
        self.assertNotEqual((self.host("Tindreu una resposta en sis mesos com a màxim.", "ca") or ("none",))[0], "directive")


class RuleFixTests(unittest.TestCase):
    def test_article_before_numbers(self):
        self.assertEqual(detokenize(tokens("It is a 1843 story , an 1920 film and an 8 year plan .")),
                         "It is an 1843 story, a 1920 film and an 8 year plan.")

    def test_article_before_consonant_sounding_vowels(self):
        self.assertEqual(detokenize(tokens("He was an United States general , an hour ago , in a apple farm .")),
                         "He was a United States general, an hour ago, in an apple farm.")

    def test_restored_span_before_final_punctuation_keeps_its_space(self):
        # FR v1 round: 21 of 60 OMIT items had "sentieret", "1979en"…
        self.assertEqual(generate_omit("Ils ont commencé à sortir un par un.", "Ils ont commencé à sortir.", "p", 1, lang="fr")["degraded"],
                         "Ils ont commencé à sortir un par un.")

    def test_no_rule_site_in_a_quoted_title(self):
        from phase6_degraded_corpus.src.selection.select_fose_pools import eligible_rule_sites, structural_features
        feats = structural_features('In " Oedipus Rex " , Oedipus is the protagonist .',
                                    'In " Oedipus the King " , Oedipus is the main character .')
        self.assertEqual(eligible_rule_sites("SYN", feats), [])

    def test_russian_and_arabic_sentences(self):
        self.assertEqual(split_sentences("Город большой. Вы там были?", "ru"), ["Город большой.", "Вы там были?"])
        self.assertEqual(split_sentences("ذهب الولد إلى المدرسة. هل تعرفه؟", "ar"), ["ذهب الولد إلى المدرسة.", "هل تعرفه؟"])


if __name__ == "__main__":
    unittest.main()
