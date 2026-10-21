#!/usr/bin/env python3
"""Build the Spanish/French S1 pools: rule sites, checker scores and one task per original.

`prepare` (CPU) reads the language's Phase 2b file and records, per pair, the OMIT/SYN/EXPL rule sites and
whether it can host a MOD or ILLOC edit. `score` (GPU) scores every clean simplification with the language's
checkers and calibrates the acceptability thresholds the way the English ones were set (τ = 10th percentile of
clean texts, δ = median − τ), writing `checker_config.json` for every later step. `allocate` (CPU) applies the
clean-quality gates and gives each original at most one task, scarcest task first, so no original appears in two
S1 items.

Tasks mirror the English S1 round: OMIT and SYN graded groups (two rule sites), SYN and EXPL pairs, MOD graded
groups (a long sentence for LLM fronting plus a dependent sentence pair for the reorder rule) and ILLOC pairs.
OMIT also has pairs, because two OMIT sites in one pair are rare outside English. Any clean statement can host an
ILLOC edit, so pairs that serve no other task enter scoring only through a fixed sample (`illoc_only_sample`).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from collections import Counter, defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl
from phase6_degraded_corpus.src.common.languages import get as language
from phase6_degraded_corpus.src.planning.plan_mmi_operations import _dependent_second, split_sentences
from phase6_degraded_corpus.src.selection.freeze_evaluation_originals import strong_key
from phase6_degraded_corpus.src.selection.select_fose_pools import check_validated, eligible_rule_sites, structural_features
from phase6_degraded_corpus.src.selection.select_mmi_pools import ReservedMatcher, corpus_of

RULE_AXES = ("OMIT", "SYN", "EXPL")
# Scarcest first: an original goes to the first task it can serve.
TASK_ORDER = ("EXPL_pair", "SYN_graded", "OMIT_graded", "SYN_pair", "OMIT_pair", "MOD_graded", "ILLOC_pair")


def quantile(values: list[float], probability: float) -> float:
    values = sorted(values)
    position = (len(values) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def mod_host(simple: str, lang: str) -> dict | None:
    """A long sentence to front a phrase in, and an adjacent dependent pair to swap."""
    sentences = split_sentences(simple, lang)
    reorder = [i for i in range(len(sentences) - 1) if _dependent_second(sentences[i], sentences[i + 1], lang)]
    if not reorder:
        return None
    target = max(range(len(sentences)), key=lambda i: len(sentences[i].split()))
    if len(sentences[target].split()) < 10:
        return None
    return {"sentences": sentences, "reorder": reorder, "target_sentence_index": target}


def prepare(cfg: dict) -> tuple[list[dict], dict]:
    import spacy

    lang = cfg["language"]
    res = language(lang)
    nlp = spacy.load(res.spacy_model, disable=["ner"])  # as in English pool selection
    check_validated(Path(cfg["phase3a_validation_file"]))
    phase3 = {r["canonical_pair_id"]: r for r in read_jsonl(Path(cfg["phase3a_candidate_file"]))}
    excluded = ReservedMatcher(
        [{"strong_key": strong_key(t), "original": t}
         for f in cfg.get("exclude_files", []) for t in {r["original"] for r in read_jsonl(Path(f))}],
        cfg["near_duplicate_jaccard"])
    counters, rows = Counter(), []
    for row in read_jsonl(Path(cfg["phase2b_file"])):
        counters["input"] += 1
        corpus = corpus_of(row)
        if row.get("repaired_duplicate_of") or corpus not in cfg["corpora"]:
            counters["duplicate_or_corpus"] += 1; continue
        original, simple = row.get("original", "").strip(), row.get("simple", "").strip()
        if not original or not simple or original.casefold() == simple.casefold():
            counters["empty_or_identical"] += 1; continue
        if excluded.match(original):
            counters["excluded_original"] += 1; continue
        feats = structural_features(original, simple)
        if not cfg["original_token_range"][0] <= len(feats["left"]) <= cfg["original_token_range"][1]:
            counters["original_length"] += 1; continue
        p3 = phase3.get(row["canonical_pair_id"])
        strategy = p3["candidate_strategy_code"] if p3 else None
        # With `require_strategy` (as in English) a rule only undoes the single strategy Phase 3a detected.
        axes = [strategy] if cfg["require_strategy"] else list(RULE_AXES)
        sites = {}
        for axis in axes:
            if axis in RULE_AXES:
                found = eligible_rule_sites(axis, feats, nlp, lang)
                if found:
                    sites[axis] = found
        mod = mod_host(simple, lang)
        question = simple.rstrip().endswith("?")
        illoc = None if question else {"imperative_cue": bool(res.imperative_cue.search(simple))}
        if not sites and not mod and not illoc:
            counters["no_task"] += 1; continue
        counters["kept"] += 1
        rows.append({
            "schema": "feats-phase6-s1-pool-candidate-v1", "language": lang,
            "canonical_pair_id": row["canonical_pair_id"], "canonical_original_id": row["canonical_original_id"],
            "original": original, "clean_simplification": simple, "source": row["corpora"][0].get("source"),
            "corpus": corpus, "eligible_sites": sites, "mod_host": mod, "illoc_host": illoc,
            "phase3a_strategy": strategy, "selection_features": {k: feats[k] for k in ("overlap", "len_ratio", "edit_blocks")},
        })
    rows, illoc_only = sample_illoc_only(rows, cfg)
    counters["illoc_only_not_sampled"] = illoc_only
    report = {"stage": "prepare", "filters": dict(sorted(counters.items())), "rows": len(rows),
              "rule_sites": dict(Counter(a for r in rows for a in r["eligible_sites"])),
              "graded_sites": dict(Counter(a for r in rows for a, s in r["eligible_sites"].items() if len(s) >= 2)),
              "mod_hosts": sum(bool(r["mod_host"]) for r in rows), "illoc_hosts": sum(bool(r["illoc_host"]) for r in rows),
              "illoc_imperative_hosts": sum(bool(r["illoc_host"] and r["illoc_host"]["imperative_cue"]) for r in rows)}
    return rows, report


def sample_illoc_only(rows: list[dict], cfg: dict) -> tuple[list[dict], int]:
    """Keep every pair with a rule site or a MOD host, and a fixed sample of the rest, deontic-modal hosts first."""
    other = [r for r in rows if r["eligible_sites"] or r["mod_host"]]
    only = pick([r for r in rows if not (r["eligible_sites"] or r["mod_host"])], cfg["seed"], "illoc_only")
    limit = cfg["illoc_only_sample"]
    modal = [r for r in only if r["illoc_host"]["imperative_cue"]][: limit // 2]
    plain = [r for r in only if not r["illoc_host"]["imperative_cue"]][: limit - len(modal)]
    kept = sorted(other + modal + plain, key=lambda r: r["canonical_pair_id"])
    return kept, len(rows) - len(kept)


def score(cfg: dict, rows: list[dict], device: str) -> tuple[list[dict], dict]:
    from phase6_degraded_corpus.src.evaluation.score_mmi_candidates import Checkers
    import torch
    import transformers

    ck = Checkers(cfg, device)
    cleans = [r["clean_simplification"] for r in rows]
    acc = ck.acceptability(cleans)
    nli = ck.nli_probs([r["original"] for r in rows], cleans)
    scores = [{"canonical_pair_id": r["canonical_pair_id"], "acceptability": a, "nli_probabilities": n}
              for r, a, n in zip(rows, acc, nli)]
    tau = round(quantile(acc, 0.10), 8)
    delta = round(quantile(acc, 0.50) - tau, 8)
    resolved = {**cfg, "tau_accept": tau, "delta": delta, "calibration": {
        "rule": "tau = 10th percentile of clean-simplification acceptability; delta = median - tau",
        "basis": f"all {len(acc)} structural candidates (no manual sample exists for this language)",
        "acceptability_kind": cfg["acceptability_kind"],
        "versions": {"torch": torch.__version__, "transformers": transformers.__version__, "python": platform.python_version()}}}
    return scores, resolved


def pick(rows: list[dict], seed: int, tag: str) -> list[dict]:
    return sorted(rows, key=lambda r: stable_key(seed, f"{tag}:{r['canonical_pair_id']}"))


def allocate(cfg: dict, rows: list[dict], scores: dict[str, dict]) -> tuple[dict[str, list[dict]], dict]:
    seed, drops = cfg["seed"], Counter()
    gated = []
    for row in rows:
        s = scores[row["canonical_pair_id"]]
        if s["acceptability"] < cfg["tau_accept"]:
            drops["clean_acceptability"] += 1; continue
        if s["nli_probabilities"]["contradiction"] >= cfg["nli_contradiction_threshold"]:
            drops["clean_contradicts_original"] += 1; continue
        gated.append({**row, "clean_acceptability": s["acceptability"], "clean_nli_probabilities": s["nli_probabilities"]})

    def eligible(task: str, row: dict) -> bool:
        axis, kind = task.split("_")
        if axis in RULE_AXES:
            sites = row["eligible_sites"].get(axis, [])
            return len(sites) >= 2 if kind == "graded" else bool(sites)
        return bool(row["mod_host"] if axis == "MOD" else row["illoc_host"])

    quota = cfg["allocation_quota"]
    used, tasks = set(), {t: [] for t in TASK_ORDER}
    for task in TASK_ORDER:
        ordered = pick([r for r in gated if eligible(task, r)], seed, task)
        if task == "ILLOC_pair":
            # Deontic modals are rare and are the only hosts for an instruction: up to a third of ILLOC, as in English.
            modal = [r for r in ordered if r["illoc_host"]["imperative_cue"]][: quota[task] // 3]
            ordered = modal + [r for r in ordered if r not in modal and not r["illoc_host"]["imperative_cue"]]
        for row in ordered:
            if len(tasks[task]) >= quota[task]:
                break
            if row["canonical_original_id"] in used:
                continue
            used.add(row["canonical_original_id"])
            tasks[task].append(row)
    out = {task: [shape(task, row, seed) for row in values] for task, values in tasks.items()}
    report = {"stage": "allocate", "gate_drops": dict(drops), "gated": len(gated), "tau_accept": cfg["tau_accept"],
              "delta": cfg["delta"], "allocated": {t: len(v) for t, v in out.items()}, "quota": quota,
              "by_corpus": {t: dict(Counter(r["corpus"] for r in v)) for t, v in out.items()}}
    return out, report


def shape(task: str, row: dict, seed: int) -> dict:
    """Give each task the fields its generator expects."""
    axis, kind = task.split("_")
    pid = row["canonical_pair_id"]
    base = {**row, "target_axis": axis, "task": task}
    if axis in RULE_AXES and kind == "graded":
        a, b = sorted(row["eligible_sites"][axis], key=lambda s: stable_key(seed, f"graded:{axis}:{pid}:{s}"))[:2]
        return {**base, "sites": {"A": a, "B": b}}
    if axis == "MOD":
        host = row["mod_host"]
        index = min(host["reorder"], key=lambda i: stable_key(seed, f"{pid}:{i}"))
        return {**base, "operation": "mod_front_heavy", "generator_kind": "llm", "sentences": host["sentences"],
                "target_sentence_index": host["target_sentence_index"], "reorder_index": index, "rule_output": None,
                "plan_status": "ready", "plan_schema": "feats-phase6-mod-graded-plan-v1"}
    if axis == "ILLOC":
        op = "illoc_imperative_swap" if row["illoc_host"]["imperative_cue"] else "illoc_hedge_swap"  # see allocate
        return {**base, "operation": op, "generator_kind": "llm", "plan_status": "ready", "plan_schema": "feats-phase6-mmi-plan-v3"}
    return base


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=("prepare", "score", "allocate"))
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--device", default="cuda")
    args = p.parse_args()
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    out = Path(cfg["output_dir"]); (out / "pools").mkdir(parents=True, exist_ok=True)
    if args.stage == "prepare":
        rows, report = prepare(cfg)
        write_jsonl(out / "pools/structural_candidates.jsonl", rows)
        report["input_sha256"] = {k: hashlib.sha256(Path(cfg[k]).read_bytes()).hexdigest()
                                  for k in ("phase2b_file", "phase3a_candidate_file")}
    elif args.stage == "score":
        scores, resolved = score(cfg, read_jsonl(out / "pools/structural_candidates.jsonl"), args.device)
        write_jsonl(out / "pools/clean_quality_scores.jsonl", scores)
        (out / "checker_config.json").write_text(json.dumps(resolved, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
        report = {"stage": "score", "scored": len(scores), "tau_accept": resolved["tau_accept"], "delta": resolved["delta"]}
    else:
        resolved = json.loads((out / "checker_config.json").read_text(encoding="utf-8"))
        scores = {r["canonical_pair_id"]: r for r in read_jsonl(out / "pools/clean_quality_scores.jsonl")}
        tasks, report = allocate(resolved, read_jsonl(out / "pools/structural_candidates.jsonl"), scores)
        for task, values in tasks.items():
            write_jsonl(out / f"allocation/{task.lower()}.jsonl", values)
    (out / f"pools/report_{args.stage}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
