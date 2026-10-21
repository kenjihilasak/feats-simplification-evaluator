#!/usr/bin/env python3
"""Deterministic rule generators for the fose_en_v1 experiment."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass

from phase6_degraded_corpus.src.common.contracts import stable_key
from phase6_degraded_corpus.src.common.languages import get as language

TOKEN_RE = re.compile(r"\w+(?:[-’']\w+)*|[^\w\s]", re.UNICODE)
WORD_RE = re.compile(r"^[^\W_]+(?:[-’'][^\W_]+)*$", re.UNICODE)
PREPOSITIONS = {"in": "on", "on": "in", "at": "in", "of": "for", "for": "of", "to": "at"}
AGREEMENT = {"is": "are", "are": "is", "was": "were", "were": "was", "has": "have", "have": "has"}
OPEN_TO_CLOSE = {"(": ")", "[": "]", "{": "}", '"': '"', "“": "”", "‘": "’"}


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def detokenize(items: list[str], lang: str = "en", references: tuple[str, ...] = ()) -> str:
    text = " ".join(items)
    text = re.sub(r"\s+([,.;:!?%\)\]\}])", r"\1", text)
    text = re.sub(r"([\(\[\{])\s+", r"\1", text)
    text = re.sub(r"\s+(['’])\s+", r"\1", text)
    text = re.sub(r'"\s*([^"]*?)\s*"', r'"\1"', text)  # straight double quotes come in pairs
    text = re.sub(r"\s+", " ", text).strip()
    if lang == "en":
        text = re.sub(r"\b([Aa])\s+([aeiouAEIOU])", lambda m: ("An" if m.group(1) == "A" else "an") + " " + m.group(2), text)
        text = re.sub(r"\b([Aa])n\s+([^aeiouAEIOU\W])", lambda m: m.group(1) + " " + m.group(2), text)
        return text
    text = re.sub(r"([¿¡])\s+", r"\1", text)
    return match_spacing(text, references)


def match_spacing(text: str, references: tuple[str, ...]) -> str:
    """Follow the source texts' spacing so typography is not a cue: "6,800" stays one number, and when the
    simplification (the last reference) spaces French high punctuation ("Pourquoi ?"), so does the output."""
    joined = " ".join(references)
    style = references[-1] if references else ""
    if re.search(r"\d[.,]\d", joined):
        text = re.sub(r"(\d)([.,]) (\d{3})\b", r"\1\2\3", text)
    if re.search(r"\w [;:!?»]", style):
        text = re.sub(r"(?<=[\w)\]\"”])([;:!?»])", r" \1", text)
    if "« " in style:
        text = re.sub(r"«\s*", "« ", text)
    return text


def splice(original: str, simple: str, edits: list[tuple[str, tuple[int, int, int, int]]]) -> str:
    """Apply aligned token edits to the simplification's own string, keeping its exact spacing.

    Used outside English, where pre-tokenized corpora (CLEAR: "en cours , et") would otherwise come back
    normalized only in the degraded version. kind: "insert" puts original tokens i1:i2 before simple token j1,
    "replace" swaps simple j1:j2 for original i1:i2, "delete" removes simple j1:j2. Edits apply right to left.
    """
    so = [m.span() for m in TOKEN_RE.finditer(original)]
    ss = [m.span() for m in TOKEN_RE.finditer(simple)]
    start = lambda j: ss[j][0] if j < len(ss) else len(simple)
    text = simple
    for kind, (i1, i2, j1, j2) in sorted(edits, key=lambda e: e[1][2], reverse=True):
        segment = original[so[i1][0]:so[i2 - 1][1]] if i2 > i1 else ""
        if kind == "insert":
            gap = original[so[i2 - 1][1]:so[i2][0]] if i2 < len(so) else ""
            at = start(j1)
            if at == len(text):
                text = text + " " + segment
            else:
                if not gap and text[at:at + 1].isalnum():
                    gap = " "
                text = text[:at] + segment + gap + text[at:]
        elif kind == "replace":
            text = text[:start(j1)] + segment + text[ss[j2 - 1][1]:]
        elif j1:  # drop the span with the space before it, keep the one after
            text = text[:ss[j1 - 1][1]] + text[ss[j2 - 1][1]:]
        else:
            text = text[start(j2):]
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


def span_is_balanced(items: list[str]) -> bool:
    """Reject spans cut out of a parenthesis or quotation."""
    stack: list[str] = []
    for item in items:
        if item in OPEN_TO_CLOSE:
            close = OPEN_TO_CLOSE[item]
            if item == close and stack and stack[-1] == close:
                stack.pop()
            else:
                stack.append(close)
        elif item in OPEN_TO_CLOSE.values():
            if not stack or stack.pop() != item:
                return False
    return not stack


def explanatory_pattern(left: list[str], inserted: list[str], right: list[str], lang: str = "en") -> str | None:
    """Classify a supported explanatory insertion from aligned token context."""
    res = language(lang)
    low = [x.casefold() for x in inserted]
    if not low:
        return None
    joined = " ".join(low)
    if inserted[0] == "(" and inserted[-1] == ")" and len(inserted) >= 3:
        return "parenthetical_gloss"
    inner = low[1:-1] if inserted[0] == "," and inserted[-1] == "," else low
    comma_delimited = (inserted[0] == "," and inserted[-1] == ",") or (left[-1:] == [","] and right[:1] == [","])
    if comma_delimited:
        # French elides the article into the noun ("l'énergie").
        if inner and (inner[0] in res.articles or (lang == "fr" and inner[0].startswith(("l'", "l’")))):
            return "appositive_gloss"
        if len(inner) >= 2 and inner[0] in res.relative_pronouns and inner[1] in res.definitional_verbs:
            return "definitional_relative"
    # English keeps its v2 behaviour; elsewhere a comma-delimited marker gloss (", c'est-à-dire …,") counts too.
    texts = [joined] if lang == "en" else [joined, " ".join(inner)]
    if any(text == marker or text.startswith(marker + " ") for text in texts for marker in res.gloss_markers):
        return "marker_gloss"
    return None


def generate_omit(original: str, simple: str, pair_id: str, seed: int, sites=None, lang: str = "en") -> dict | None:
    left, right, _ = alignment(original, simple)
    sites = sites if sites is not None else edit_sites(original, simple, "delete")
    site = choose(seed, pair_id, "OMIT", sites)
    if site is None:
        return None
    i1, i2, j1, _ = site
    inserted = left[i1:i2]
    degraded = detokenize(right[:j1] + inserted + right[j1:]) if lang == "en" else splice(original, simple, [("insert", site)])
    return {"degraded": degraded, "span": inserted, "site": site}


def generate_syn(original: str, simple: str, pair_id: str, seed: int, sites=None, lang: str = "en") -> dict | None:
    left, right, _ = alignment(original, simple)
    sites = sites if sites is not None else edit_sites(original, simple, "replace")
    site = choose(seed, pair_id, "SYN", sites)
    if site is None:
        return None
    i1, i2, j1, j2 = site
    degraded = detokenize(right[:j1] + left[i1:i2] + right[j2:]) if lang == "en" else splice(original, simple, [("replace", site)])
    return {"degraded": degraded, "restored": left[i1:i2], "simple_span": right[j1:j2], "site": site}


def generate_expl(original: str, simple: str, pair_id: str, seed: int, sites=None, lang: str = "en") -> dict | None:
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
    if lang == "en":
        degraded = detokenize(kept)
    else:
        degraded = splice(original, simple, [("delete", site)])
        degraded = re.sub(r",(\s*),", r",", degraded)  # the gloss sat between two commas
    degraded = re.sub(r"\(\s*\)", "", degraded)
    dangling = {"en": r"which|a", "es": r"que|el|la|un|una", "fr": r"qui|que|le|la|un|une"}[lang]
    degraded = re.sub(rf",\s*(?:{dangling})\s*([,.;])", r"\1", degraded, flags=re.I)
    pattern = explanatory_pattern(right[:j1], removed, right[j2:], lang)
    if pattern is None:
        return None
    return {"degraded": degraded.strip(), "removed": removed, "site": site, "expl_pattern": pattern}
