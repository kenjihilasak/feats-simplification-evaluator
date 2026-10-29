#!/usr/bin/env python3
"""Build a language's Phase 6 pools: rule sites, checker scores and one task per original.

`prepare` (CPU) reads the language's Phase 2b file and records, per pair, the OMIT/SYN/EXPL rule sites and
whether it can host a MOD or ILLOC edit. `score` (GPU) scores every clean simplification with the language's
checkers and calibrates the acceptability thresholds the way the English ones were set (τ = 10th percentile of
clean texts, δ = median − τ), writing `checker_config.json` for every later step. `allocate` (CPU) applies the
clean-quality gates and gives each original at most one task, scarcest task first, so no original appears in two
S1 items.

Tasks: OMIT and SYN graded groups (two rule sites), SYN, OMIT and EXPL pairs, MOD graded groups (a long sentence
for LLM fronting plus a dependent sentence pair for the reorder rule) and ILLOC pairs.

ILLOC v4 (28 Oct 2026): Illocution is how directly a sentence expresses its communicative purpose, so the
degradation keeps the purpose and makes it less direct. Only a sentence that already performs a direct act on the
reader can host it: an instruction, a question to the reader, or a statement that addresses the reader ("you").
Encyclopedic statements have no such act and host no ILLOC item. The v3 operations (statement -> imperative, which
reviewers judged an improvement, and hedging, which changes meaning) are retired.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import json
import platform
from collections import Counter, defaultdict
from itertools import zip_longest
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl
from phase6_degraded_corpus.src.common.languages import get as language, is_imperative_root, is_second_person, load_nlp, stop_words
from phase6_degraded_corpus.src.planning.plan_mmi_operations import _dependent_second, split_sentences
from phase6_degraded_corpus.src.selection.freeze_evaluation_originals import strong_key
from phase6_degraded_corpus.src.selection.select_fose_pools import check_validated, eligible_rule_sites, structural_features
from phase6_degraded_corpus.src.selection.select_mmi_pools import ReservedMatcher, corpus_of

RULE_AXES = ("OMIT", "SYN", "EXPL")
# Scarcest first: an original goes to the first task it can serve.
TASK_ORDER = ("ILLOC_pair", "EXPL_pair", "SYN_graded", "OMIT_graded", "SYN_pair", "OMIT_pair", "MOD_graded")
ILLOC_OPERATIONS = {"directive": "illoc_directive_to_impersonal", "question": "illoc_question_to_indirect",
                    "address": "illoc_address_to_impersonal"}
QUOTED = re.compile(r'"[^"]*"|“[^”]*”|«[^»]*»|„[^“”]*[“”]')


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


def title_like(sentence: str, kind: str, lang: str) -> bool:
    """The act word belongs to a capitalised name or title, not to the text: "Let It Bleed is a 1969 album",
    "Rise Against formed in 1999", "Mad About You is an American situation comedy" (English v2 examples). A
    capitalised function word after the verb marks a title; a name ("Visit London") does not."""
    words = re.findall(r"\w+(?:['’]\w+)?", sentence)
    if len(words) < 2:
        return False
    capital = lambda w: w[:1].isupper() and w != "I"
    if kind == "directive":
        return capital(words[1]) and words[1].lower() in stop_words(lang)
    if kind == "address" and lang == "en":
        for i, w in enumerate(words):
            if language(lang).second_person.fullmatch(w):
                return (i == 0 and capital(words[1])) or (i > 0 and capital(w))
    return False


def illoc_host(simple: str, lang: str, nlp) -> dict | None:
    """The first sentence that performs a direct act on the reader, outside quotations and titles.

    Directive: an imperative root. Question: a sentence of four or more words ending in a question mark.
    Address: a statement with a second-person word. Quoted text is blanked first, so "Curb Your Enthusiasm" or a
    cited slogan does not count.
    """
    sentences = split_sentences(simple, lang)
    addresses_reader = bool(language(lang).second_person.search(QUOTED.sub(" ", simple)))
    found = []
    for i, sentence in enumerate(sentences):
        bare = QUOTED.sub(lambda m: " " * len(m.group(0)), sentence).strip()
        if len(bare.split()) < 4:
            continue
        doc = nlp(bare if lang in {"en", "ru", "ar"} else bare[:1].lower() + bare[1:])
        if bare.rstrip().endswith(tuple(language(lang).question_marks)):
            found.append(("question", i))
        elif is_imperative_root(doc, lang, addresses_reader) and not title_like(bare, "directive", lang):
            found.append(("directive", i))
        elif is_second_person(doc, bare, lang) and not title_like(bare, "address", lang):
            found.append(("address", i))
    if not found:
        return None
    kind, index = found[0]
    return {"kind": kind, "sentences": sentences, "target_sentence_index": index}


def prepare(cfg: dict) -> tuple[list[dict], dict]:
    lang = cfg["language"]
    res = language(lang)
    nlp = load_nlp(lang, disable=("ner",))  # as in English pool selection
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
        # In narrative corpora a second person or a question is a character speaking, not the text addressing its reader.
        illoc = None if corpus in cfg.get("illoc_excluded_corpora", ()) else illoc_host(simple, lang, nlp)
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
    report = {"stage": "prepare", "filters": dict(sorted(counters.items())), "rows": len(rows),
              "rule_sites": dict(Counter(a for r in rows for a in r["eligible_sites"])),
              "graded_sites": dict(Counter(a for r in rows for a, s in r["eligible_sites"].items() if len(s) >= 2)),
              "mod_hosts": sum(bool(r["mod_host"]) for r in rows),
              "illoc_hosts": dict(Counter(r["illoc_host"]["kind"] for r in rows if r["illoc_host"]))}
    return rows, report


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
            # Interleave the three kinds so the rarer acts (directives, questions) are not crowded out by "you".
            by_kind = {k: [r for r in ordered if r["illoc_host"]["kind"] == k] for k in ILLOC_OPERATIONS}
            ordered = [r for group in zip_longest(*by_kind.values()) for r in group if r is not None]
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
        host = row["illoc_host"]
        return {**base, "operation": ILLOC_OPERATIONS[host["kind"]], "generator_kind": "llm", "sentences": host["sentences"],
                "target_sentence_index": host["target_sentence_index"], "plan_status": "ready",
                "plan_schema": "feats-phase6-mmi-plan-v4"}
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
