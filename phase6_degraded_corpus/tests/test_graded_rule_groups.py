from phase6_degraded_corpus.src.generation.generate_fose_rules import alignment
from phase6_degraded_corpus.src.generation.generate_graded_rule_groups import apply_sites


def _sites(original, simple, tag):
    _, _, ops = alignment(original, simple)
    return [(i1, i2, j1, j2) for op, i1, i2, j1, j2 in ops if op == tag]


def test_syn_two_sites_restore_both_words():
    original = "The physician prescribed a potent medication."
    simple = "The doctor prescribed a strong medication."
    sites = _sites(original, simple, "replace")
    assert len(sites) == 2
    assert apply_sites("SYN", original, simple, sites[:1])["degraded"] == "The physician prescribed a strong medication."
    assert apply_sites("SYN", original, simple, sites)["degraded"] == original


def test_omit_two_sites_reinsert_both_spans():
    original = "In 1990, the old bridge, built of stone, was closed for repairs."
    simple = "The old bridge was closed."
    sites = _sites(original, simple, "delete")
    both = apply_sites("OMIT", original, simple, sites)["degraded"]
    one = apply_sites("OMIT", original, simple, sites[:1])["degraded"]
    assert len(both.split()) > len(one.split()) > len(simple.split())


def test_detokenize_closes_quote_pairs():
    from phase6_degraded_corpus.src.generation.generate_fose_rules import detokenize, tokens
    text = 'The song " Help " was a hit, called " Yesterday " later.'
    assert detokenize(tokens(text)) == 'The song "Help" was a hit, called "Yesterday" later.'


def test_s1_items_hide_levels_and_operations():
    import json
    from pathlib import Path
    path = Path("phase6_degraded_corpus/runs/annotation_v1/s1_items.jsonl")
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        row = json.loads(line)
        assert set(row) == {"case_id", "axis", "format", "original", "versions"}
        assert set(row["versions"]) <= {"X", "Y", "Z"}
