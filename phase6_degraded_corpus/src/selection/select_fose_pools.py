#!/usr/bin/env python3
"""Select independent FLUENCY/OMIT/SYN/EXPL pools for fose_en_v1."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import spacy
from wordfreq import zipf_frequency

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl
from phase6_degraded_corpus.src.common.languages import get as language, stop_words
from phase6_degraded_corpus.src.generation.generate_fose_rules import (
    WORD_RE, alignment, detokenize, explanatory_pattern, fluency_sites, span_is_balanced,
)
from phase6_degraded_corpus.src.selection.select_mmi_pools import ReservedMatcher, corpus_of
from phase6_degraded_corpus.src.selection.freeze_evaluation_originals import strong_key

AXES = ("FLUENCY", "OMIT", "SYN", "EXPL")


def content(tokens: list[str], lang: str = "en") -> list[str]:
    stops = stop_words(lang)
    return [t for t in tokens if WORD_RE.match(t) and t.casefold() not in stops]


def structural_features(original: str, simple: str) -> dict:
    left, right, ops = alignment(original, simple)
    edits = [(tag, i1, i2, j1, j2) for tag, i1, i2, j1, j2 in ops if tag != "equal"]
    return {"left": left, "right": right, "ops": edits, "overlap": 2 * sum(i2 - i1 for tag, i1, i2, _, _ in ops if tag == "equal") / max(1, len(left) + len(right)),
            "len_ratio": len(right) / max(1, len(left)), "edit_blocks": len(edits)}


def _analysed(items: list[str], nlp, lang: str = "en") -> list:
    return list(nlp(detokenize(items, lang)))


def _content(doc) -> list:
    return [t for t in doc if t.pos_ in {"NOUN", "VERB", "ADJ", "ADV"} and not t.is_stop]


def eligible_rule_sites(axis: str, feats: dict, nlp=None, lang: str = "en") -> list:
    max_edit_blocks = 8 if axis == "EXPL" else 4
    if not (feats["overlap"] >= .4 and .5 <= feats["len_ratio"] <= 1.6 and feats["edit_blocks"] <= max_edit_blocks):
        return []
    sites = []
    for tag, i1, i2, j1, j2 in feats["ops"]:
        old, new = feats["left"][i1:i2], feats["right"][j1:j2]
        site = (i1, i2, j1, j2)
        old_doc = _analysed(old, nlp, lang) if nlp is not None else None
        new_doc = _analysed(new, nlp, lang) if nlp is not None else None
        if axis == "OMIT" and tag == "delete" and 2 <= len(old) <= 12 and span_is_balanced(old):
            old_content = _content(old_doc) if old_doc is not None else content(old, lang)
            simple_lemmas = ({t.lemma_.casefold() for t in _analysed(feats["right"], nlp, lang) if WORD_RE.match(t.text)}
                             if nlp is not None else {t.casefold() for t in feats["right"] if WORD_RE.match(t)})
            if any((t.lemma_.casefold() if old_doc is not None else t.casefold()) not in simple_lemmas for t in old_content):
                sites.append(site)
        elif axis == "SYN" and tag == "replace" and 1 <= len(old) <= 2 and 1 <= len(new) <= 3 and all(WORD_RE.match(x) for x in old + new):
            old_content = _content(old_doc) if old_doc is not None else content(old, lang)
            new_content = _content(new_doc) if new_doc is not None else content(new, lang)
            proper_or_number = (any(t.pos_ == "PROPN" or t.like_num for t in old_doc + new_doc)
                                if old_doc is not None else any(any(ch.isdigit() for ch in x) for x in old + new))
            old_lemmas = {t.lemma_.casefold() for t in old_content} if old_doc is not None else {t.casefold() for t in old_content}
            new_lemmas = {t.lemma_.casefold() for t in new_content} if new_doc is not None else {t.casefold() for t in new_content}
            if len(old_content) == 1 and new_content and not proper_or_number and old_lemmas.isdisjoint(new_lemmas):
                old_zipf = sum(zipf_frequency(t.text if old_doc is not None else t, lang) for t in old_content) / len(old_content)
                new_zipf = sum(zipf_frequency(t.text if new_doc is not None else t, lang) for t in new_content) / len(new_content)
                if old_zipf <= new_zipf - .5:
                    sites.append(site)
        elif axis == "EXPL" and tag == "insert" and len(new) >= 2 and content(new, lang):
            pattern = explanatory_pattern(feats["right"][:j1], new, feats["right"][j2:], lang)
            original_cf = {x.casefold() for x in feats["left"] if WORD_RE.match(x)}
            gloss_cf = {x.casefold() for x in content(new, lang)}
            term = next((x.casefold() for x in reversed(feats["right"][:j1]) if WORD_RE.match(x)), None)
            factual = any(any(ch.isdigit() for ch in x) for x in new)
            if nlp is not None:
                # Spanish/French spaCy has no numeric entity types; digits cover them above.
                factual = factual or any(t.ent_type_ in language(lang).entity_types_factual
                                         or (t.ent_type_ and t.text.casefold() not in original_cf) for t in new_doc)
            if pattern and term in original_cf and not gloss_cf.issubset(original_cf) and not factual:
                sites.append(site)
    if axis == "OMIT" and any(tag == "insert" for tag, *_ in feats["ops"]):
        return []
    return sites


def check_validated(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    text = json.dumps(data).casefold()
    if "fail" in text or not any(token in text for token in ('"valid": true', '"status": "validated"', '"passed": true')):
        raise RuntimeError(f"STOP: Phase 3a candidate set is not validated: {path}")


def build_structural(cfg: dict) -> tuple[list[dict], dict]:
    check_validated(Path(cfg["phase3a_validation_file"]))
    phase3 = {r["canonical_pair_id"]: r for r in read_jsonl(Path(cfg["phase3a_candidate_file"]))}
    reserved = ReservedMatcher(read_jsonl(Path(cfg["reserved_membership_file"])), cfg["near_duplicate_jaccard"])
    audited = {x.strip() for x in Path(cfg["audited_originals_file"]).read_text().splitlines() if x.strip()}
    audited_texts = {row["original"] for filename in cfg["audited_split_files"] for row in read_jsonl(Path(filename))}
    audited_matcher = ReservedMatcher(
        [{"strong_key": strong_key(text), "original": text} for text in audited_texts],
        cfg["near_duplicate_jaccard"],
    )
    mmi = {r["canonical_pair_id"] for r in read_jsonl(Path(cfg["mmi_allocation_file"]))}
    nlp = spacy.load("en_core_web_sm", disable=["ner"])
    counters = Counter()
    by_axis_source = defaultdict(Counter)
    output = []
    for row in read_jsonl(Path(cfg["phase2b_file"])):
        counters["input"] += 1
        corpus = corpus_of(row)
        if row.get("repaired_duplicate_of") or corpus not in cfg["corpora"]:
            counters["duplicate_or_corpus"] += 1; continue
        original, simple = row.get("original", "").strip(), row.get("simple", "").strip()
        if not original or not simple or original.casefold() == simple.casefold():
            counters["empty_or_identical"] += 1; continue
        audited_hit = audited_matcher.match(original)
        if row["canonical_original_id"] in audited or audited_hit:
            kind = audited_hit["type"] if audited_hit else "id"
            counters[f"audited_original_{kind}"] += 1; continue
        if reserved.match(original):
            counters["reserved_original"] += 1; continue
        f = structural_features(original, simple)
        if not cfg["original_token_range"][0] <= len(f["left"]) <= cfg["original_token_range"][1]:
            counters["original_length"] += 1; continue
        axes, sites, error_types = [], {}, []
        fs = fluency_sites(simple, nlp)
        error_types = [k for k, value in fs.items() if value]
        if error_types:
            axes.append("FLUENCY")
        p3 = phase3.get(row["canonical_pair_id"])
        if p3:
            axis = p3["candidate_strategy_code"]
            if axis in {"OMIT", "SYN", "EXPL"}:
                found = eligible_rule_sites(axis, f, nlp)
                if found:
                    axes.append(axis); sites[axis] = found
        if not axes:
            counters["no_rule_site"] += 1; continue
        for axis in axes:
            by_axis_source[(axis, corpus)]["structural"] += 1
        output.append({"schema": "feats-phase6-fose-pool-candidate-v1", "canonical_pair_id": row["canonical_pair_id"],
            "canonical_original_id": row["canonical_original_id"], "language": "en", "original": original,
            "clean_simplification": simple, "original_raw": row.get("original_raw"), "clean_simplification_raw": row.get("simple_raw"),
            "glue_repaired": bool(row.get("text_repaired")), "source": row["corpora"][0].get("source"), "corpus": corpus,
            "eligible_axes": axes, "eligible_sites": sites, "fluency_error_types": error_types,
            "phase3a": ({k: p3.get(k) for k in ("candidate_strategy_code", "quality_tier", "supporting_models", "confirmation_count")} if p3 else None),
            "also_in_mmi": row["canonical_pair_id"] in mmi, "selection_features": {k: f[k] for k in ("overlap", "len_ratio", "edit_blocks")}})
    report = {"schema": "feats-phase6-fose-pool-report-v1", "experiment_id": cfg["experiment_id"], "stage": "structural",
              "filters": dict(sorted(counters.items())), "cells": {f"{a}|{s}": dict(c) for (a, s), c in sorted(by_axis_source.items())},
              "structural_union": len(output)}
    return output, report


def finalize(cfg: dict, rows: list[dict], scores: dict[str, dict]) -> tuple[dict[str, list[dict]], dict]:
    pools = {a: [] for a in AXES}; drops = defaultdict(Counter)
    for row in rows:
        if row["corpus"] not in cfg["corpora"]:
            for axis in row["eligible_axes"]:
                drops[axis]["source_excluded"] += 1
            continue
        score = scores.get(row["canonical_pair_id"])
        if score is None: raise ValueError(f"missing clean score: {row['canonical_pair_id']}")
        for axis in row["eligible_axes"]:
            if score["acceptability"] < cfg["tau_accept"]: drops[axis]["acceptability"] += 1; continue
            if score["nli_probabilities"]["contradiction"] >= cfg["nli_contradiction_threshold"]: drops[axis]["nli_contradiction"] += 1; continue
            pools[axis].append({**row, "target_axis": axis, "clean_acceptability": score["acceptability"],
                                "clean_nli_probabilities": score["nli_probabilities"]})
    non_fluency_max = max(
        [len(pools[a]) for a in ("OMIT", "SYN", "EXPL")]
        + list(cfg["existing_axis_pair_counts"].values())
    )
    if len(pools["FLUENCY"]) > non_fluency_max:
        groups = defaultdict(list)
        for row in pools["FLUENCY"]:
            kind = min(row["fluency_error_types"], key=lambda k: stable_key(cfg["seed"], row["canonical_pair_id"] + k))
            row["assigned_error_type"] = kind; groups[(row["corpus"], kind)].append(row)
        ordered = []
        for values in groups.values(): values.sort(key=lambda r: stable_key(cfg["seed"], r["canonical_pair_id"]))
        keys = sorted(groups); i = 0
        while len(ordered) < non_fluency_max and keys:
            key = keys[i % len(keys)]
            if groups[key]: ordered.append(groups[key].pop(0))
            if not groups[key]: keys.remove(key); i = 0
            else: i += 1
        drops["FLUENCY"]["cap"] = len(pools["FLUENCY"]) - len(ordered); pools["FLUENCY"] = ordered
    for axis in AXES: pools[axis].sort(key=lambda r: r["canonical_pair_id"])
    cells = {}
    for axis, values in pools.items():
        for corpus in cfg["corpora"]:
            cell = [r for r in values if r["corpus"] == corpus]
            cells[f"{axis}|{corpus}"] = {"records": len(cell), "also_in_mmi": sum(r["also_in_mmi"] for r in cell)}
    return pools, {"schema": "feats-phase6-fose-pool-report-v1", "experiment_id": cfg["experiment_id"], "stage": "quality_gated",
                   "quality": {"models": {"nli": [cfg["nli_model"], cfg["nli_revision"]], "acceptability": [cfg["acceptability_model"], cfg["acceptability_revision"]]},
                               "tau_accept": cfg["tau_accept"], "nli_contradiction_threshold": cfg["nli_contradiction_threshold"]},
                   "wordfreq_version": cfg["wordfreq_version"], "cells": cells,
                   "axis_totals": {a: len(v) for a, v in pools.items()}, "drop_reasons": {a: dict(c) for a, c in drops.items()}}


def main():
    p = argparse.ArgumentParser(); p.add_argument("--config", type=Path, required=True); p.add_argument("--stage", choices=("prepare", "finalize"), required=True); args = p.parse_args()
    cfg = json.loads(args.config.read_text()); out = Path(cfg["output_dir"]); (out / "pools").mkdir(parents=True, exist_ok=True)
    if args.stage == "prepare":
        rows, report = build_structural(cfg); write_jsonl(out / "pools/structural_candidates.jsonl", rows)
        (out / "pools/pool_report_pre_quality.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    else:
        rows = read_jsonl(out / "pools/structural_candidates.jsonl"); scores = {r["canonical_pair_id"]: r for r in read_jsonl(out / "pools/clean_quality_scores.jsonl")}
        pools, report = finalize(cfg, rows, scores)
        for axis, values in pools.items(): write_jsonl(out / f"pools/{axis.lower()}.jsonl", values)
        report["input_sha256"] = {k: hashlib.sha256(Path(cfg[k]).read_bytes()).hexdigest() for k in ("phase2b_file", "phase3a_candidate_file")}
        (out / "pool_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        (out / "pools/pool_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    summary = report["axis_totals"] if "axis_totals" in report else {"structural_union": report["structural_union"]}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__": main()
