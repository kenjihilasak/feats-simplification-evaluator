#!/usr/bin/env python3
"""Graded OMIT/SYN groups: the clean simplification (1.0), one undone edit (0.5) and two undone edits (0.0).

Each group comes from one pair with at least two eligible rule sites. Sites A and B are checked alone with the
FOSE v2 checks, and the combined text AB is checked for acceptability and NLI. A group is valid only if A, B and
AB all pass. The 0.5 version is A or B, chosen deterministically, so both single edits are reviewed over the sample.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import spacy

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl
from phase6_degraded_corpus.src.evaluation.score_fose_candidates import score
from phase6_degraded_corpus.src.generation.generate_fose_rules import alignment, detokenize, splice
from phase6_degraded_corpus.src.selection.freeze_evaluation_originals import strong_key
from phase6_degraded_corpus.src.selection.select_fose_pools import eligible_rule_sites, structural_features
from phase6_degraded_corpus.src.selection.select_mmi_pools import ReservedMatcher, corpus_of

AXES = ("OMIT", "SYN")


def apply_sites(axis: str, original: str, simple: str, sites: list, lang: str = "en") -> dict:
    """Undo one or more aligned edits, right to left so earlier indices stay valid."""
    left, right, _ = alignment(original, simple)
    tokens = list(right)
    for i1, i2, j1, j2 in sorted(sites, key=lambda s: s[2], reverse=True):
        tokens[j1:(j1 if axis == "OMIT" else j2)] = left[i1:i2]
    first = sites[0]
    if lang == "en":
        degraded = detokenize(tokens)
    else:
        degraded = splice(original, simple, [("insert" if axis == "OMIT" else "replace", site) for site in sites])
    output = {"degraded": degraded, "site": first, "sites": sites}
    if axis == "OMIT":
        output["span"] = left[first[0]:first[1]]
    else:
        output.update({"restored": left[first[0]:first[1]], "simple_span": right[first[2]:first[3]]})
    return output


def excluded(cfg: dict, extra: list[Path]) -> tuple[ReservedMatcher, set[str], ReservedMatcher]:
    reserved = ReservedMatcher(read_jsonl(Path(cfg["reserved_membership_file"])), cfg["near_duplicate_jaccard"])
    ids = {x.strip() for x in Path(cfg["audited_originals_file"]).read_text().splitlines() if x.strip()}
    texts = {r["original"] for f in cfg["audited_split_files"] for r in read_jsonl(Path(f))}
    for path in extra:
        rows = json.loads(path.read_text()) if path.suffix == ".json" else read_jsonl(path)
        ids |= {r["canonical_original_id"] for r in rows if r.get("canonical_original_id")}
    audited = ReservedMatcher([{"strong_key": strong_key(t), "original": t} for t in texts], cfg["near_duplicate_jaccard"])
    return reserved, ids, audited


def candidates(cfg: dict, extra: list[Path]) -> list[dict]:
    reserved, ids, audited = excluded(cfg, extra)
    nlp = spacy.load("en_core_web_sm")
    tag = {"OMIT": "delete", "SYN": "replace"}
    out = []
    for row in read_jsonl(Path(cfg["phase2b_file"])):
        corpus = corpus_of(row)
        if row.get("repaired_duplicate_of") or corpus not in cfg["corpora"]:
            continue
        original, simple = row.get("original", "").strip(), row.get("simple", "").strip()
        if not original or not simple or original.casefold() == simple.casefold():
            continue
        feats = structural_features(original, simple)
        if not cfg["original_token_range"][0] <= len(feats["left"]) <= cfg["original_token_range"][1]:
            continue
        for axis in AXES:
            if sum(op[0] == tag[axis] for op in feats["ops"]) < 2:
                continue
            sites = eligible_rule_sites(axis, feats, nlp)
            if len(sites) < 2:
                continue
            if row["canonical_original_id"] in ids or audited.match(original) or reserved.match(original):
                continue
            pid = row["canonical_pair_id"]
            a, b = sorted(sites, key=lambda s: stable_key(cfg["seed"], f"graded:{axis}:{pid}:{s}"))[:2]
            base = {"canonical_pair_id": pid, "canonical_original_id": row["canonical_original_id"], "corpus": corpus,
                    "original": original, "clean_simplification": simple, "target_axis": axis}
            out.append({**base, "sites": {"A": a, "B": b}})
    return out


def score_groups(groups: list[dict], cfg: dict, device: str) -> list[dict]:
    rows = []
    for g in groups:
        for version, sites in (("A", [g["sites"]["A"]]), ("B", [g["sites"]["B"]]), ("AB", [g["sites"]["A"], g["sites"]["B"]])):
            out = apply_sites(g["target_axis"], g["original"], g["clean_simplification"], sites, cfg.get("language", "en"))
            rows.append({**{k: v for k, v in g.items() if k != "sites"}, "canonical_pair_id": f'{g["canonical_pair_id"]}#{version}',
                         "version": version, "rule_output": out, "degraded_simplification": out["degraded"]})
    # Clean-side features the checks need; computed once per pair.
    from phase6_degraded_corpus.src.evaluation.score_mmi_candidates import Checkers
    ck = Checkers(cfg, device)
    cleans = sorted({g["clean_simplification"] for g in groups})
    acc = dict(zip(cleans, ck.acceptability(cleans)))
    for r in rows:
        r["clean_acceptability"] = acc[r["clean_simplification"]]
    scored = {r["canonical_pair_id"]: r for r in score(rows, cfg, device)}
    for g in groups:
        pid = g["canonical_pair_id"]
        versions = {v: scored[f"{pid}#{v}"] for v in ("A", "B", "AB")}
        g["versions"] = {v: {"degraded": r["degraded_simplification"], "checks": r.get("checks"), "valid": r.get("valid", False),
                              "features": r.get("features")} for v, r in versions.items()}
        g["clean_acceptability"] = acc[g["clean_simplification"]]
        g["valid"] = all(r.get("valid", False) for r in versions.values()) and versions["AB"]["degraded_simplification"] not in {
            versions["A"]["degraded_simplification"], versions["B"]["degraded_simplification"]}
        g["mild_version"] = "A" if int(stable_key(cfg["seed"], f"mild:{pid}"), 16) % 2 == 0 else "B"
    return groups


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--exclude", type=Path, action="append", default=[], help="files with canonical_original_id to keep unseen")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--device", default="cuda")
    args = p.parse_args()
    cfg = json.loads(args.config.read_text())
    groups = score_groups(candidates(cfg, args.exclude), cfg, args.device)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output, groups)
    print(json.dumps({"groups": dict(Counter(g["target_axis"] for g in groups)),
                      "valid": dict(Counter(g["target_axis"] for g in groups if g["valid"]))}, indent=2))


if __name__ == "__main__":
    main()
