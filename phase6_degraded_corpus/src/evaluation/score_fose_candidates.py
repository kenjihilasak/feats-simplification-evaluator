#!/usr/bin/env python3
"""Generate, automatically check, and blind the fose_en_v1 audit sample."""

from __future__ import annotations

import argparse
import difflib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import spacy
from wordfreq import zipf_frequency

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl
from phase6_degraded_corpus.src.common.languages import get as language, load_nlp
from phase6_degraded_corpus.src.evaluation.score_mmi_candidates import Checkers
from phase6_degraded_corpus.src.generation.generate_fose_rules import (
    TOKEN_RE, WORD_RE, generate_expl, generate_fluency, generate_omit, generate_syn, tokens,
)

TASK = {
    "FLUENCY": "Introduce one obvious local grammar error while preserving the meaning and every other quality.",
    "OMIT": "Restore one detail that was usefully omitted; it must be unnecessary or too hard for the target reader.",
    "SYN": "Restore one harder Original word or phrase with the same meaning as the simple wording.",
    "EXPL": "Remove one explanation or definition that genuinely helped understanding, changing nothing else.",
}


def edit_count(a: str, b: str) -> int:
    return sum(tag != "equal" for tag, *_ in difflib.SequenceMatcher(None, [x.casefold() for x in tokens(a)], [x.casefold() for x in tokens(b)], autojunk=False).get_opcodes())


def sample_rows(cfg: dict, per_cell: int = 60) -> list[dict]:
    out = []
    for axis in TASK:
        rows = read_jsonl(Path(cfg["output_dir"]) / f"pools/{axis.lower()}.jsonl")
        for corpus in cfg["corpora"]:
            cell = [r for r in rows if r["corpus"] == corpus]
            cell.sort(key=lambda r: stable_key(cfg["seed"], f"audit:{axis}:{r['canonical_pair_id']}"))
            out.extend(cell[:per_cell])
    return out


def generate(rows: list[dict], cfg: dict) -> list[dict]:
    lang = cfg.get("language", "en")
    nlp = load_nlp(lang)
    out = []
    for row in rows:
        axis = row["target_axis"]
        if axis == "FLUENCY":
            result = generate_fluency(row["clean_simplification"], row["canonical_pair_id"], cfg["seed"], nlp, row.get("assigned_error_type"))
        elif axis == "OMIT": result = generate_omit(row["original"], row["clean_simplification"], row["canonical_pair_id"], cfg["seed"], row["eligible_sites"][axis], lang)
        elif axis == "SYN": result = generate_syn(row["original"], row["clean_simplification"], row["canonical_pair_id"], cfg["seed"], row["eligible_sites"][axis], lang)
        else: result = generate_expl(row["original"], row["clean_simplification"], row["canonical_pair_id"], cfg["seed"], row["eligible_sites"][axis], lang)
        out.append({**row, "rule_output": result, "degraded_simplification": result["degraded"] if result else None})
    return out


def score(rows: list[dict], cfg: dict, device: str) -> list[dict]:
    ck = Checkers(cfg, device)
    lang = cfg.get("language", "en")
    nlp = ck.nlp
    valid_rows = [r for r in rows if r.get("degraded_simplification")]
    degraded = [r["degraded_simplification"] for r in valid_rows]
    clean = [r["clean_simplification"] for r in valid_rows]
    original = [r["original"] for r in valid_rows]
    acc = ck.acceptability(degraded)
    cd = ck.nli_probs(clean, degraded); dc = ck.nli_probs(degraded, clean); od = ck.nli_probs(original, degraded)
    features = {r["canonical_pair_id"]: (acc[i], cd[i], dc[i], od[i]) for i, r in enumerate(valid_rows)}
    for row in rows:
        degraded = row.get("degraded_simplification"); axis = row["target_axis"]
        if not degraded:
            row["checks"] = {"generated": False}; row["valid"] = False; continue
        accept, nli_cd, nli_dc, nli_od = features[row["canonical_pair_id"]]
        base = {"generated": True, "not_noop": degraded != row["clean_simplification"]}
        if axis == "FLUENCY":
            checks = {"one_edit_block": edit_count(row["clean_simplification"], degraded) == 1,"acceptability_drop_ge_0.10": accept <= row["clean_acceptability"] - .10,
                      "entails_both_ways": min(nli_cd["entailment"], nli_dc["entailment"]) >= .5}
        elif axis == "OMIT":
            span = " ".join(row["rule_output"]["span"])
            checks = {"inserted_from_original": span.casefold() in row["original"].casefold(),
                      "longer": len(tokens(degraded)) > len(tokens(row["clean_simplification"])),
                      "acceptable": accept >= min(cfg["tau_accept"], row["clean_acceptability"] - cfg["delta"]),
                      "clean_to_degraded_not_contradiction": nli_cd["contradiction"] < .5}
        elif axis == "SYN":
            restored = [x for x in row["rule_output"]["restored"] if WORD_RE.match(x)]
            simple = [x for x in row["rule_output"]["simple_span"] if WORD_RE.match(x)]
            rz = sum(zipf_frequency(x, lang) for x in restored) / max(1, len(restored)); sz = sum(zipf_frequency(x, lang) for x in simple) / max(1, len(simple))
            checks = {"restored_from_original": " ".join(row["rule_output"]["restored"]).casefold() in row["original"].casefold(),
                      "zipf_gap_ge_0.5": rz <= sz - .5,
                      "one_restored_content_word": len([t for t in nlp(" ".join(row["rule_output"]["restored"])) if t.pos_ in {"NOUN", "VERB", "ADJ", "ADV"} and not t.is_stop]) == 1,
                      "different_lemmas": {t.lemma_.casefold() for t in nlp(" ".join(row["rule_output"]["restored"]))}.isdisjoint({t.lemma_.casefold() for t in nlp(" ".join(row["rule_output"]["simple_span"]))}),
                      "entails_both_ways": min(nli_cd["entailment"], nli_dc["entailment"]) >= .5,
                      "acceptable": accept >= min(cfg["tau_accept"], row["clean_acceptability"] - cfg["delta"])}
        else:
            removed = " ".join(row["rule_output"]["removed"])
            checks = {"acceptable": accept >= min(cfg["tau_accept"], row["clean_acceptability"] - cfg["delta"]),
                      "clean_to_degraded_not_contradiction": nli_cd["contradiction"] < .5,
                      "shorter": len(tokens(degraded)) < len(tokens(row["clean_simplification"])),
                      "removed_absent_original": removed.casefold() not in row["original"].casefold()}
        row["features"] = {"acceptability": accept, "nli_clean_degraded": nli_cd, "nli_degraded_clean": nli_dc, "nli_original_degraded": nli_od}
        row["checks"] = {**base, **checks}; row["valid"] = all(row["checks"].values())
    return rows


def build_review(rows: list[dict], cfg: dict, review: Path, key_path: Path) -> None:
    # Audit the automatic-check survivors; if a cell has fewer than 20, use all survivors.
    eligible = [r for r in rows if r["valid"] and r["corpus"] in cfg["corpora"]]
    grouped = defaultdict(list)
    for row in eligible:
        grouped[(row["target_axis"], row["corpus"])].append(row)
    cases = []
    for key, cell in grouped.items():
        cell.sort(key=lambda r: stable_key(cfg["seed"], f"blind:{r['canonical_pair_id']}:{r['target_axis']}"))
        cases.extend(cell[:20])
    cases.sort(key=lambda r: stable_key(cfg["seed"], f"shuffle:{r['canonical_pair_id']}:{r['target_axis']}"))
    lines = ["# FOSE v1 blinded human review", "", "Mark exactly one box per case. **Unsure counts as valid.** Valid means the stated rule was applied correctly and the Degraded text is clearly a worse simplification on that axis, with everything else unchanged.", ""]
    key = {}
    for index, row in enumerate(cases, 1):
        case = f"F{index:03d}"; key[case] = {k: row[k] for k in ("canonical_pair_id", "canonical_original_id", "target_axis", "corpus")}
        lines += [f"### Case {case}", "", f"- **Axis:** `{row['target_axis']}`", f"- **Required change and validity criterion:** {TASK[row['target_axis']]}",
                  f"- **Source:** {row['corpus']}", f"- **Original:** {row['original']}", f"- **Simplified:** {row['clean_simplification']}",
                  f"- **Degraded:** {row['degraded_simplification']}", "", "- [ ] Valid", "- [ ] Invalid", "- [ ] Unsure", "- **Note:**", ""]
    review.parent.mkdir(parents=True, exist_ok=True); review.write_text("\n".join(lines), encoding="utf-8")
    key_path.parent.mkdir(parents=True, exist_ok=True); key_path.write_text(json.dumps(key, indent=2, sort_keys=True) + "\n")


def main():
    p = argparse.ArgumentParser(); p.add_argument("command", choices=("sample", "score", "review")); p.add_argument("--config", type=Path, required=True); p.add_argument("--device", default="cuda"); args = p.parse_args()
    cfg = json.loads(args.config.read_text()); root = Path(cfg["output_dir"]); sample = root / "audit/sample.jsonl"; scored = root / "audit/scored.jsonl"
    if args.command == "sample": write_jsonl(sample, generate(sample_rows(cfg), cfg)); print(len(read_jsonl(sample)))
    elif args.command == "score": write_jsonl(scored, score(read_jsonl(sample), cfg, args.device)); print(dict(Counter((r["target_axis"], r["valid"]) for r in read_jsonl(scored))))
    else:
        build_review(read_jsonl(scored), cfg, Path("phase6_degraded_corpus/docs/reports/current/fose_v1_review.md"), root / "audit/review_key.json")


if __name__ == "__main__": main()
