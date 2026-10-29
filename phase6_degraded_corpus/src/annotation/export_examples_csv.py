#!/usr/bin/env python3
"""Export a sample of a Phase 6 v2 corpus as an examples CSV for choosing review items.

Same columns as the v1 file (`runs/annotation_v1/s1_en_examples_2026-10-22.csv`) plus `version`: one row per non-clean
version of each sampled case, for all seven FEATS axes.
- OMIT, SYN, EXPL, MOD, ILLOC come from `final/phase6_corpus.jsonl`; graded OMIT/SYN groups are preferred over pairs,
  and ILLOC cases are interleaved by operation, preferring those with a control.
- MEANING and FLUENCY come from the group files, which keep the rule of each version; one version per level, groups
  with the most levels first.
`--exclude` lists faulty degradations found in review: `{"AXIS|canonical_pair_id": reason}` skips a case (the next one
takes its place), `{"AXIS|canonical_pair_id|version": reason}` drops one version. Errors already in the corpus (Original
or human simplification) are not excluded. Cases with the same clean text are shown once.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl

AXES = {"MEANING": "Meaning", "FLUENCY": "Fluency", "OMIT": "Omission", "SYN": "Synonymy", "EXPL": "Explanation",
        "MOD": "Modulation", "ILLOC": "Illocution"}
FORMAT = {"pair": "pair", "graded": "rank3"}
DESCRIPTION = {
    ("OMIT", "degraded"): "one omitted detail restored from the original",
    ("OMIT", "mild"): "one omitted detail restored from the original",
    ("OMIT", "strong"): "two omitted details restored from the original",
    ("SYN", "degraded"): "one harder word restored from the original",
    ("SYN", "mild"): "one harder word restored from the original",
    ("SYN", "strong"): "two harder words restored from the original",
    ("EXPL", "degraded"): "explanation added by the simplification removed",
    ("MOD", "mild"): "secondary information moved to the start of a sentence (LLM)",
    ("MOD", "strong"): "secondary information fronted and dependent sentences swapped (LLM)",
    ("ILLOC", "illoc_directive_to_impersonal"): "direct instruction turned into an impersonal statement (LLM)",
    ("ILLOC", "illoc_question_to_indirect"): "direct question turned into an embedded question (LLM)",
    ("ILLOC", "illoc_address_to_impersonal"): "address to the reader ('you') made impersonal (LLM)",
    ("ILLOC", "paraphrase"): "control: reworded, act kept direct (LLM)",
}
MEANING_RULES = {
    "adverb_also": "redundant 'also' removed; meaning kept",
    "adjective": "an adjective deleted",
    "appositive": "an appositive deleted",
    "adverb": "an adverb deleted",
    "prepositional_adjunct": "a peripheral phrase deleted",
    "peripheral_oblique": "a peripheral phrase deleted",
    "drop_relative_clause": "a relative clause deleted",
    "relative_clause": "a relative clause deleted",
    "drop_coordinated_clause": "a coordinated clause deleted",
    "final_coordinated_clause": "a coordinated clause deleted",
    "generalize_year": "a date made vaguer",
    "intensifier": "an intensifier deleted",
    "intensifier_very": "an intensifier deleted",
    "intensifier_just": "an intensifier deleted",
    "drop_sentence": "a whole sentence deleted",
    "llm_contradict": "a fact contradicted (LLM, confirmed by NLI)",
    "number_changed": "a number changed (contradiction)",
    "year_changed": "a year changed (contradiction)",
}
FLUENCY_EDITS = {"determiner_drop": "article dropped", "preposition_swap": "wrong preposition",
                 "agreement": "agreement broken", "word_order": "two words swapped"}
LEVELS = {"MEANING": ("neutral_trim", "mild_loss", "major_loss", "contradiction"),
          "FLUENCY": ("minor", "major", "severe")}
COLUMNS = ("case_id", "dataset", "feats_axis", "item_format", "source", "human_simplification", "automatic_degradation",
           "degradation_operation", "operation_description", "target_score", "version", "canonical_pair_id")


def operation(r: dict, version: str) -> str:
    if version == "paraphrase":
        return "illoc_direct_paraphrase"
    if r["axis"] == "MOD":
        return "mod_front_heavy" if version == "mild" else "mod_front_heavy+mod_sentence_reorder"
    return r["operation"] if r["format"] == "pair" else f"{r['operation']}:{version}"


def corpus_case(r: dict) -> dict:
    versions = []
    for version, text in r["versions"].items():
        if version == "clean":
            continue
        key = (r["axis"], version)
        if r["axis"] == "ILLOC":
            key = ("ILLOC", "paraphrase" if version == "paraphrase" else r["operation"])
        versions.append((version, text, r["scores"][version], operation(r, version), DESCRIPTION[key]))
    return {"axis": r["axis"], "format": r["format"], "corpus": r["corpus"], "original": r["original"],
            "clean": r["versions"]["clean"], "pair": r["canonical_pair_id"], "operation": r["operation"], "versions": versions}


def group_case(g: dict, axis: str) -> dict:
    by_level = {}
    for m in g["members"]:
        if m["level"] in LEVELS[axis] and m["level"] not in by_level:
            by_level[m["level"]] = m
    versions = []
    for level in LEVELS[axis]:
        m = by_level.get(level)
        if not m:
            continue
        if axis == "MEANING":
            rule = m.get("rule") or ("llm_contradict" if level == "contradiction" else "")
            desc = MEANING_RULES.get(rule, rule) + (f": \"{m['removed']}\"" if m.get("removed") else "")
            op = f"meaning_{rule}"
        else:
            edits = m.get("edits", [])
            desc = f"{level} fluency error: " + ", ".join(FLUENCY_EDITS.get(e, e) for e in edits)
            op = "fluency_" + "+".join(edits)
        versions.append((level, m["text"], m["target_score"], op, desc))
    clean = next(m["text"] for m in g["members"] if m["level"] == "clean")
    return {"axis": axis, "format": "graded", "corpus": g["corpus"], "original": g["original"], "clean": clean,
            "pair": g["canonical_pair_id"], "operation": f"{axis.lower()}_graded", "versions": versions}


def reviewed(c: dict, excluded: set[str]) -> dict | None:
    """The case without its excluded versions; None if the case is excluded or has no degradation left."""
    key = f"{c['axis']}|{c['pair']}"
    if key in excluded:
        return None
    versions = [v for v in c["versions"] if f"{key}|{v[0]}" not in excluded]
    return {**c, "versions": versions} if any(v[2] < 1.0 for v in versions) else None


def sample(cases: list[dict], per_axis: int, seed: int, excluded: set[str]) -> list[dict]:
    by_axis, seen = defaultdict(list), set()
    for c in filter(None, (reviewed(c, excluded) for c in cases)):
        if (c["axis"], c["clean"]) not in seen:  # PaCCSS-IT repeats sentences ("Questo è un tuo problema.")
            seen.add((c["axis"], c["clean"]))
            by_axis[c["axis"]].append(c)
    picked = []
    for axis in AXES:
        pool = by_axis[axis][:]
        random.Random(f"{seed}:{axis}").shuffle(pool)  # one stream per axis: an exclusion in one axis leaves the others as reviewed
        if axis == "ILLOC":
            by_op = defaultdict(list)
            for c in sorted(pool, key=lambda c: all(v[0] != "paraphrase" for v in c["versions"])):
                by_op[c["operation"]].append(c)
            queues, pool = list(by_op.values()), []
            while any(queues):
                pool += [q.pop(0) for q in queues if q]
        elif axis in LEVELS:
            pool.sort(key=lambda c: -len(c["versions"]))
        else:
            pool.sort(key=lambda c: c["format"] != "graded")
        picked += pool[:per_axis]
    return picked


def csv_rows(cases: list[dict], lang: str) -> list[dict]:
    out = []
    for n, c in enumerate(cases, 1):
        for version, text, score, op, desc in c["versions"]:
            out.append({"case_id": f"{lang.upper()}-S{n:03d}", "dataset": c["corpus"], "feats_axis": AXES[c["axis"]],
                        "item_format": FORMAT[c["format"]], "source": c["original"], "human_simplification": c["clean"],
                        "automatic_degradation": text, "degradation_operation": op, "operation_description": desc,
                        "target_score": score, "version": version, "canonical_pair_id": c["pair"]})
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--meaning-groups", type=Path, help="default: <run-dir>/scored/meaning_groups.jsonl")
    p.add_argument("--fluency-groups", type=Path, help="default: <run-dir>/scored/fluency_groups.jsonl")
    p.add_argument("--exclude", type=Path)
    p.add_argument("--per-axis", type=int, default=60)
    p.add_argument("--seed", type=int, default=20261029)
    args = p.parse_args()
    lang = args.run_dir.name.split("_")[1]
    cases = [corpus_case(r) for r in read_jsonl(args.run_dir / "final/phase6_corpus.jsonl")
             if r["axis"] not in LEVELS]
    for axis, path in (("MEANING", args.meaning_groups), ("FLUENCY", args.fluency_groups)):
        path = path or args.run_dir / f"scored/{axis.lower()}_groups.jsonl"
        cases += [group_case(g, axis) for g in read_jsonl(path)]
    excluded = set(json.loads(args.exclude.read_text(encoding="utf-8"))) if args.exclude and args.exclude.exists() else set()
    picked = sample(cases, args.per_axis, args.seed, excluded)
    rows = csv_rows(picked, lang)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:  # the BOM makes Excel/Outlook read UTF-8 ("l’aiuto", not "lâ€™aiuto")
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    counts = defaultdict(int)
    for c in picked:
        counts[c["axis"]] += 1
    print(args.output, len(picked), "cases", len(rows), "rows", dict(counts))


if __name__ == "__main__":
    main()
