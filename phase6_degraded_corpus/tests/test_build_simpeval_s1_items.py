import json

import pytest

from phase6_degraded_corpus.src.annotation import build_simpeval_s1_items as m

SYSTEMS = ("Human 1 Writing", "Human 2 Writing", "GPT-3-few-shot", "GPT-3-zero-shot", "Muss", "T5-3B")


def csv_rows(n=4, h2_better=()):
    rows = []
    for i in range(n):
        for j, s in enumerate(SYSTEMS):
            r = 80.0 if (s == "Human 2 Writing" and i in h2_better) else 60.0 if s == "Human 1 Writing" else 50.0
            rows.append({"original_id": str(i), "original": f"The original sentence number {i} is rather long and complex.",
                         "generation": f"Simpler text {j} for sentence {i}.", "system": s, "sentence_type": "x",
                         "rating_1": r, "rating_2": r, "rating_3": r})
    return rows


def pid(oid, system):
    return m.pair_id(str(oid), system)


def test_human_choice_and_tie():
    rows = csv_rows(3, h2_better={1})
    for r in rows:  # original 2: exact tie -> Human 1
        if r["original_id"] == "2" and r["system"] == "Human 2 Writing":
            r["rating_1"] = r["rating_2"] = r["rating_3"] = 60.0
    sel = m.select_versions(rows)
    assert [v[0]["system"] for v in sel.values()] == ["Human 1 Writing", "Human 2 Writing", "Human 1 Writing"]
    assert [x["system"] for x in sel["0"]][1:] == ["GPT-3-few-shot", "Muss"]
    recs = m.phase3a_records(sel)
    assert len(recs) == 9 and all(r["id"] == r["canonical_pair_id"] for r in recs)
    assert recs[0]["id"] == "pair:en:simpeval2022:0:human-1-writing"


def test_consensus_needs_two_models(tmp_path):
    paths = {}
    for k, model in enumerate(m.MODELS):
        p = tmp_path / f"{model}.jsonl"
        codes = ["OMIT"] if k < 2 else ["SYN"] if k == 2 else []
        p.write_text(json.dumps({"canonical_pair_id": "a", "predicted_codes": codes}) + "\n"
                     + json.dumps({"canonical_pair_id": "b", "predicted_codes": []}) + "\n")
        paths[model] = p
    c = m.confirmed(paths)
    assert c == {"a": {"OMIT": sorted(m.MODELS[:2])}, "b": {}}


def strategies_for(sel, per_original):
    """per_original: oid -> [codes for human, gpt, muss]."""
    out = {}
    for oid, versions in sel.items():
        for v, codes in zip(versions, per_original.get(oid, [[], [], []])):
            out[v["pair_id"]] = {c: list(m.MODELS[:2]) for c in codes}
    return out


def test_axis_majority_tie_and_fallback():
    sel = m.select_versions(csv_rows(6))
    strat = strategies_for(sel, {
        "0": [["OMIT"], ["OMIT", "COMP"], ["SYN"]],          # majority OMIT
        "1": [["MOD"], ["MOD", "SYN"], ["SYN"]],              # tie 2-2, human has MOD
        "2": [["COMP", "SYNT"], ["COMP"], ["SYNT"]],          # no axis -> fallback
        "3": [["EXPL"], [], []],                              # only one version -> fallback
        "4": [[], ["SYN"], ["SYN"]],                          # human not needed when no tie
        "5": [[], [], []],
    })
    axes = m.choose_axes(sel, strat, hosts_act=lambda text: "sentence 3" in text)
    assert axes["0"][0] == "OMIT"
    assert axes["1"][0] == "MOD" and "human" in axes["1"][1]
    assert axes["4"][0] == "SYN"
    assert axes["3"][0] == "ILLOC"
    assert sorted([axes["2"][0], axes["5"][0]]) == ["FLUENCY", "MEANING"]


def test_items_shuffled_and_blind():
    sel = m.select_versions(csv_rows(12))
    strat = strategies_for(sel, {str(i): [["OMIT"], ["OMIT"], []] for i in range(12)})
    public, key, report = m.build(sel, strat, hosts_act=lambda t: False)
    assert len(public) == 12 and report["by_axis"] == {"OMIT": 12}
    assert sorted(p["case_id"] for p in public) == [f"EN-SE{i:03d}" for i in range(1, 13)]
    human_labels = {k["human_label"] for k in key}
    assert len(human_labels) > 1  # labels shuffled
    for p, k in zip(public, key):
        assert p["case_id"] == k["case_id"] and p["format"] == "rank3" and set(p["versions"]) == set("XYZ")
        assert set(p) == {"case_id", "language", "axis", "format", "original", "versions"}
        text = json.dumps(p).casefold()
        for word in ("human", "gpt", "muss", "simpeval", "writing", "system", "rating"):
            assert word not in text
        assert k["source"] == "simpeval_2022" and set(k["systems"].values()) == {"Human 1 Writing", "GPT-3-few-shot", "Muss"}
        assert k["systems"][k["human_label"]] == "Human 1 Writing"
        assert k["confirmed_strategies"][k["human_label"]] == {"OMIT": sorted(m.MODELS[:2])}


def test_public_items_have_no_key_fields():
    sel = m.select_versions(csv_rows(2))
    public, _, _ = m.build(sel, strategies_for(sel, {}), hosts_act=lambda t: False)
    for p in public:
        assert "simpeval" not in json.dumps(p).casefold()
        assert not any(k in p for k in ("systems", "source", "original_id", "mean_human_rating", "pair_ids"))
