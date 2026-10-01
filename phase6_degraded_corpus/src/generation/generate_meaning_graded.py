#!/usr/bin/env python3
"""Graded MEANING groups (MEANING recipe v2, plan §2): rules only, no LLM.

`candidates` (CPU): for every base pair build candidate texts per level.
`score` (GPU): acceptability of every candidate and NLI(clean -> candidate).
`select` (CPU): keep, per level, the first candidate (stable order) passing its checks,
and write one group per pair: original_copy, clean, neutral_trim, mild_loss, major_loss,
contradiction (each when available), with target scores.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl
from phase6_degraded_corpus.src.planning.plan_mmi_operations import fix_articles, split_sentences

TARGETS = {"original_copy": 1.0, "clean": 1.0, "neutral_trim": 1.0, "mild_loss": 0.67, "major_loss": 0.33, "contradiction": 0.0}
# v2.1 mapping from the human review (2026-10-01): "very"/"really" lose meaning -> mild.
NEUTRAL_WORDS = {"also", "just"}
NON_CONTENT_ADV = {"not", "never", "also", "very", "really", "just", "only", "even", "then", "so", "too", "however", "n't"}
CONTENT_POS = {"NOUN", "PROPN", "ADJ", "NUM", "VERB", "ADV"}
WORD = re.compile(r"\w+(?:[-’']\w+)*")


def tidy(text: str) -> str:
    text = re.sub(r"\(\s*[,;]?\s*\)", "", text)
    text = re.sub(r"\s+([,.;:!?)])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r",\s*([.;:!?])", r"\1", text)
    text = re.sub(r"^\s*[,;]\s*", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return fix_articles(text)


def delete_span(text: str, start: int, end: int) -> str:
    return tidy(text[:start] + " " + text[end:])


def neutral_trims(text: str) -> list[dict]:
    out = []
    for m in re.finditer(r"\s*\((?:\s*[;,]\s*)*\)|\s*\(\s*/[^)]*/\s*\)", text):
        out.append({"rule": "empty_or_pronunciation_parenthetical", "text": tidy(text[:m.start()] + text[m.end():])})
    for m in re.finditer(r"\b(also|just)\b\s*", text, re.I):
        if m.group(1).lower() in NEUTRAL_WORDS:
            out.append({"rule": f"adverb_{m.group(1).lower()}", "text": tidy(text[:m.start()] + text[m.end():])})
    return out


def subtree_span(token) -> tuple[int, int]:
    tokens = list(token.subtree)
    return tokens[0].idx, tokens[-1].idx + len(tokens[-1].text)


def has_content(span) -> bool:
    return any(t.pos_ in CONTENT_POS and t.lower_ not in NON_CONTENT_ADV for t in span)


def mild_losses(doc) -> list[dict]:
    text, out = doc.text, []
    for m in re.finditer(r"\b(very|really)\b\s*", text, re.I):
        out.append({"rule": f"intensifier_{m.group(1).lower()}", "removed": m.group(1), "text": tidy(text[:m.start()] + text[m.end():])})
    out += [c for c in clause_and_year_losses(doc, text)]
    for tok in doc:
        if tok.dep_ == "appos":
            start, end = subtree_span(tok)
            before, after = text[:start].rstrip(), text[end:].lstrip()
            if before.endswith(",") and (after.startswith(",") or after[:1] in {".", ""}):
                cut_start = len(before) - 1
                cut_end = end + (len(text[end:]) - len(after)) + (1 if after.startswith(",") else 0)
                out.append({"rule": "appositive", "removed": text[start:end], "text": delete_span(text, cut_start, cut_end)})
        elif tok.dep_ == "amod" and tok.pos_ == "ADJ" and tok.head.pos_ == "NOUN":
            start, end = subtree_span(tok)
            if end - start <= 25:
                out.append({"rule": "adjective", "removed": text[start:end], "text": delete_span(text, start, end)})
        elif tok.dep_ == "prep" and tok.head.pos_ == "VERB" and tok.lower_ != "of":
            span = list(tok.subtree)
            # Peripheral only: short, and the verb keeps another complement or prepositional phrase.
            others = [c for c in tok.head.children if c.dep_ in {"dobj", "attr", "acomp", "prep", "xcomp", "ccomp"} and c.i != tok.i]
            if len(span) <= 6 and others and has_content(span):
                start, end = subtree_span(tok)
                out.append({"rule": "prepositional_adjunct", "removed": text[start:end], "text": delete_span(text, start, end)})
        elif tok.dep_ == "advmod" and tok.pos_ == "ADV" and tok.lower_ not in NON_CONTENT_ADV and tok.head.pos_ == "VERB":
            start, end = subtree_span(tok)
            out.append({"rule": "adverb", "removed": text[start:end], "text": delete_span(text, start, end)})
    return out


def century(year: int) -> str:
    n = (year - 1) // 100 + 1
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"the {n}{suffix} century"


def clause_and_year_losses(doc, text: str) -> list[dict]:
    """Relative / coordinated clause deletion and year generalization: judged 'Some' -> mild (v2.1)."""
    out = []
    for tok in doc:
        if tok.dep_ == "conj" and tok.pos_ == "VERB" and tok.head.dep_ == "ROOT":
            cc = [c for c in tok.head.children if c.dep_ == "cc" and c.i < tok.i]
            start = (cc[-1].idx if cc else subtree_span(tok)[0])
            end = subtree_span(tok)[1]
            if text[end:].strip()[:1] in {".", ""}:
                out.append({"rule": "drop_coordinated_clause", "removed": text[start:end], "text": delete_span(text, start, end)})
        elif tok.dep_ == "relcl":
            start, end = subtree_span(tok)
            before = text[:start].rstrip()
            cut_start = len(before) - 1 if before.endswith(",") else start
            after = text[end:]
            cut_end = end + (1 if after.lstrip().startswith(",") and before.endswith(",") else 0)
            out.append({"rule": "drop_relative_clause", "removed": text[start:end], "text": delete_span(text, cut_start, cut_end)})
    for m in re.finditer(r"\b(in|since|from|by|until) (1[0-9]{3}|20[0-2][0-9])\b", text):
        out.append({"rule": "generalize_year", "removed": m.group(2),
                    "text": tidy(text[:m.start()] + f"{m.group(1)} {century(int(m.group(2)))}" + text[m.end():])})
    return out


def major_losses(doc, text: str) -> list[dict]:
    """Only whole-sentence deletion reached the 'A lot' threshold in the review (v2.1).
    Number generalization was removed (decimal bug, 'about many')."""
    sentences = split_sentences(text)
    return [{"rule": "drop_sentence", "removed": s, "text": tidy(" ".join(sentences[:i] + sentences[i + 1:]))}
            for i, s in enumerate(sentences[1:], 1)]


def balanced(candidate: str, clean: str) -> bool:
    """Reject deletions that leave an unmatched quote or bracket."""
    def parity(s: str) -> tuple:
        return (s.count('"') % 2, s.count("“") - s.count("”"), s.count("(") - s.count(")"))
    return parity(candidate) == parity(clean)


def base_pairs(corpus_dir: Path, scores_path: Path, entail_filter: bool) -> list[dict]:
    scores = {r["canonical_pair_id"]: r for r in read_jsonl(scores_path)}
    pairs: dict[str, dict] = {}
    for split in ("train", "validation"):
        for r in read_jsonl(corpus_dir / f"{split}.jsonl"):
            if r.get("axis") != "MEANING" or r.get("corpus") == "Wikipedia-Vikidia":
                continue
            p = pairs.setdefault(r["canonical_pair_id"], {k: r.get(k) for k in (
                "canonical_pair_id", "canonical_original_id", "original", "corpus", "split")})
            p["split"] = split
            p["clean" if r["variant"] == "simplified" else "contradiction"] = r["text"]
    out = []
    for p in pairs.values():
        s = scores[p["canonical_pair_id"]]
        p["clean_entailment"] = s["nli_probabilities"]["entailment"]
        p["clean_acceptability"] = s["acceptability"]
        p["entailment_filter_pass"] = p["clean_entailment"] >= 0.5
        if p["entailment_filter_pass"] or not entail_filter:
            out.append(p)
    return sorted(out, key=lambda p: p["canonical_pair_id"])


def build_candidates(pairs: list[dict], seed: int, per_level: int) -> list[dict]:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    rows = []
    for p, doc in zip(pairs, nlp.pipe([p["clean"] for p in pairs], batch_size=256)):
        levels = {"neutral_trim": neutral_trims(p["clean"]), "mild_loss": mild_losses(doc),
                  "major_loss": major_losses(doc, p["clean"])}
        candidates = []
        for level, cands in levels.items():
            unique = {}
            for c in cands:
                if c["text"] and c["text"] != p["clean"] and WORD.search(c["text"]) and balanced(c["text"], p["clean"]):
                    unique.setdefault(c["text"], c)
            ordered = sorted(unique.values(), key=lambda c: stable_key(seed, f'{p["canonical_pair_id"]}:{level}:{c["text"]}'))
            candidates += [{"level": level, **c} for c in ordered[:per_level]]
        rows.append({**p, "candidates": candidates})
    return rows


def score(rows: list[dict], pools_config: dict, device: str) -> None:
    from phase6_degraded_corpus.src.evaluation.score_mmi_candidates import Checkers
    ck = Checkers(pools_config, device)
    flat = [(r, c) for r in rows for c in r["candidates"]]
    acc = ck.acceptability([c["text"] for _, c in flat])
    nli = ck.nli_probs([r["clean"] for r, _ in flat], [c["text"] for _, c in flat])
    for (r, c), a, n in zip(flat, acc, nli):
        c["acceptability"], c["nli_clean_candidate"] = a, n


def passes(row: dict, c: dict, cfg: dict) -> dict:
    clean_tokens = re.findall(r"\w+", row["clean"].lower())
    cand_tokens = re.findall(r"\w+", c["text"].lower())
    removed = Counter(clean_tokens) - Counter(cand_tokens)
    added = Counter(cand_tokens) - Counter(clean_tokens)
    checks = {"acceptable": c["acceptability"] >= min(cfg["tau_accept"], row["clean_acceptability"] - cfg["delta"])}
    if c["level"] == "neutral_trim":
        checks["only_whitelisted_removed"] = not added and set(removed) <= NEUTRAL_WORDS
    else:
        checks["not_contradiction"] = c["nli_clean_candidate"]["contradiction"] < 0.5
        checks["removes_content"] = bool(removed)
    return checks


def select(rows: list[dict], cfg: dict) -> tuple[list[dict], dict]:
    groups, stats = [], Counter()
    for r in rows:
        members = [{"level": "original_copy", "text": r["original"]}, {"level": "clean", "text": r["clean"]}]
        for level in ("neutral_trim", "mild_loss", "major_loss"):
            stats[f"{level}:pairs_with_candidates"] += any(c["level"] == level for c in r["candidates"])
            for c in r["candidates"]:
                if c["level"] != level:
                    continue
                c["checks"] = passes(r, c, cfg)
                if all(c["checks"].values()):
                    members.append({k: c[k] for k in ("level", "text", "rule", "removed") if k in c})
                    stats[f"{level}:selected"] += 1
                    break
        if r.get("contradiction"):
            members.append({"level": "contradiction", "text": r["contradiction"]})
        for m in members:
            m["target_score"] = TARGETS[m["level"]]
        groups.append({k: r[k] for k in ("canonical_pair_id", "canonical_original_id", "original", "corpus", "split",
                                         "clean_entailment", "entailment_filter_pass")} | {"members": members})
        stats["groups"] += 1
        stats[f"group_size:{len(members)}"] += 1
    return groups, dict(sorted(stats.items()))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("candidates", "score", "select"))
    parser.add_argument("--corpus-dir", type=Path, default=Path("phase6_degraded_corpus/runs/mmi_en_v2_full/corpus"))
    parser.add_argument("--pools-config", type=Path, default=Path("phase6_degraded_corpus/configs/experiments/mmi_en_v2_pools.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("phase6_degraded_corpus/runs/meaning_graded_en_v1"))
    parser.add_argument("--all-pairs", action="store_true", help="no entailment filter (ablation A_all)")
    parser.add_argument("--seed", type=int, default=20261001)
    parser.add_argument("--per-level", type=int, default=4)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    cfg = json.loads(args.pools_config.read_text())
    suffix = "_all" if args.all_pairs else ""
    cand_path, scored_path = args.out_dir / f"candidates{suffix}.jsonl", args.out_dir / f"scored{suffix}.jsonl"
    if args.stage == "candidates":
        pairs = base_pairs(args.corpus_dir, Path(cfg["quality_scores_file"]), entail_filter=not args.all_pairs)
        rows = build_candidates(pairs, args.seed, args.per_level)
        write_jsonl(cand_path, rows)
        print(json.dumps({"pairs": len(rows), "candidates": dict(Counter(c["level"] for r in rows for c in r["candidates"]))}))
    elif args.stage == "score":
        rows = read_jsonl(cand_path)
        score(rows, cfg, args.device)
        write_jsonl(scored_path, rows)
    else:
        groups, stats = select(read_jsonl(scored_path), cfg)
        write_jsonl(args.out_dir / f"groups{suffix}.jsonl", groups)
        (args.out_dir / f"groups{suffix}_report.json").write_text(json.dumps(stats, indent=2) + "\n")
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
