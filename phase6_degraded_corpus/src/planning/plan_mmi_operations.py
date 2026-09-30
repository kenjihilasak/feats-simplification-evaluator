#!/usr/bin/env python3
"""Plan one v2 degradation operation per MMI split row (plan §3).

MEANING picks one factual span; number/date spans are corrupted here by rule, the other
types are left for the LLM. MOD picks one adjacent Simplified sentence pair to merge.
ILLOC balances question / directive / hedged injections within each cell. The same plan
feeds C1–C4; `--c0-dir` also writes v1-format manifests so C0 runs the frozen v1 scripts
on identical pairs and targets.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl
from phase6_degraded_corpus.src.planning.multi_axis import detect_illocution
from phase6_degraded_corpus.src.planning.plan_meaning_corruptions import detect

MEANING_TYPES = ("number", "date", "entity", "negation", "event", "property", "relation")
RULE_TYPES = {"number", "date", "negation"}
ILLOC_OPERATIONS = ("assertion_to_question", "assertion_to_directive", "assertion_to_hedged")
MONTHS = (
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
)
YEAR = re.compile(r"^(?:1[5-9]\d{2}|20\d{2})$")
SENTENCE_BOUNDARY = re.compile(
    r"(?<!\b[A-Z]\.)(?<!\bMr\.)(?<!\bMrs\.)(?<!\bDr\.)(?<!\bSt\.)(?<!\bJr\.)(?<!\bSr\.)"
    r"(?<=[.!?])[\"”)]?\s+(?=[\"“(]?[A-Z0-9])"
)
V1_CORRUPTION = {
    "number": "number_replacement", "date": "date_replacement", "entity": "entity_replacement",
    "negation": "negation_reversal", "event": "event_replacement",
    "property": "property_replacement", "relation": "relation_reversal",
}


def split_sentences(text: str) -> list[str]:
    return [part for part in SENTENCE_BOUNDARY.split(text.strip()) if part]


def _hash_int(seed: int, value: str) -> int:
    return int(stable_key(seed, value)[:12], 16)


def meaning_candidates(text: str) -> dict[str, list[dict]]:
    """Typed cues from the v1 detector, without placeholder or sentence-initial cues."""
    found = detect(text)
    usable = lambda cues: [cue for cue in cues if cue.get("start") is not None]
    negation_words = [c for c in usable(found["negation_reversal"]) if c["text"].lower() in {"not", "never", "no"}]
    months = "|".join(MONTHS)

    def safe_number(cue: dict) -> bool:
        before, after = text[: cue["start"]], text[cue["end"] :]
        if re.search(rf"(?:{months})\s*$", before) or re.match(rf"\s*(?:{months})\b", after):
            return False  # day of month ("20 March", "April 26")
        if re.search(r"[A-Z][\w-]*\s*$", before) and not re.search(r"(?:^|[.;:(,]\s*)$", before):
            return False  # part of a name ("Voyager 2", "World War 2")
        if re.match(r"\s*(?:to|-|–|—|and)\s*\d", after) or re.search(r"\d\s*(?:to|-|–|—|and)\s*$", before):
            return False  # one end of a range ("2,000 to 3,000")
        return True

    return {
        "number": [cue for cue in usable(found["number_replacement"]) if safe_number(cue)],
        "date": usable(found["date_replacement"]),
        "entity": usable(found["entity_replacement"]),
        "negation": negation_words or usable(found["negation_reversal"]),
        "event": [extend_auxiliary(text, c) for c in usable(found["event_replacement"]) if c["text"] != "central event"],
        # Lowercase only (not "New" in "New York"), and not the "old" of "21 years old".
        "property": [c for c in usable(found["property_replacement"])
                     if c["text"].islower() and not re.search(r"\byears?\s*$", text[: c["start"]])],
        # A relation flip on a clause that already has a negation yields "not no …": use negation instead.
        "relation": [] if NEGATED.search(text) else usable(found["relation_reversal"]),
    }


NEGATED = re.compile(r"\b(?:not|never|no|n't)\b", re.I)


def extend_auxiliary(text: str, cue: dict) -> dict:
    """Include a preceding auxiliary in an event span ("was born" -> "died", not "was died")."""
    match = re.search(r"\b(?:was|were|is|are|has been|have been|had been)\s+$", text[: cue["start"]])
    if not match:
        return cue
    return {"text": text[match.start() : cue["end"]], "start": match.start(), "end": cue["end"]}


def corrupt_number(text: str, original: str, seed: int, key: str) -> str | None:
    """Scale a number while keeping its surface format; never reuse a number of the Original."""
    percent = text.endswith("%")
    core = text.rstrip("%")
    decimals = len(core.split(".", 1)[1]) if "." in core and "," not in core else 0
    try:
        value = float(core.replace(",", ""))
    except ValueError:
        return None
    factors = (2, 3, 10) if value < 1000 else (2, 3, 0.5)
    start = _hash_int(seed, key)
    for offset in range(len(factors)):
        new = value * factors[(start + offset) % len(factors)]
        if decimals:
            rendered = f"{new:.{decimals}f}"
        elif "," in core:
            rendered = f"{int(round(new)):,}"
        else:
            rendered = str(int(round(new)))
        rendered += "%" if percent else ""
        if rendered != text and rendered not in original:
            return rendered
    return None


def corrupt_date(text: str, original: str, seed: int, key: str) -> str | None:
    if text in MONTHS:
        start = _hash_int(seed, key)
        for offset in range(1, 12):
            month = MONTHS[(MONTHS.index(text) + 1 + (start + offset) % 11) % 12]
            if month != text and month not in original:
                return month
        return None
    if not YEAR.match(text):
        return None
    year = int(text)
    start = _hash_int(seed, key)
    for offset in range(38):
        shift = 3 + (start + offset) % 38
        for candidate in (year - shift, year + shift):
            if 1000 <= candidate <= 2025 and str(candidate) not in original:
                return str(candidate)
    return None


ADVERBS_AFTER_AUX = {"also", "always", "often", "still", "already", "usually", "now", "only", "sometimes", "mainly", "mostly"}
DO_SUPPORT = {"has": "does not have", "have": "do not have", "had": "did not have"}
NEGATABLE_AUX = {"is", "are", "was", "were", "can", "could", "will", "would", "should", "must", "may", "might",
                 "does", "do", "did", "has", "have", "had"}
PARTICIPLE = re.compile(r"^(?:been|\w+ed|\w+en|got|made|built|won|lost|become|come|gone|done|seen|found|held|led|left|put|set|told|known|written|taken|given|born)$", re.I)


def negate(text: str, cue: dict) -> str | None:
    """Flip polarity at the cue deterministically, or return None when no safe rule applies."""
    word = cue["text"].lower()
    before, after = text[: cue["start"]], text[cue["end"] :]
    if word in {"not", "never"}:
        return re.sub(r"\s{2,}", " ", before.rstrip() + " " + after.lstrip()).strip()
    if word == "no":
        return before + "some" + after if cue["text"].islower() else None
    if word not in NEGATABLE_AUX or re.match(r"\s+(?:not|never|no)\b|n't", after, re.I):
        return None
    next_word = (re.match(r"\s+([\w'-]+)", after) or [None, ""])[1]
    if re.search(r"\bthere\s+$", before, re.I) and word in {"is", "are", "was", "were"}:
        # "there were X" -> "there were no X"; drop a leading a/an/some.
        rest = re.sub(r"^\s+(?:a|an|some|several)\b", "", after, flags=re.I)
        return before + cue["text"] + " no" + (rest if rest.startswith(" ") else " " + rest.lstrip())
    if word in DO_SUPPORT and not PARTICIPLE.match(next_word):
        return before + DO_SUPPORT[word] + after
    if next_word.lower() in ADVERBS_AFTER_AUX:  # "was also" -> "was also not"
        m = re.match(r"(\s+[\w'-]+)", after)
        return before + cue["text"] + m.group(1) + " not" + after[m.end():]
    return before + cue["text"] + " not" + after


def fix_articles(text: str) -> str:
    """Make a/an agree with the next word (sound approximated by spelling; common exceptions handled)."""
    return re.sub(r"\b([Aa]n?)(\s+)([A-Za-z])", _article, text)


def _article(m: re.Match) -> str:
    article, space, first = m.group(1), m.group(2), m.group(3)
    rest = re.match(r"[A-Za-z]\w*", m.string[m.start(3):]).group(0).lower()
    vowel = rest[0] in "aeiou" and not re.match(r"^(?:uni|use|usu|uti|eu|one|once)", rest)
    vowel = vowel or re.match(r"^(?:hour|honest|honou?r|heir)", rest) is not None
    wanted = "an" if vowel else "a"
    if article.lower() == wanted:
        return m.group(0)
    return (wanted.capitalize() if article[0].isupper() else wanted) + space + first


def splice(text: str, start: int, end: int, replacement: str) -> str:
    left, right = text[:start], text[end:]
    if not replacement:
        left = left.rstrip() if right[:1] in {",", ".", ";", ":", ""} else left
        return re.sub(r"\s{2,}", " ", left + (" " if left and right and not right.startswith(" ") else "") + right.lstrip(" ")).strip()
    return left + replacement + right


def plan_meaning(rows: list[dict], seed: int) -> list[dict]:
    counts: Counter = Counter()
    planned = []
    for row in sorted(rows, key=lambda r: stable_key(seed, r["canonical_pair_id"])):
        cues = meaning_candidates(row["clean_simplification"])
        original_cf = row["original"].casefold()
        # A factual span must be supported by the Original, otherwise corrupting it cannot
        # contradict the Original. Negation/relation cues are function words and are exempt.
        for kind in ("number", "date", "entity", "event", "property"):
            cues[kind] = [c for c in cues[kind] if c["text"].casefold() in original_cf]
        applicable = [kind for kind in MEANING_TYPES if cues[kind]]
        if not applicable:
            planned.append({**row, "operation": None, "plan_status": "no_applicable_cue"})
            continue
        # Balance types within the cell; rule types stay but do not crowd out LLM types.
        kind = min(applicable, key=lambda k: (counts[k], stable_key(seed, f'{row["canonical_pair_id"]}:{k}')))
        cue = min(cues[kind], key=lambda c: stable_key(seed, f'{row["canonical_pair_id"]}:{kind}:{c["start"]}'))
        rule_output = None
        if kind == "negation":
            # v2.1: rule-based polarity flip (heldout audit: LLM negations were often ungrammatical).
            degraded = negate(row["clean_simplification"], cue)
            if degraded is not None:
                rule_output = {"replacement": None, "degraded": fix_articles(degraded)}
        elif kind in RULE_TYPES:
            corrupt = corrupt_number if kind == "number" else corrupt_date
            replacement = corrupt(cue["text"], row["original"], seed, row["canonical_pair_id"])
            if replacement is None:
                fallback = [k for k in applicable if k not in RULE_TYPES]
                if not fallback:
                    planned.append({**row, "operation": None, "plan_status": "rule_corruption_impossible"})
                    continue
                kind = min(fallback, key=lambda k: (counts[k], k))
                cue = cues[kind][0]
            else:
                rule_output = {
                    "replacement": replacement,
                    "degraded": fix_articles(splice(row["clean_simplification"], cue["start"], cue["end"], replacement)),
                }
        counts[kind] += 1
        planned.append({
            **row,
            "operation": f"meaning_{kind}",
            "meaning_type": kind,
            "generator_kind": "rule" if rule_output else "llm",
            "target_span": {"text": cue["text"], "start": cue["start"], "end": cue["end"]},
            "rule_output": rule_output,
            "plan_status": "ready",
        })
    return planned


def plan_mod(rows: list[dict], seed: int) -> list[dict]:
    planned = []
    for row in rows:
        sentences = split_sentences(row["clean_simplification"])
        if len(sentences) < 2:
            planned.append({**row, "operation": None, "plan_status": "fewer_than_two_sentences"})
            continue
        index = min(range(len(sentences) - 1), key=lambda i: stable_key(seed, f'{row["canonical_pair_id"]}:{i}'))
        planned.append({
            **row,
            "operation": "recombine_split",
            "generator_kind": "llm",
            "sentences": sentences,
            "merge_index": index,
            "plan_status": "ready",
        })
    return planned


def plan_illoc(rows: list[dict], seed: int) -> list[dict]:
    ordered = sorted(rows, key=lambda r: stable_key(seed, r["canonical_pair_id"]))
    return [
        {
            **row,
            "operation": ILLOC_OPERATIONS[position % len(ILLOC_OPERATIONS)],
            "generator_kind": "llm",
            "plan_status": "ready",
        }
        for position, row in enumerate(ordered)
    ]


def v1_manifests(planned: list[dict]) -> tuple[list[dict], list[dict]]:
    """C0 inputs in the frozen v1 formats: MEANING plan rows and multi-axis manifest rows."""
    meaning, other = [], []
    for row in planned:
        if row.get("plan_status") != "ready":
            continue
        base = {
            "canonical_pair_id": row["canonical_pair_id"],
            "canonical_original_id": row["canonical_original_id"],
            "original": row["original"],
            "clean_simplification": row["clean_simplification"],
            "target_axis": row["target_axis"],
        }
        if row["target_axis"] == "MEANING":
            meaning.append({
                **base,
                "predicted_strategy": None,
                "target_score": 0.0,
                "assigned_corruption": V1_CORRUPTION[row["meaning_type"]],
                "target_cue": row["target_span"],
                "generation_status": "ready",
            })
        elif row["target_axis"] == "MOD":
            other.append({
                **base, "source_strategy": "MOD",
                "assigned_operation": "reverse_information_restructuring",
                "target_cue": {"text": "sentence structure", "start": None, "end": None},
            })
        else:
            cues = detect_illocution(row["original"], row["clean_simplification"])
            cue = min(cues, key=lambda c: stable_key(0, f'{c["operation"]}:{c["text"]}')) if cues else {
                "operation": "certainty_reversal", "text": "assertion", "start": None, "end": None,
            }
            other.append({
                **base, "source_strategy": None,
                "assigned_operation": cue["operation"],
                "target_cue": {k: cue[k] for k in ("text", "start", "end")},
                "v1_cue_fallback": not cues,
            })
    return meaning, other


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", type=Path, required=True, help="dev.jsonl or heldout.jsonl")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260930)
    parser.add_argument("--c0-dir", type=Path)
    args = parser.parse_args()
    rows = read_jsonl(args.split)
    by_cell: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        by_cell[(row["target_axis"], row["corpus"])].append(row)
    planned = []
    for (axis, _corpus), cell in sorted(by_cell.items()):
        planner = {"MEANING": plan_meaning, "MOD": plan_mod, "ILLOC": plan_illoc}[axis]
        planned.extend(planner(cell, args.seed))
    planned.sort(key=lambda r: r["canonical_pair_id"])
    for row in planned:
        row["plan_schema"] = "feats-phase6-mmi-plan-v2"
    write_jsonl(args.output, planned)
    report = {
        "rows": len(planned),
        "status": dict(Counter(r["plan_status"] for r in planned)),
        "operations": dict(Counter(f'{r["target_axis"]}:{r.get("operation")}' for r in planned)),
        "generator_kind": dict(Counter(str(r.get("generator_kind")) for r in planned)),
    }
    if args.c0_dir:
        meaning, other = v1_manifests(planned)
        write_jsonl(args.c0_dir / "meaning_plan.jsonl", meaning)
        write_jsonl(args.c0_dir / "multi_axis_manifest.jsonl", other)
        report["c0"] = {"meaning": len(meaning), "mod_illoc": len(other),
                        "illoc_v1_cue_fallback": sum(r.get("v1_cue_fallback", False) for r in other)}
    args.output.with_suffix(".report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
