#!/usr/bin/env python3
"""Graded MEANING and FLUENCY groups outside English, from a language's v2 pool.

The English recipes (`generate_meaning_graded.py`, `generate_fluency_graded.py`) parse with English spaCy labels
and English word tables. Here the same levels are built from Universal Dependencies labels, which every v2 parser
uses, and per-language tables.

MEANING (target scores as in English v2.1): original copy, clean and a neutral trim ("también", "aussi"…, an empty
parenthetical) 1.0; a mild loss 0.67 (an adjective, appositive, adverb, short peripheral oblique, relative clause,
final coordinated clause or intensifier deleted); a major loss 0.33 (a non-first sentence deleted); a contradiction
0.0 (a number or year changed by rule, or a negation or antonym from the LLM, which NLI must judge a contradiction).

FLUENCY (as in English): clean and original copy 1.0; minor 0.67 (an article dropped or a preposition swapped);
major 0.33 (article gender/number agreement broken, a word-order swap, or two minor errors); severe 0.0 (three
errors). Errors are edited on character spans, so the rest of the text keeps its exact form. As in English,
FLUENCY negatives are not selected with the acceptability model (the baseline the scorer must beat); NLI must
only confirm that meaning is kept.

Stages: `candidates` (CPU) writes the groups' candidates and an LLM plan for contradictions, `generate_mmi_v2`
(GPU) fills that plan, `score` (GPU) adds NLI and acceptability, `select` (CPU) writes the groups.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl
from phase6_degraded_corpus.src.common.languages import get as language, load_nlp
from phase6_degraded_corpus.src.planning.plan_mmi_operations import corrupt_number, split_sentences

MEANING_TARGETS = {"original_copy": 1.0, "clean": 1.0, "neutral_trim": 1.0, "mild_loss": 0.67, "major_loss": 0.33,
                   "contradiction": 0.0}
FLUENCY_TARGETS = {"original_copy": 1.0, "clean": 1.0, "minor": 0.67, "major": 0.33, "severe": 0.0}

NEUTRAL = {"es": {"también"}, "fr": {"aussi", "également"}, "it": {"anche"}, "ca": {"també"},
           "ru": {"также", "тоже"}, "ar": {"أيضا", "أيضاً"}}
INTENSIFIERS = {"es": {"muy"}, "fr": {"très"}, "it": {"molto"}, "ca": {"molt"}, "ru": {"очень"}, "ar": {"جدا", "جداً"}}
# Prepositions swapped for a minor error, and articles whose gender or number is flipped for an agreement error.
PREPOSITIONS = {
    "es": {"de": "en", "en": "de", "a": "en", "con": "de", "por": "para", "para": "por"},
    "fr": {"de": "à", "à": "de", "en": "dans", "dans": "en", "sur": "à", "pour": "de"},
    "it": {"di": "a", "a": "di", "in": "su", "su": "in", "con": "per", "per": "con", "da": "di"},
    "ca": {"de": "a", "a": "de", "en": "a", "amb": "per", "per": "amb"},
    "ru": {"в": "на", "на": "в", "с": "из", "из": "с", "к": "в"},
    "ar": {"في": "على", "على": "في", "من": "إلى", "إلى": "من"},
}
ARTICLE_SWAP = {
    "es": {"el": "la", "la": "el", "los": "las", "las": "los", "un": "una", "una": "un"},
    "fr": {"le": "la", "la": "le", "un": "une", "une": "un"},
    "it": {"il": "la", "la": "il", "i": "le", "le": "i", "un": "una", "una": "un"},
    "ca": {"el": "la", "la": "el", "els": "les", "les": "els", "un": "una", "una": "un"},
}
MINOR, MAJOR = ("determiner_drop", "preposition_swap"), ("agreement", "word_order")
LEVEL_PLANS = {"minor": [("minor", 1)], "major": [("major", 1)], "major_two_minor": [("minor", 2)], "severe": [("any", 3)]}
YEAR = re.compile(r"(?<!\d)(1[0-9]{3}|20[0-2][0-9])(?!\d)")
NUMBER = re.compile(r"(?<![\w.,])\d+(?:[.,]\d+)*%?(?![\w])")


# ---------- shared ----------

def tidy(text: str) -> str:
    text = re.sub(r"\(\s*[,;]?\s*\)", "", text)
    text = re.sub(r"\s+([,.;:!?)؟،])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r",\s*([.;:!?])", r"\1", text)
    text = re.sub(r"^\s*[,;]\s*", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text[:1].upper() + text[1:] if text[:1].islower() else text


def whole(token) -> bool:
    """Stanza splits Arabic clitics into words that share one surface token; only whole tokens are edited."""
    return getattr(token, "whole", True)


def standalone(token, text: str) -> bool:
    """The token is a word of its own in the text: spaCy splits Catalan "del" into "d" + "el", and Italian "dell'" is
    glued to its noun; editing either breaks the word ("dprojecte", "abbonamentodell '")."""
    s, e = token.idx, token.idx + len(token.text)
    glued = lambda c: c.isalnum() or c in "'’"
    return (whole(token) and text[s:e] == token.text and token.text[-1:] not in {"'", "’"}
            and not (s > 0 and glued(text[s - 1])) and not (e < len(text) and glued(text[e])))


def subtree(doc, token) -> list:
    """Tokens whose head chain reaches `token` (spaCy's subtree, also for the Stanza adapter)."""
    out = []
    for t in doc:
        u, steps = t, 0
        while u.i != token.i and u.head.i != u.i and steps < len(doc):
            u, steps = u.head, steps + 1
        if u.i == token.i:
            out.append(t)
    return out


def char_span(tokens: list) -> tuple[int, int]:
    return min(t.idx for t in tokens), max(t.idx + len(t.text) for t in tokens)


def balanced(candidate: str, clean: str) -> bool:
    def parity(s: str) -> tuple:
        return (s.count('"') % 2, s.count("“") - s.count("”"), s.count("«") - s.count("»"), s.count("(") - s.count(")"))
    return parity(candidate) == parity(clean)


# ---------- MEANING ----------

def neutral_trims(text: str, lang: str) -> list[dict]:
    out = [{"rule": "empty_parenthetical", "text": tidy(text[:m.start()] + text[m.end():])}
           for m in re.finditer(r"\s*\((?:\s*[;,]\s*)*\)", text)]
    for word in NEUTRAL.get(lang, ()):
        for m in re.finditer(rf"(?<!\w){re.escape(word)}(?!\w),?\s*", text, re.I):
            out.append({"rule": f"adverb_{word}", "text": tidy(text[:m.start()] + text[m.end():])})
    return out


def mild_losses(doc, text: str, lang: str) -> list[dict]:
    res = language(lang)
    out = []
    for word in INTENSIFIERS.get(lang, ()):
        for m in re.finditer(rf"(?<!\w){re.escape(word)}(?!\w)\s*", text, re.I):
            out.append({"rule": "intensifier", "removed": m.group(0).strip(), "text": tidy(text[:m.start()] + text[m.end():])})

    def cut(rule: str, tokens: list, start: int | None = None, end: int | None = None):
        if not all(whole(t) for t in tokens):
            return
        edges = sorted(tokens, key=lambda t: t.idx)
        if not (standalone(edges[0], text) or edges[0].is_punct) or not (standalone(edges[-1], text) or edges[-1].is_punct):
            return
        s, e = char_span(tokens)
        s, e = (start if start is not None else s), (end if end is not None else e)
        out.append({"rule": rule, "removed": text[s:e], "text": tidy(text[:s] + " " + text[e:])})

    for tok in doc:
        span = subtree(doc, tok)
        content = any(t.pos_ in {"NOUN", "PROPN", "ADJ", "NUM", "VERB"} for t in span)
        if tok.dep_ == "amod" and tok.pos_ == "ADJ" and tok.head.pos_ == "NOUN" and len(span) <= 3:
            # A parse error can hang a clause under an adjective ("espanyols però veniu"): only a contiguous run of
            # adjectives and adverbs is cut.
            ids = sorted(t.i for t in span)
            if ids == list(range(ids[0], ids[-1] + 1)) and all(t.pos_ in {"ADJ", "ADV"} for t in span):
                cut("adjective", span)
        elif tok.dep_ == "appos":
            s, e = char_span(span)
            before, after = text[:s].rstrip(), text[e:]
            if before.endswith(",") and (after.lstrip().startswith(",") or after.strip()[:1] in {".", ""}):
                cut("appositive", span, len(before) - 1, e + (len(after) - len(after.lstrip())) + (1 if after.lstrip().startswith(",") else 0))
        elif (tok.dep_ == "advmod" and tok.pos_ == "ADV" and tok.head.pos_ == "VERB" and len(span) == 1
              and not res.negation.search(tok.text) and tok.lower_ not in NEUTRAL.get(lang, ())
              and not set(tok.morph.get("PronType")) & {"Int", "Rel"}):  # "Come sarà…?" is another question without "Come"
            cut("adverb", span)
        elif tok.dep_.startswith("obl") and tok.head.pos_ == "VERB" and 2 <= len(span) <= 6 and content:
            others = [c for c in doc if c.head.i == tok.head.i and c.i != tok.i and c.i != tok.head.i
                      and (c.dep_.startswith(("obj", "obl", "xcomp", "ccomp")))]
            if others:
                cut("peripheral_oblique", span)
        elif tok.dep_ in {"acl:relcl", "relcl"} or (tok.dep_ == "acl" and any("Rel" in t.morph.get("PronType") for t in span)):
            s, e = char_span(span)
            before = text[:s].rstrip()
            after = text[e:]
            cut_start = len(before) - 1 if before.endswith(",") else s
            cut_end = e + (1 if after.lstrip().startswith(",") and before.endswith(",") else 0)
            cut("relative_clause", span, cut_start, cut_end)
        elif tok.dep_ == "conj" and tok.pos_ == "VERB" and tok.head.dep_ == "ROOT":
            s, e = char_span(span)
            cc = [c for c in doc if c.head.i == tok.i and c.dep_ == "cc" and c.i < span[0].i + 1]
            start = min([c.idx for c in cc] + [s])
            if text[e:].strip()[:1] in {".", ""}:
                cut("final_coordinated_clause", span, start, e)
    return out


def major_losses(text: str, lang: str) -> list[dict]:
    sentences = split_sentences(text, lang)
    return [{"rule": "drop_sentence", "removed": s, "text": tidy(" ".join(sentences[:i] + sentences[i + 1:]))}
            for i, s in enumerate(sentences[1:], 1) if sentences.count(s) == 1]


MONTH_NAMES = re.compile(
    r"(?:de\s+|d['’]\s*)?(?:january|february|march|april|may|june|july|august|september|october|november|december|"
    r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre|"
    r"gener|febrer|març|maig|juny|juliol|setembre|desembre|gennaio|febbraio|aprile|maggio|giugno|luglio|"
    r"settembre|ottobre|dicembre|janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|"
    r"décembre|января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\b", re.I)
RANGE_WORD = r"(?:y|i|e|and|to|a|al|hasta|fins|à|au|et|до|и|–|-)"
RANGE_FILL = r"(?:(?:el|la|les|los|il|the|año|años|any|anys|anno|anni|year|years|de|del|l['’]|d['’])\s*){0,3}"


def changeable(text: str, start: int, end: int) -> bool:
    """A number whose change is a clean contradiction. Not: a date part ("01/12/2017", "30 de juny"), one end of a
    range ("entre 16 y 25 años", "desde 2021 hasta 2027": a changed end can invert it), a decade ("anys 90"), part of a
    digit group or code ("900 922 357", "Model 721")."""
    before, after = text[:start], text[end:]
    if re.search(r"[/\-–:]\s*$", before) or re.match(r"\s*[/\-–:]\s*\d", after):
        return False
    if re.search(r"\d\s+$", before) or re.match(r"\s+\d", after) or MONTH_NAMES.match(after.lstrip()):
        return False
    if re.search(rf"\d\S*\s+{RANGE_FILL}{RANGE_WORD}\s+{RANGE_FILL}$", before) or \
            re.match(rf"\s+{RANGE_WORD}\s+{RANGE_FILL}\d", after):
        return False
    if re.search(r"(?:anys|años|anni|années|years|ans)\s+$", before, re.I) or re.match(r"s\b", after):
        return False
    word = re.search(r"(\w+)\s+$", before)
    return not (word and word.group(1)[:1].isupper() and not re.search(r"(?:^|[.!?]\s+)\w+\s+$", before))


def number_contradictions(text: str, original: str, seed: int, pid: str) -> list[dict]:
    out = []
    for m in YEAR.finditer(text):
        if not changeable(text, m.start(), m.end()):
            continue
        shift = 3 + int(stable_key(seed, f"{pid}:year:{m.start()}")[:4], 16) % 28
        new = str(int(m.group(1)) + shift)
        if new not in original:
            out.append({"rule": "year_changed", "removed": m.group(1), "text": text[:m.start()] + new + text[m.end():]})
    for m in NUMBER.finditer(text):
        if YEAR.fullmatch(m.group(0)) or not changeable(text, m.start(), m.end()):
            continue
        new = corrupt_number(m.group(0), original, seed, f"{pid}:{m.start()}")
        if new:
            out.append({"rule": "number_changed", "removed": m.group(0), "text": text[:m.start()] + new + text[m.end():]})
    return out


# ---------- FLUENCY ----------

def fluency_sites(doc, lang: str) -> dict[str, list]:
    res = language(lang)
    sites = {k: [] for k in (*MINOR, *MAJOR)}
    preps, swaps = PREPOSITIONS.get(lang, {}), ARTICLE_SWAP.get(lang, {})
    tokens, text = list(doc), doc.text
    for i, tok in enumerate(tokens):
        if not standalone(tok, text):
            continue
        nxt = tokens[i + 1] if i + 1 < len(tokens) else None
        nxt = nxt if nxt is not None and standalone(nxt, text) else None
        low = tok.lower_
        article = tok.pos_ == "DET" and low in res.articles
        if article and nxt is not None and nxt.pos_ == "NOUN":
            sites["determiner_drop"].append(i)
            if low in swaps:
                sites["agreement"].append(i)
        if tok.pos_ == "ADP" and low in preps:
            sites["preposition_swap"].append(i)
        if nxt is not None and not (tok.like_num or nxt.like_num):
            if tok.pos_ == "AUX" and nxt.pos_ == "VERB":
                sites["word_order"].append((i, i + 1))
            elif tok.pos_ == "ADP" and nxt.pos_ in {"NOUN", "PROPN"} and tok.head.i == nxt.i:  # "en Madrid" -> "Madrid en"
                sites["word_order"].append((i, i + 1))
    return sites


def pick_edits(sites: dict, plan: list, seed: int, pid: str, tag: str) -> list | None:
    pools = {"minor": [(k, s) for k in MINOR for s in sites[k]], "major": [(k, s) for k in MAJOR for s in sites[k]],
             "any": [(k, s) for k in (*MINOR, *MAJOR) for s in sites[k]]}
    chosen, used = [], set()
    for group, n in plan:
        kinds_used = Counter()
        for kind, site in sorted(pools[group], key=lambda e: stable_key(seed, f"{pid}:{tag}:{e}")):
            if sum(c in pools[group] for c in chosen) >= n:
                break
            pos = set(site) if isinstance(site, tuple) else {site}
            if pos & used or any(abs(p - q) <= 1 for p in pos for q in used):
                continue
            if group == "any" and kinds_used[kind] >= 2:
                continue
            chosen.append((kind, site)); used |= pos; kinds_used[kind] += 1
        if sum(c in pools[group] for c in chosen) < n:
            return None
    return chosen


def recase(new: str, old: str) -> str:
    return new[:1].upper() + new[1:] if old[:1].isupper() else new


def apply_errors(text: str, doc, edits: list, lang: str) -> str:
    tokens = list(doc)
    spans = []  # (start, end, replacement)
    for kind, site in edits:
        if kind == "word_order":
            a, b = tokens[site[0]], tokens[site[1]]
            between = text[a.idx + len(a.text):b.idx]
            first, second = b.text, a.text
            if a.text[:1].isupper() and b.pos_ != "PROPN":  # the sentence keeps its capital
                first, second = recase(b.text, a.text), (a.text if a.pos_ == "PROPN" else a.text[:1].lower() + a.text[1:])
            spans.append((a.idx, b.idx + len(b.text), first + between + second))
        else:
            t = tokens[site]
            if kind == "determiner_drop":
                end = t.idx + len(t.text)
                while end < len(text) and text[end] == " ":
                    end += 1
                if t.text[:1].isupper() and end < len(text):  # "La casa" -> "Casa": the next letter takes the capital
                    spans.append((t.idx, end + 1, text[end].upper()))
                else:
                    spans.append((t.idx, end, ""))
            else:
                table = PREPOSITIONS[lang] if kind == "preposition_swap" else ARTICLE_SWAP[lang]
                spans.append((t.idx, t.idx + len(t.text), recase(table[t.lower_], t.text)))
    for start, end, new in sorted(spans, reverse=True):
        text = text[:start] + new + text[end:]
    return re.sub(r"\s{2,}", " ", text).strip()


# ---------- stages ----------

def pool(run: Path) -> tuple[list[dict], dict]:
    cfg = json.loads((run / "checker_config.json").read_text(encoding="utf-8"))
    scores = {r["canonical_pair_id"]: r for r in read_jsonl(run / "pools/clean_quality_scores.jsonl")}
    rows = []
    for r in read_jsonl(run / "pools/structural_candidates.jsonl"):
        s = scores[r["canonical_pair_id"]]
        if s["acceptability"] >= cfg["tau_accept"] and s["nli_probabilities"]["contradiction"] < cfg["nli_contradiction_threshold"]:
            rows.append({**r, "clean_acceptability": s["acceptability"]})
    return rows, cfg


def candidates(run: Path, size: int) -> tuple[list[dict], list[dict], list[dict]]:
    rows, cfg = pool(run)
    lang, seed = cfg["language"], cfg["seed"]
    nlp = load_nlp(lang)
    pick = lambda tag: sorted(rows, key=lambda r: stable_key(seed, f"{tag}:{r['canonical_pair_id']}"))[:size]
    meaning, fluency, plan = [], [], []
    for r in pick("meaning_ml"):
        clean, pid = r["clean_simplification"], r["canonical_pair_id"]
        doc = nlp(clean)
        levels = {"neutral_trim": neutral_trims(clean, lang), "mild_loss": mild_losses(doc, clean, lang),
                  "major_loss": major_losses(clean, lang), "contradiction": number_contradictions(clean, r["original"], seed, pid)}
        cands = []
        for level, found in levels.items():
            unique = {}
            for c in found:
                if c["text"] and c["text"] != clean and re.search(r"\w", c["text"]) and balanced(c["text"], clean):
                    unique.setdefault(c["text"], c)
            ordered = sorted(unique.values(), key=lambda c: stable_key(seed, f"{pid}:{level}:{c['text']}"))
            cands += [{"level": level, "generator": "rule", **c} for c in ordered[:4]]
        meaning.append({**{k: r[k] for k in ("canonical_pair_id", "canonical_original_id", "corpus", "original",
                                            "clean_acceptability")}, "language": lang, "clean": clean, "candidates": cands})
        sentences = split_sentences(clean, lang)
        target = max(range(len(sentences)), key=lambda i: len(sentences[i].split()))
        plan.append({**r, "target_axis": "CONTRA", "operation": "meaning_contradict", "generator_kind": "llm",
                     "sentences": sentences, "target_sentence_index": target, "plan_status": "ready", "language": lang})
    for r in pick("fluency_ml"):
        clean, pid = r["clean_simplification"], r["canonical_pair_id"]
        doc = nlp(clean)
        sites = fluency_sites(doc, lang)
        members = []
        for name, level_plan in LEVEL_PLANS.items():
            edits = pick_edits(sites, level_plan, seed, pid, name)
            if edits:
                text = apply_errors(clean, doc, edits, lang)
                if text != clean:
                    members.append({"level": "major" if name == "major_two_minor" else name, "rule": name,
                                    "edits": [k for k, _ in edits], "text": text})
        fluency.append({**{k: r[k] for k in ("canonical_pair_id", "canonical_original_id", "corpus", "original")},
                        "language": lang, "clean": clean, "members": members})
    return meaning, fluency, plan


def score(run: Path, device: str) -> None:
    from phase6_degraded_corpus.src.evaluation.score_mmi_candidates import Checkers
    from phase6_degraded_corpus.src.generation.export_phase6_corpus import keep_spelling

    cfg = json.loads((run / "checker_config.json").read_text(encoding="utf-8"))
    meaning = read_jsonl(run / "meaning_fluency/meaning_candidates.jsonl")
    llm = {g["canonical_pair_id"]: g for g in read_jsonl(run / "generations/contradict.jsonl")} \
        if (run / "generations/contradict.jsonl").exists() else {}
    for r in meaning:
        g = llm.get(r["canonical_pair_id"])
        for c in (g or {}).get("candidates", []):
            if c.get("degraded") and c["degraded"] != r["clean"]:
                # The LLM also repairs accents ("busqueda" -> "búsqueda"), a cue unrelated to the contradiction.
                r["candidates"].append({"level": "contradiction", "generator": "llm", "rule": "llm_contradict",
                                        "text": keep_spelling(r["clean"], c["degraded"])})
    fluency = read_jsonl(run / "meaning_fluency/fluency_candidates.jsonl")
    ck = Checkers(cfg, device)
    flat = [(r["clean"], c) for r in meaning for c in r["candidates"]]
    acc = ck.acceptability([c["text"] for _, c in flat])
    fwd = ck.nli_probs([clean for clean, _ in flat], [c["text"] for _, c in flat])
    for (_, c), a, f in zip(flat, acc, fwd):
        c["acceptability"], c["nli_clean_candidate"] = a, f
    flat = [(r["clean"], m) for r in fluency for m in r["members"]]
    fwd = ck.nli_probs([clean for clean, _ in flat], [m["text"] for _, m in flat])
    bwd = ck.nli_probs([m["text"] for _, m in flat], [clean for clean, _ in flat])
    for (_, m), f, b in zip(flat, fwd, bwd):
        m["meaning_kept"] = min(f["entailment"], b["entailment"]) >= 0.5
    write_jsonl(run / "meaning_fluency/meaning_scored.jsonl", meaning)
    write_jsonl(run / "meaning_fluency/fluency_scored.jsonl", fluency)


def meaning_checks(row: dict, c: dict, cfg: dict) -> dict:
    clean_tokens = re.findall(r"\w+", row["clean"].casefold())
    cand_tokens = re.findall(r"\w+", c["text"].casefold())
    removed, added = Counter(clean_tokens) - Counter(cand_tokens), Counter(cand_tokens) - Counter(clean_tokens)
    checks = {"acceptable": c["acceptability"] >= min(cfg["tau_accept"], row["clean_acceptability"] - cfg["delta"])}
    if c["level"] == "neutral_trim":
        checks["only_whitelisted_removed"] = not added and set(removed) <= NEUTRAL.get(row["language"], set())
    elif c["level"] == "contradiction":
        checks["contradicts_clean"] = c["nli_clean_candidate"]["contradiction"] >= 0.5
        # One small edit: a contradiction is a changed fact, not a rewrite.
        checks["small_edit"] = sum(removed.values()) <= 2 and sum(added.values()) <= 3
    else:
        checks["not_contradiction"] = c["nli_clean_candidate"]["contradiction"] < 0.5
        checks["removes_content"] = bool(removed)
    return checks


def select(run: Path) -> dict:
    cfg = json.loads((run / "checker_config.json").read_text(encoding="utf-8"))
    groups, stats = [], Counter()
    for r in read_jsonl(run / "meaning_fluency/meaning_scored.jsonl"):
        members = [{"level": "original_copy", "text": r["original"]}, {"level": "clean", "text": r["clean"]}]
        for level in ("neutral_trim", "mild_loss", "major_loss", "contradiction"):
            # Rule contradictions (a changed number) come first; the LLM fills in where there is no number.
            ordered = sorted((c for c in r["candidates"] if c["level"] == level), key=lambda c: c["generator"] != "rule")
            for c in ordered:
                c["checks"] = meaning_checks(r, c, cfg)
                if all(c["checks"].values()):
                    members.append({k: c[k] for k in ("level", "text", "rule", "removed") if k in c})
                    stats[f"MEANING:{level}"] += 1
                    break
        for m in members:
            m["target_score"] = MEANING_TARGETS[m["level"]]
        if len({m["target_score"] for m in members}) >= 2:
            groups.append({k: r[k] for k in ("canonical_pair_id", "canonical_original_id", "corpus", "original", "language")}
                          | {"axis": "MEANING", "members": members})
    write_jsonl(run / "scored/meaning_groups.jsonl", groups)
    stats["MEANING:groups"] = len(groups)
    fgroups = []
    for r in read_jsonl(run / "meaning_fluency/fluency_scored.jsonl"):
        members = [{"level": "original_copy", "text": r["original"]}, {"level": "clean", "text": r["clean"]}]
        for m in r["members"]:
            if m.get("meaning_kept"):
                members.append(m); stats[f"FLUENCY:{m['rule']}"] += 1
        for m in members:
            m["target_score"] = FLUENCY_TARGETS[m["level"]]
        if len({m["target_score"] for m in members}) >= 2:
            fgroups.append({k: r[k] for k in ("canonical_pair_id", "canonical_original_id", "corpus", "original", "language")}
                           | {"axis": "FLUENCY", "members": members})
    write_jsonl(run / "scored/fluency_groups.jsonl", fgroups)
    stats["FLUENCY:groups"] = len(fgroups)
    return dict(sorted(stats.items()))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=("candidates", "score", "select"))
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--size", type=int, default=600, help="pairs per axis")
    p.add_argument("--device", default="cuda")
    args = p.parse_args()
    out = args.run_dir / "meaning_fluency"; out.mkdir(parents=True, exist_ok=True)
    if args.stage == "candidates":
        meaning, fluency, plan = candidates(args.run_dir, args.size)
        write_jsonl(out / "meaning_candidates.jsonl", meaning)
        write_jsonl(out / "fluency_candidates.jsonl", fluency)
        write_jsonl(out / "contradict_plan.jsonl", plan)
        print(json.dumps({"meaning": dict(Counter(c["level"] for r in meaning for c in r["candidates"])),
                          "fluency": dict(Counter(m["rule"] for r in fluency for m in r["members"])), "llm_plan": len(plan)},
                         ensure_ascii=False))
    elif args.stage == "score":
        score(args.run_dir, args.device)
    else:
        print(json.dumps(select(args.run_dir), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
