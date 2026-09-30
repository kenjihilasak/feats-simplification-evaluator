#!/usr/bin/env python3
"""Deterministic rule generators for the fose_en_v1 experiment."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass

from phase6_degraded_corpus.src.common.contracts import stable_key

TOKEN_RE = re.compile(r"\w+(?:[-’']\w+)*|[^\w\s]", re.UNICODE)
WORD_RE = re.compile(r"^[^\W_]+(?:[-’'][^\W_]+)*$", re.UNICODE)
PREPOSITIONS = {"in": "on", "on": "in", "at": "in", "of": "for", "for": "of", "to": "at"}
AGREEMENT = {"is": "are", "are": "is", "was": "were", "were": "was", "has": "have", "have": "has"}


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def detokenize(items: list[str]) -> str:
    text = " ".join(items)
    text = re.sub(r"\s+([,.;:!?%\)\]\}])", r"\1", text)
    text = re.sub(r"([\(\[\{])\s+", r"\1", text)
    text = re.sub(r"\s+(['’])\s+", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\b([Aa])\s+([aeiouAEIOU])", lambda m: ("An" if m.group(1) == "A" else "an") + " " + m.group(2), text)
    text = re.sub(r"\b([Aa])n\s+([^aeiouAEIOU\W])", lambda m: m.group(1) + " " + m.group(2), text)
    return text


def alignment(original: str, simple: str):
    left, right = tokens(original), tokens(simple)
    ops = difflib.SequenceMatcher(None, [x.casefold() for x in left], [x.casefold() for x in right], autojunk=False).get_opcodes()
    return left, right, ops


def choose(seed: int, pair_id: str, kind: str, sites: list):
    return min(sites, key=lambda site: stable_key(seed, f"{pair_id}:{kind}:{site}")) if sites else None


def fluency_sites(text: str, nlp) -> dict[str, list]:
    doc = nlp(text)
    sites = {name: [] for name in ("agreement", "determiner_drop", "preposition_swap", "word_order")}
    for i, tok in enumerate(doc):
        low = tok.lower_
        if low in AGREEMENT:
            subjects = [c for c in tok.children if c.dep_ in {"nsubj", "nsubjpass"}]
            if len(subjects) == 1 and subjects[0].pos_ in {"NOUN", "PRON", "PROPN"}:
                sites["agreement"].append(i)
        if low in {"a", "an", "the"} and i + 1 < len(doc):
            following = doc[i + 1]
            if following.pos_ == "NOUN" and "Plur" not in following.morph.get("Number"):
                sites["determiner_drop"].append(i)
        if low in PREPOSITIONS and tok.pos_ == "ADP":
            sites["preposition_swap"].append(i)
        if i + 1 < len(doc) and tok.pos_ == "ADJ" and doc[i + 1].pos_ == "NOUN" and not (tok.ent_type_ or doc[i + 1].ent_type_):
            sites["word_order"].append((i, i + 1))
        if i + 1 < len(doc) and tok.pos_ == "AUX" and doc[i + 1].pos_ == "VERB" and not (tok.like_num or doc[i + 1].like_num):
            sites["word_order"].append((i, i + 1))
    return sites


def generate_fluency(text: str, pair_id: str, seed: int, nlp, error_type: str | None = None) -> dict | None:
    doc = nlp(text)
    available = fluency_sites(text, nlp)
    kinds = [error_type] if error_type else [k for k, v in available.items() if v]
    kinds = [k for k in kinds if available.get(k)]
    if not kinds:
        return None
    kind = min(kinds, key=lambda value: stable_key(seed, f"{pair_id}:{value}"))
    site = choose(seed, pair_id, kind, available[kind])
    values = [tok.text for tok in doc]
    if kind == "agreement":
        replacement = AGREEMENT[values[site].casefold()]
        values[site] = replacement.capitalize() if values[site][0].isupper() else replacement
    elif kind == "determiner_drop":
        del values[site]
    elif kind == "preposition_swap":
        replacement = PREPOSITIONS[values[site].casefold()]
        values[site] = replacement.capitalize() if values[site][0].isupper() else replacement
    else:
        left, right = site
        values[left], values[right] = values[right], values[left]
    return {"degraded": detokenize(values), "error_type": kind, "site": site}


def edit_sites(original: str, simple: str, tag: str) -> list[tuple[int, int, int, int]]:
    _, _, ops = alignment(original, simple)
    return [(i1, i2, j1, j2) for op, i1, i2, j1, j2 in ops if op == tag]


def generate_omit(original: str, simple: str, pair_id: str, seed: int, sites=None) -> dict | None:
    left, right, _ = alignment(original, simple)
    sites = sites if sites is not None else edit_sites(original, simple, "delete")
    site = choose(seed, pair_id, "OMIT", sites)
    if site is None:
        return None
    i1, i2, j1, _ = site
    inserted = left[i1:i2]
    return {"degraded": detokenize(right[:j1] + inserted + right[j1:]), "span": inserted, "site": site}


def generate_syn(original: str, simple: str, pair_id: str, seed: int, sites=None) -> dict | None:
    left, right, _ = alignment(original, simple)
    sites = sites if sites is not None else edit_sites(original, simple, "replace")
    site = choose(seed, pair_id, "SYN", sites)
    if site is None:
        return None
    i1, i2, j1, j2 = site
    return {"degraded": detokenize(right[:j1] + left[i1:i2] + right[j2:]), "restored": left[i1:i2], "simple_span": right[j1:j2], "site": site}


def generate_expl(original: str, simple: str, pair_id: str, seed: int, sites=None) -> dict | None:
    _, right, _ = alignment(original, simple)
    sites = sites if sites is not None else edit_sites(original, simple, "insert")
    site = choose(seed, pair_id, "EXPL", sites)
    if site is None:
        return None
    _, _, j1, j2 = site
    removed = right[j1:j2]
    kept = right[:j1] + right[j2:]
    while len(kept) >= 2 and kept[j1 - 1:j1 + 1] == [",", ","]:
        del kept[j1]
    degraded = detokenize(kept)
    degraded = re.sub(r"\(\s*\)", "", degraded)
    degraded = re.sub(r",\s*(?:which|a)\s*([,.;])", r"\1", degraded, flags=re.I)
    return {"degraded": degraded.strip(), "removed": removed, "site": site}
