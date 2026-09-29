#!/usr/bin/env python3
"""Apply the v2 axis checks (plan §3) to every candidate of every config, identically.

C0 raw outputs (frozen v1 scripts) are first converted to the v2 record shape with one
candidate. Each candidate gets its check vector; a row's selected candidate is the first
one (in sample order) that passes every check of its axis/operation.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, write_jsonl
from phase6_degraded_corpus.src.planning.plan_mmi_operations import split_sentences

WORD = re.compile(r"\d+(?:[.,]\d+)*|\w+(?:[-’']\w+)*|[^\w\s]")
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
NEGATION = re.compile(r"\b(?:not|never|no|n't|none|nobody|nothing)\b", re.I)
CONNECTIVES = {
    "and", "but", "or", "so", "because", "while", "whereas", "although", "though", "which", "who",
    "whom", "whose", "where", "when", "that", "this", "these", "those", "it", "he", "she", "they",
    "him", "her", "them", "its", "his", "their", "there", "also", "then", "be", "have", "do",
    "including", "include", "call", "called", "known",
}
QUESTION_START = {
    "is", "are", "was", "were", "do", "does", "did", "has", "have", "had", "can", "could", "will",
    "would", "should", "may", "might", "must", "shall", "who", "what", "when", "where", "which", "why", "how",
}
DIRECTIVE_LEXICON = {
    "note", "that", "remember", "keep", "in", "mind", "consider", "please", "know", "bear", "be",
    "aware", "you", "should", "must", "learn", "understand", "notice", "recall", "take", ",", ":",
}
HEDGE_LEXICON = {
    "might", "may", "could", "possibly", "perhaps", "probably", "likely", "maybe", "it", "is", "was",
    "believed", "thought", "said", "that", "seems", "seem", "seemed", "appears", "appear", "appeared",
    "to", "have", "has", "had", "be", "been", "reportedly", "some", "people", "say", "according",
    "apparently", "presumably", "supposedly", "would", "can", ",",
}
AUXILIARIES = {"is", "are", "was", "were", "be", "been", "has", "have", "had", "do", "does", "did", "will", "can"}


def tokens(text: str) -> list[str]:
    return [t.casefold() for t in WORD.findall(text or "")]


def signature(text: str) -> list[str]:
    return re.findall(r"\w+", (text or "").casefold())


def diff_blocks(a: list[str], b: list[str]) -> list[tuple[str, list[str], list[str]]]:
    ops = difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
    return [(op, a[i1:i2], b[j1:j2]) for op, i1, i2, j1, j2 in ops if op != "equal"]


def overlap(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, tokens(a), tokens(b), autojunk=False).ratio()


class Checkers:
    """NLI, acceptability and spaCy, loaded once."""

    def __init__(self, pools_config: dict, device: str):
        import spacy
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.torch = torch
        self.device = torch.device(device)
        cache = Path(pools_config["cache_dir"]) / "hub"

        def load(model_id: str, revision: str):
            path = cache / f"models--{model_id.replace('/', '--')}" / "snapshots" / revision
            tok = AutoTokenizer.from_pretrained(path, local_files_only=True)
            model = AutoModelForSequenceClassification.from_pretrained(path, local_files_only=True).to(self.device).eval()
            return tok, model

        self.nli_tok, self.nli = load(pools_config["nli_model"], pools_config["nli_revision"])
        self.nli_ids = {k: int(self.nli.config.label2id[k]) for k in ("entailment", "neutral", "contradiction")}
        self.cola_tok, self.cola = load(pools_config["acceptability_model"], pools_config["acceptability_revision"])
        self.nlp = spacy.load("en_core_web_sm")
        self.batch = pools_config.get("checker_batch_size", 64)

    def nli_probs(self, premises: list[str], hypotheses: list[str]) -> list[dict]:
        out = []
        with self.torch.inference_mode():
            for i in range(0, len(premises), self.batch):
                enc = self.nli_tok(premises[i:i + self.batch], hypotheses[i:i + self.batch], padding=True,
                                   truncation=True, max_length=512, return_tensors="pt").to(self.device)
                probs = self.nli(**enc).logits.softmax(-1).float().cpu()
                out += [{k: float(p[idx]) for k, idx in self.nli_ids.items()} for p in probs]
        return out

    def acceptability(self, texts: list[str]) -> list[float]:
        out = []
        with self.torch.inference_mode():
            for i in range(0, len(texts), self.batch):
                enc = self.cola_tok(texts[i:i + self.batch], padding=True, truncation=True,
                                    max_length=512, return_tensors="pt").to(self.device)
                out += self.cola(**enc).logits.softmax(-1)[:, 0].float().cpu().tolist()
        return out

    def content_lemmas(self, text: str) -> set[str]:
        return {
            t.lemma_.casefold() for t in self.nlp(text)
            if t.is_alpha and not t.is_stop and t.lemma_.casefold() not in CONNECTIVES and t.pos_ != "PRON"
        }

    def proper_nouns(self, text: str) -> set[str]:
        return {t.text.casefold() for t in self.nlp(text) if t.pos_ == "PROPN"}


def check_meaning(row, cand, feats, cfg) -> dict:
    blocks = diff_blocks(tokens(row["clean_simplification"]), tokens(cand))
    inserted = [t for _, _, new in blocks for t in new if re.match(r"\w", t)]
    original_tokens = set(tokens(row["original"]))
    checks = {
        "one_edit_block": len(blocks) == 1,
        "contradicts_original": feats["nli_original_degraded"]["contradiction"] >= 0.5,
        "fluency_kept": feats["acceptability"] >= row["clean_acceptability"] - cfg["delta"],
    }
    if row.get("meaning_type") in {"entity", "property"}:
        checks["replacement_not_in_original"] = not inserted or not set(inserted) <= original_tokens
    return checks


def check_mod(row, cand, feats, cfg, ck: Checkers) -> dict:
    clean = row["clean_simplification"]
    lem_c, lem_d = ck.content_lemmas(clean), ck.content_lemmas(cand)
    original_only = ck.content_lemmas(row["original"]) - lem_c
    return {
        "sentence_count_minus_one": len(split_sentences(cand)) == len(split_sentences(clean)) - 1,
        "content_lemmas_within_2": len(lem_c ^ lem_d) <= 2,
        "numbers_identical": sorted(NUMBER.findall(cand)) == sorted(NUMBER.findall(clean)),
        "negation_identical": len(NEGATION.findall(cand)) == len(NEGATION.findall(clean)),
        # Text containment, not POS-set equality: spaCy tags proper nouns inconsistently across rewrites.
        "proper_nouns_kept": all(p in cand.casefold() for p in ck.proper_nouns(clean))
                             and all(p in clean.casefold() for p in ck.proper_nouns(cand)),
        "no_original_leak": not (lem_d - lem_c) & original_only,
        "entails_both_ways": min(feats["nli_clean_degraded"]["entailment"], feats["nli_degraded_clean"]["entailment"]) >= 0.5,
        "acceptable": acceptable_enough(row, feats, cfg),
    }


def acceptable_enough(row: dict, feats: dict, cfg: dict) -> bool:
    """Absolute τ, or no worse than the clean text by more than δ (merges and questions score lower on CoLA)."""
    return feats["acceptability"] >= min(cfg["tau_accept"], row["clean_acceptability"] - cfg["delta"])


def check_illoc(op: str, row, cand, feats, cfg, ck: Checkers) -> dict:
    clean = row["clean_simplification"]
    blocks = diff_blocks(tokens(clean), tokens(cand))
    inserted = [t for _, _, new in blocks for t in new]
    deleted = [t for _, old, _ in blocks for t in old]
    acceptable = acceptable_enough(row, feats, cfg)
    if op == "assertion_to_question":
        first = tokens(cand)[:1]
        return {
            "ends_with_question_mark": cand.rstrip().rstrip('"”').endswith("?"),
            "question_opening": bool(first) and first[0] in QUESTION_START,
            "content_lemmas_within_1": len(ck.content_lemmas(clean) ^ ck.content_lemmas(cand)) <= 1,
            "acceptable": acceptable,
        }
    lexicon = DIRECTIVE_LEXICON if op == "assertion_to_directive" else HEDGE_LEXICON
    return {
        "edit_blocks_le_2": 1 <= len(blocks) <= 2,
        "inserted_in_lexicon": bool(inserted) and set(inserted) <= lexicon,
        "deleted_only_auxiliaries_or_final_punct": set(deleted) <= AUXILIARIES | {".", ","},
        "not_question": not cand.rstrip().endswith("?"),
        "acceptable": acceptable,
    }


def c0_records(path_meaning: Path, path_other: Path, plan: dict[str, dict]) -> list[dict]:
    records = []
    for path, key in ((path_meaning, "distorted_simplification"), (path_other, "degraded_simplification")):
        if not path.exists():
            continue
        for raw in read_jsonl(path):
            row = plan[raw["canonical_pair_id"]]
            degraded = (raw.get("generation") or {}).get(key)
            records.append({
                **{k: row.get(k) for k in ("canonical_pair_id", "canonical_original_id", "corpus", "target_axis", "operation",
                                         "original", "clean_simplification", "clean_acceptability", "meaning_type",
                                         "generator_kind", "target_span", "split")},
                "config_id": "C0", "model": "Qwen/Qwen2.5-7B-Instruct (4-bit NF4, v1 pipeline)",
                "candidates": [{"raw": raw.get("raw_response"), "parsed": raw.get("generation"),
                                "degraded": degraded.strip() if isinstance(degraded, str) else None, "generator": "llm"}],
                "c0_v1_operation": raw.get("assigned_operation") or raw.get("assigned_corruption"),
            })
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generations", type=Path, help="v2 generation file")
    parser.add_argument("--c0-dir", type=Path, help="C0_raw directory (meaning.jsonl, mod_illoc.jsonl)")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--pools-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    cfg = json.loads(args.pools_config.read_text(encoding="utf-8"))
    plan = {row["canonical_pair_id"]: row for row in read_jsonl(args.plan)}
    if args.c0_dir:
        records = c0_records(args.c0_dir / "meaning.jsonl", args.c0_dir / "mod_illoc.jsonl", plan)
    else:
        records = read_jsonl(args.generations)
    ck = Checkers(cfg, args.device)

    flat = [(ri, ci, c["degraded"]) for ri, r in enumerate(records) for ci, c in enumerate(r["candidates"]) if c["degraded"]]
    texts = [d for _, _, d in flat]
    acc = ck.acceptability(texts)
    originals = [records[ri]["original"] for ri, _, _ in flat]
    cleans = [records[ri]["clean_simplification"] for ri, _, _ in flat]
    nli_od = ck.nli_probs(originals, texts)
    nli_cd = ck.nli_probs(cleans, texts)
    nli_dc = ck.nli_probs(texts, cleans)
    feats_by = {(ri, ci): {"acceptability": acc[k], "nli_original_degraded": nli_od[k],
                           "nli_clean_degraded": nli_cd[k], "nli_degraded_clean": nli_dc[k]}
                for k, (ri, ci, _) in enumerate(flat)}

    for ri, row in enumerate(records):
        clean, original = row["clean_simplification"], row["original"]
        for ci, cand in enumerate(row["candidates"]):
            degraded = cand["degraded"]
            if not degraded:
                cand.update({"features": None, "checks": {"parsed": False}, "valid": False})
                continue
            feats = feats_by[(ri, ci)]
            axis = row["target_axis"]
            base = {"parsed": True, "not_noop": signature(degraded) != signature(clean)}
            if axis != "MOD":
                # For MOD, moving toward the Original is the intended effect; no_original_leak covers leaks.
                base["not_copy_original"] = not (signature(degraded) == signature(original)
                                                 or overlap(degraded, original) > overlap(degraded, clean) + 0.1)
            if axis == "MEANING":
                specific = check_meaning(row, degraded, feats, cfg)
            elif axis == "MOD":
                specific = check_mod(row, degraded, feats, cfg, ck)
            else:
                ops = ([row["operation"]] if row.get("config_id") != "C0"
                       else ["assertion_to_question", "assertion_to_directive", "assertion_to_hedged"])
                results = {op: check_illoc(op, row, degraded, feats, cfg, ck) for op in ops}
                # C0 used v1 operations: credit it with the v2 operation it satisfies best.
                best = max(results, key=lambda op: (all(results[op].values()), sum(results[op].values())))
                specific = results[best]
                cand["matched_operation"] = best
            cand["features"] = feats
            cand["checks"] = {**base, **specific}
            cand["valid"] = all(cand["checks"].values())
        valid = [c.get("valid", False) for c in row["candidates"]]
        row["selected_index"] = valid.index(True) if any(valid) else None
        row["check_pass_at_1"] = bool(valid) and valid[0]
        row["yield"] = any(valid)
        row["single_edit"] = _single_edit(row)
    write_jsonl(args.output, records)
    print(json.dumps({"rows": len(records), "yield": sum(r["yield"] for r in records)}, indent=2))


def _single_edit(row: dict) -> bool | None:
    idx = row["selected_index"] if row["selected_index"] is not None else 0
    cand = row["candidates"][idx] if row["candidates"] else None
    if not cand or not cand["degraded"]:
        return None
    if row["target_axis"] == "MOD":
        return cand["checks"].get("sentence_count_minus_one")
    return len(diff_blocks(tokens(row["clean_simplification"]), tokens(cand["degraded"]))) == 1


if __name__ == "__main__":
    main()
