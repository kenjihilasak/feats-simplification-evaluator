from phase6_degraded_corpus.src.evaluation.materialize_mmi_full import split_for
from phase6_degraded_corpus.src.generation.generate_fose_rules import generate_expl, generate_omit, generate_syn


def test_omit_changes_once():
    out = generate_omit("The old red house burned down.", "The house burned down.", "p", 1)
    assert out and out["degraded"] == "The old red house burned down."


def test_omit_must_not_change_without_delete():
    assert generate_omit("The house burned down.", "The house burned down.", "p", 1) is None


def test_syn_restores_original_span():
    out = generate_syn("The physician arrived.", "The doctor arrived.", "p", 1)
    assert out and out["degraded"] == "The physician arrived."


def test_expl_removes_inserted_span():
    out = generate_expl("Mars is a planet.", "Mars, a red world, is a planet.", "p", 1)
    assert out and len(out["degraded"]) < len("Mars, a red world, is a planet.")


def test_split_consistency_with_mmi():
    oid = "original:en:test"
    assert split_for(oid, 20260930, .1) == split_for(oid, 20260930, .1)
