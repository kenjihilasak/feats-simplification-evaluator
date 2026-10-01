import spacy

from phase6_degraded_corpus.src.generation.generate_fose_rules import generate_fluency
from phase6_degraded_corpus.src.selection.select_fose_pools import eligible_rule_sites, structural_features


def test_all_fluency_rules_must_change():
    nlp = spacy.load("en_core_web_sm")
    examples = {
        "agreement": "The bird is here.",
        "determiner_drop": "She found a book.",
        "preposition_swap": "She lives in Paris.",
        "word_order": "It is a famous singer.",
    }
    for kind, sentence in examples.items():
        result = generate_fluency(sentence, kind, 20260930, nlp, kind)
        assert result is not None
        assert result["degraded"] != sentence


def test_fluency_must_not_change_without_requested_site():
    nlp = spacy.load("en_core_web_sm")
    assert generate_fluency("Birds fly.", "p", 20260930, nlp, "preposition_swap") is None


def test_omit_rejects_alignment_with_insertion():
    features = structural_features("The old house fell.", "The house suddenly fell.")
    assert eligible_rule_sites("OMIT", features) == []


def test_syn_requires_rarer_original_wording():
    qualifying = structural_features("The physician arrived.", "The doctor arrived.")
    reversed_pair = structural_features("The doctor arrived.", "The physician arrived.")
    assert eligible_rule_sites("SYN", qualifying)
    assert eligible_rule_sites("SYN", reversed_pair) == []
