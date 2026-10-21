import json
from pathlib import Path

from phase6_degraded_corpus.src.evaluation.shortcut_audit import audit, pair_examples, cv_auc, shallow_features, write_report
from phase6_degraded_corpus.src.generation.generate_fose_rules import explanatory_pattern, span_is_balanced
from phase6_degraded_corpus.src.planning.plan_mmi_operations import plan_illoc, plan_mod


def row(pid, text, axis):
    return {"canonical_pair_id": pid, "canonical_original_id": pid, "clean_simplification": text, "original": text, "target_axis": axis}


def test_explanation_patterns_are_explicit():
    assert explanatory_pattern(["Mars"], [",", "a", "red", "world", ","], ["is"]) == "appositive_gloss"
    assert explanatory_pattern(["Mars"], ["(", "red", "world", ")"], ["is"]) == "parenthetical_gloss"
    assert explanatory_pattern(["Mars"], [",", "which", "is", "red", ","], ["is"]) == "definitional_relative"
    assert explanatory_pattern(["Mars"], ["known", "as", "Ares"], ["is"]) == "marker_gloss"
    assert explanatory_pattern(["Mars"], ["discovered", "in", "1999"], ["is"]) is None


def test_omit_span_boundary_balance():
    assert span_is_balanced(["(", "red", ")"])
    assert not span_is_balanced(["red", ")"])
    assert not span_is_balanced(['"', "red"])


def test_mod_planner_keeps_count_and_can_reorder_dependency():
    planned = plan_mod([row("x", "Marie opened the shop. She closed it later.", "MOD")], 4)[0]
    assert planned["operation"] in {"mod_front_heavy", "mod_bury_topic", "mod_sentence_reorder"}
    if planned["operation"] == "mod_sentence_reorder":
        assert planned["rule_output"]["degraded"].count(".") == planned["clean_simplification"].count(".")


def test_illoc_planner_uses_reverse_for_questions_and_no_question_ops_otherwise():
    planned = plan_illoc([row("q", "Is it open?", "ILLOC"), row("s", "It is open.", "ILLOC")], 2)
    ops = {x["canonical_pair_id"]: x["operation"] for x in planned}
    assert ops["q"] == "illoc_question_to_statement"
    assert ops["s"] == "illoc_hedge_swap"  # no modal verb, so no imperative


def test_shortcut_features_and_reports(tmp_path):
    assert shallow_features("It is here.", "It may be here.")[0] == 1
    rows = [{**row(str(i), f"Item {i} is here.", "ILLOC"), "degraded_simplification": f"Item {i} may be here.", "operation": "illoc_hedge_swap"} for i in range(10)]
    report = audit(rows)
    assert "ILLOC" in report["axes"]
    write_report(report, tmp_path)
    assert json.loads((tmp_path / "shortcut_audit.json").read_text())["gate_auc"] == .70


def test_identical_pair_has_chance_auc():
    rows = [{**row(str(i), f"Item {i} is here.", "ILLOC"),
             "degraded_simplification": f"Item {i} is here.",
             "operation": "identity", "clean_acceptability": .9,
             "clean_nli_probabilities": {"entailment": .8},
             "features": {"acceptability": .9, "nli_original_degraded": {"entailment": .8}}}
            for i in range(10)]
    x, y, _, _ = pair_examples(rows)
    assert abs(cv_auc(x, y) - .5) < .01

def test_rule_axes_split_gate_and_definitional_features():
    rows = [{**row(str(i), f"Item {i} is here.", "OMIT"),
             "degraded_simplification": f"Item {i} from London is here.", "operation": "omit"}
            for i in range(10)]
    result = audit(rows)["axes"]["OMIT"]
    assert "definitional" in result
    assert result["gate"]["largest_weight_feature"] not in {"delta_tokens", "delta_characters", "token_overlap"}


def test_v3_cluster_job_and_model_configs():
    import json
    from pathlib import Path
    root = Path(__file__).parents[2] / "phase6_degraded_corpus"
    job = (root / "jobs/submit_mmi_v3_generate_gpu.sh").read_text()
    config = json.loads((root / "configs/experiments/mmi_en_v3_generation.json").read_text())
    assert "--gres=gpu:l40s:1" in job and "--partition=gpu" in job
    assert config["configs"]["MOD_C2"]["model_id"] == "google/gemma-3-12b-it"
    assert config["configs"]["ILLOC_C1"]["model_id"] == "Qwen/Qwen2.5-7B-Instruct"
    assert config["configs"]["MOD_C2"]["n"] == config["configs"]["ILLOC_C1"]["n"] == 4


def test_illoc_planner_only_makes_imperatives_from_modal_sentences():
    rows = [row(f"m{i}", "Visitors should book tickets early.", "ILLOC") for i in range(4)]
    ops = {x["operation"] for x in plan_illoc(rows, 1)}
    assert ops <= {"illoc_imperative_swap", "illoc_hedge_swap"} and "illoc_exclaim" not in ops


class _Spacy:
    def __init__(self):
        import spacy
        self.nlp = spacy.load("en_core_web_sm")


def test_mod_movement_requires_real_reordering():
    from phase6_degraded_corpus.src.evaluation.score_mmi_candidates import mod_movement
    ck = _Spacy()
    clean = "The museum opened a new gallery after many years of planning."
    assert mod_movement("mod_front_heavy", clean, "After many years of planning, the museum opened a new gallery.", ck)["fronted_phrase_ge_4_tokens"]
    assert not mod_movement("mod_front_heavy", clean, "Then the museum opened a new gallery after many years of planning.", ck)["fronted_phrase_ge_4_tokens"]
    clean = "Marie Curie discovered radium in 1898."
    assert mod_movement("mod_bury_topic", clean, "In 1898, radium was discovered by Marie Curie.", ck)["topic_moved_to_end"]
    assert not mod_movement("mod_bury_topic", clean, "In 1898, Marie Curie discovered radium.", ck)["topic_moved_to_end"]
