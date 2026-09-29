#!/usr/bin/env python3
"""Create an immutable Phase 2b text-repair variant."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

REPAIR_VERSION = "feats-text-repair-v1.1"
R1_LANGUAGES = {"en", "es", "fr", "it", "ca", "de", "pt-BR", "ru", "sl"}
BLOCKED_LANGUAGES = {"ja", "ur", "ar"}
ABBREVIATIONS = {
    value.casefold() for value in (
        "Dr Mr Mrs Ms Jr Sr St Mt Ft Prof Gen Col Lt Capt Sgt Rev Hon Gov Sen Rep "
        "Inc Ltd Co Corp Vol Fig No Nr Art pp vs etc cf ca approx Jan Feb Mar Apr "
        "Jun Jul Aug Sep Sept Oct Nov Dec av ap Sig Sra Sr Dña Dott Ing Avv "
        "ул г гг др им т св"
    ).split()
}
EXTENSIONS = {
    "net", "com", "org", "edu", "gov", "exe", "txt", "html", "php",
    "jpg", "jpeg", "png", "svg", "gif", "pdf",
}
PTB_BRACKETS = {
    "-LRB-": "(", "-RRB-": ")", "-LSB-": "[", "-RSB-": "]",
    "-LCB-": "{", "-RCB-": "}",
}
OPEN_BRACKETS = {"(", "[", "{"}
CLOSE_BRACKETS = {")", "]", "}"}
R1_CANDIDATE = re.compile(
    r"(?:(?P<word>(?<![\w])[^\W_]{2,})|"
    r"(?P<close>[\)\]\u201d\u00bb\"]))"
    r"(?P<punct>[.!?](?:[\"\u201d\u00bb])?)"
    r"(?P<opening>[\"\u201c\u00ab\(\[]?)(?P<right>[^\W\d_]+)",
    re.UNICODE,
)
LOOSE_BOUNDARY = re.compile(r"\w[.!?][A-Z\u00c0-\u00de\u0400-\u042f]")
ENGLISH_RECALL_PATTERN = re.compile(r"[a-z]{2,}[.!?][A-Z][a-z]")
DETOK_PATTERNS = {
    "space_before_period_or_comma": re.compile(r"\w\s+[.,]"),
    "space_after_open_bracket": re.compile(r"[\(\[\{]\s+\w"),
    "space_before_close_bracket": re.compile(r"\w\s+[\)\]\}]"),
}


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}: {exc}") from exc


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def repaired_key(language: str, original: str, simple: str) -> bytes:
    digest = hashlib.sha256()
    for value in (language, original, simple):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.digest()


def _apply_r2(text: str, field: str) -> tuple[str, list[dict], list[int | None]]:
    repairs: list[dict] = []
    items: list[dict] = []
    index = 0
    token_re = re.compile("|".join(re.escape(token) for token in PTB_BRACKETS))
    for match in token_re.finditer(text):
        items.extend({"char": text[i], "origin": i, "created": False} for i in range(index, match.start()))
        replacement = PTB_BRACKETS[match.group(0)]
        items.append({"char": replacement, "origin": match.start(), "created": True})
        repairs.append({
            "field": field, "rule": "R2_ptb_bracket", "offset_raw": match.start(),
            "raw_token": match.group(0), "replacement": replacement,
        })
        index = match.end()
    items.extend({"char": text[i], "origin": i, "created": False} for i in range(index, len(text)))

    # Clean only around opening brackets created by R2.
    index = 0
    while index < len(items):
        item = items[index]
        if not (item["created"] and item["char"] in OPEN_BRACKETS):
            index += 1
            continue
        if index > 0 and items[index - 1]["char"].isalnum():
            items.insert(index, {"char": " ", "origin": None, "created": False})
            index += 1
        while index + 1 < len(items) and items[index + 1]["char"].isspace():
            del items[index + 1]
        if index + 1 < len(items) and items[index + 1]["char"] in {",", ";"}:
            del items[index + 1]
            while index + 1 < len(items) and items[index + 1]["char"].isspace():
                del items[index + 1]
        index += 1

    # Remove tokenizer whitespace before closing brackets created by R2.
    index = 0
    while index < len(items):
        item = items[index]
        if item["created"] and item["char"] in CLOSE_BRACKETS:
            while index > 0 and items[index - 1]["char"].isspace():
                del items[index - 1]
                index -= 1
        index += 1

    # Remove empty bracket pairs created by R2 and their preceding space.
    matching = {"(": ")", "[": "]", "{": "}"}
    index = 0
    while index + 1 < len(items):
        left, right = items[index], items[index + 1]
        if (left["created"] and right["created"]
                and left["char"] in matching and right["char"] == matching[left["char"]]):
            del items[index:index + 2]
            if index > 0 and items[index - 1]["char"].isspace():
                del items[index - 1]
                index -= 1
            continue
        index += 1

    return ("".join(item["char"] for item in items), repairs,
            [item["origin"] for item in items])

def _valid_right(word: str, following: str, language: str) -> bool:
    if word.casefold() in EXTENSIONS:
        return False
    if len(word) >= 2 and word[0].isupper() and any(char.islower() for char in word[1:]):
        pass
    elif len(word) == 1 and (
        (language == "en" and word in {"A", "I"})
        or (language == "ru" and word in {"В", "С", "К", "О", "У", "Я"})
    ) and following[:1].isspace():
        pass
    else:
        return False
    if following.startswith(".") and len(following) > 1 and following[1].isalpha():
        return False
    return True


def _apply_r1(text: str, origins: list[int | None], language: str, field: str) -> tuple[str, list[dict]]:
    if language not in R1_LANGUAGES:
        return text, []
    repairs: list[dict] = []
    pieces: list[str] = []
    cursor = 0
    for match in R1_CANDIDATE.finditer(text):
        word, close = match.group("word"), match.group("close")
        left = word or close
        if match.start() > 0 and text[match.start() - 1] in "/@\\":
            continue
        if word and not ((word[-1].islower() or word[-1].isdigit())
                         and word.casefold() not in ABBREVIATIONS):
            continue
        right = match.group("right")
        if not _valid_right(right, text[match.end("right"):], language):
            continue
        insertion = match.end("punct")
        punct = match.group("punct")
        opening = match.group("opening")
        if punct.endswith("\"") and text[:insertion - 1].count("\"") % 2 == 0:
            insertion -= 1
            punct = punct[:-1]
            opening = "\"" + opening
        pieces.append(text[cursor:insertion]); pieces.append(" ")
        raw_origin = origins[insertion - 1] if insertion and insertion - 1 < len(origins) else None
        repairs.append({
            "field": field, "rule": "R1_glued_sentence",
            "offset_raw": None if raw_origin is None else raw_origin + 1,
            "left": left + punct,
            "right": opening + right,
        })
        cursor = insertion
    pieces.append(text[cursor:])
    return "".join(pieces), repairs


def repair_field(text: str, language: str, field: str) -> tuple[str, list[dict]]:
    if language in BLOCKED_LANGUAGES:
        return text, []
    r2_text, r2_repairs, origins = _apply_r2(text, field)
    repaired, r1_repairs = _apply_r1(r2_text, origins, language, field)
    return repaired, r2_repairs + r1_repairs


def repair_record(record: dict) -> dict:
    language = record["language"]
    original_raw, simple_raw = record["original"], record["simple"]
    original, original_repairs = repair_field(original_raw, language, "original")
    simple, simple_repairs = repair_field(simple_raw, language, "simple")
    repairs = original_repairs + simple_repairs
    return {
        **record,
        "original": original,
        "simple": simple,
        "original_raw": original_raw,
        "simple_raw": simple_raw,
        "original_raw_sha256": text_sha256(original_raw),
        "simple_raw_sha256": text_sha256(simple_raw),
        "text_repair_version": REPAIR_VERSION,
        "text_repairs": repairs,
        "text_repaired": bool(repairs),
        "repaired_duplicate_of": None,
    }


def corpus_labels(record: dict) -> list[str]:
    values = [item.get("corpus") for item in record.get("corpora", []) if item.get("corpus")]
    return sorted(set(values)) or ["unknown"]


def reservoir_add(values: list, item, seen: int, limit: int, rng: random.Random) -> None:
    if len(values) < limit:
        values.append(item)
    else:
        index = rng.randrange(seen)
        if index < limit:
            values[index] = item


def context(text: str, offset: int | None, radius: int = 40) -> str:
    if offset is None:
        return text[: radius * 2].replace("\n", " ")
    return text[max(0, offset - radius): offset + radius].replace("\n", " ")


def process_file(input_path: Path, output_path: Path, stats: dict, audits: dict,
                 detok: dict, rng: random.Random) -> None:
    language = input_path.parent.name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(".jsonl.first-pass")
    key_min: dict[bytes, str] = {}
    with temporary.open("w", encoding="utf-8") as out:
        for row_index, record in enumerate(iter_jsonl(input_path), 1):
            repaired = repair_record(record)
            pair_id = repaired["canonical_pair_id"]
            if language == "en" and (ENGLISH_RECALL_PATTERN.search(repaired["original"])
                                      or ENGLISH_RECALL_PATTERN.search(repaired["simple"])):
                stats[(language, "__language__")]["remaining_strict_recall_rows"] += 1
            key = repaired_key(language, repaired["original"], repaired["simple"])
            current = key_min.get(key)
            if current is None or pair_id < current:
                key_min[key] = pair_id
            labels = corpus_labels(record)
            for corpus in labels:
                bucket = stats[(language, corpus)]
                bucket["pairs"] += 1
                if any(x["field"] == "original" for x in repaired["text_repairs"]):
                    bucket["repaired_originals"] += 1
                if any(x["field"] == "simple" for x in repaired["text_repairs"]):
                    bucket["repaired_simples"] += 1
                for repair in repaired["text_repairs"]:
                    bucket[repair["rule"]] += 1
            if repaired["text_repairs"]:
                for repair in repaired["text_repairs"]:
                    example = {
                        "language": language, "corpora": labels, "pair_id": pair_id,
                        "field": repair["field"], "rule": repair["rule"],
                        "before": context(record[repair["field"]], repair.get("offset_raw")),
                        "after": context(repaired[repair["field"]], repair.get("offset_raw")),
                    }
                    if repair["rule"] == "R1_glued_sentence":
                        if language == "en" and "WikiAutoEN" in labels:
                            audits["wiki_seen"] += 1
                            reservoir_add(audits["wiki"], example, audits["wiki_seen"], 200, rng)
                        else:
                            audits["other_r1"].append(example)
                    else:
                        audits["r2_seen"] += 1
                        reservoir_add(audits["r2"], example, audits["r2_seen"], 50, rng)
            elif LOOSE_BOUNDARY.search(record["original"]) or LOOSE_BOUNDARY.search(record["simple"]):
                audits["recall_seen"] += 1
                reservoir_add(audits["recall"], {
                    "language": language, "corpora": labels, "pair_id": pair_id,
                    "original": record["original"], "simple": record["simple"],
                }, audits["recall_seen"], 200, rng)
            for corpus in labels:
                for field in ("original", "simple"):
                    value = record[field]
                    for name, pattern in DETOK_PATTERNS.items():
                        if pattern.search(value):
                            detok[(language, corpus, name)]["count"] += 1
                            examples = detok[(language, corpus, name)]["examples"]
                            if len(examples) < 10:
                                examples.append({"pair_id": pair_id, "field": field, "text": value})
            out.write(json.dumps(repaired, ensure_ascii=False, sort_keys=True) + "\n")

    duplicates = 0
    with temporary.open(encoding="utf-8") as inp, output_path.with_suffix(".jsonl.tmp").open("w", encoding="utf-8") as out:
        for line in inp:
            record = json.loads(line)
            key = repaired_key(language, record["original"], record["simple"])
            minimum = key_min[key]
            if record["canonical_pair_id"] != minimum:
                record["repaired_duplicate_of"] = minimum
                duplicates += 1
            out.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(output_path.with_suffix(".jsonl.tmp"), output_path)
    temporary.unlink()
    stats[(language, "__language__")]["duplicates_created"] = duplicates


def render_audit(audits: dict) -> str:
    lines = [
        "# Text repair precision audit", "",
        "Mark exactly one checkbox per item. Stop before downstream use until the audit passes: ≥99% correct for English WikiAutoEN R1 and ≥95% elsewhere.", "",
    ]
    sections = [
        ("English WikiAutoEN R1 sample", audits["wiki"]),
        ("All non-WikiAutoEN R1 repairs", audits["other_r1"]),
        ("R2 PTB-bracket sample", audits["r2"]),
    ]
    for title, values in sections:
        lines += [f"## {title}", "", f"Items: **{len(values)}**", ""]
        for index, item in enumerate(values, 1):
            lines += [
                f"### {title} {index:03d}", "",
                f"- Pair: `{item['pair_id']}`", f"- Language: `{item['language']}`",
                f"- Corpora: `{', '.join(item['corpora'])}`", f"- Field: `{item['field']}`",
                f"- Rule: `{item['rule']}`", f"- Before: {item['before']}",
                f"- After: {item['after']}", "", "- [ ] Correct", "- [ ] Wrong", "- Note:", "",
            ]
    lines += ["## Possibly missed boundaries", "", f"Sample: **{len(audits['recall'])}**", ""]
    for index, item in enumerate(audits["recall"], 1):
        lines += [
            f"### Recall {index:03d}", "", f"- Pair: `{item['pair_id']}`",
            f"- Language: `{item['language']}`", f"- Original: {item['original']}",
            f"- Simplified: {item['simple']}", "", "- [ ] Missed repair", "- [ ] Correctly unchanged", "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def render_summary(stats: dict, input_root: Path, output_root: Path) -> str:
    lines = [
        "# Text repair summary", "",
        f"- Repair version: `{REPAIR_VERSION}`",
        f"- Input: `{input_root}`", f"- Output: `{output_root}`", "",
        "| Language | Corpus | Pairs | Repaired originals | Repaired simples | R1 repairs | R2 repairs |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for (language, corpus), values in sorted(stats.items()):
        if corpus == "__language__":
            continue
        lines.append(
            f"| {language} | {corpus} | {values['pairs']} | {values['repaired_originals']} | "
            f"{values['repaired_simples']} | {values['R1_glued_sentence']} | {values['R2_ptb_bracket']} |"
        )
    duplicates = sum(v["duplicates_created"] for (lang, corpus), v in stats.items() if corpus == "__language__")
    english_recall = stats[("en", "__language__")]["remaining_strict_recall_rows"]
    lines += ["", f"Repair-induced duplicates retained and marked: **{duplicates}**.",
              f"English rows still matching `[a-z]{{2,}}[.!?][A-Z][a-z]`: **{english_recall}**.", ""]
    return "\n".join(lines)


def render_detok(detok: dict) -> str:
    lines = ["# Detokenization audit", "", "Reported only; no automatic repair is applied.", "",
             "| Language | Corpus | Pattern | Matching field occurrences |", "|---|---|---|---:|"]
    for key, value in sorted(detok.items()):
        lines.append(f"| {key[0]} | {key[1]} | {key[2]} | {value['count']} |")
    for key, value in sorted(detok.items()):
        if not value["examples"]:
            continue
        lines += ["", f"## {key[0]} / {key[1]} / {key[2]}", ""]
        for item in value["examples"]:
            lines.append(f"- `{item['pair_id']}` ({item['field']}): {item['text']}")
    return "\n".join(lines).rstrip() + "\n"


def process_root(input_root: Path, output_root: Path, reports_root: Path, seed: int = 20260930) -> dict:
    files = sorted(input_root.glob("*/feats_consolidated.jsonl"))
    if not files:
        raise FileNotFoundError(f"no Phase 2b files under {input_root}")
    output_root.mkdir(parents=True, exist_ok=True); reports_root.mkdir(parents=True, exist_ok=True)
    stats = defaultdict(Counter)
    audits = {"wiki": [], "other_r1": [], "r2": [], "recall": [],
              "wiki_seen": 0, "r2_seen": 0, "recall_seen": 0}
    detok = defaultdict(lambda: {"count": 0, "examples": []})
    rng = random.Random(seed)
    for path in files:
        target = output_root / path.parent.name / path.name
        print(f"repairing {path} -> {target}", flush=True)
        process_file(path, target, stats, audits, detok, rng)
    summary = {
        "schema": "feats-text-repair-summary-v1", "repair_version": REPAIR_VERSION,
        "input_root": str(input_root), "output_root": str(output_root), "seed": seed,
        "files": len(files),
        "audit_counts": {key: len(audits[key]) for key in ("wiki", "other_r1", "r2", "recall")},
        "statistics": {f"{k[0]}::{k[1]}": dict(v) for k, v in sorted(stats.items())},
    }
    (reports_root / "text_repair_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (reports_root / "text_repair_summary.md").write_text(render_summary(stats, input_root, output_root), encoding="utf-8")
    (reports_root / "text_repair_audit.md").write_text(render_audit(audits), encoding="utf-8")
    (reports_root / "detokenization_audit.md").write_text(render_detok(detok), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--reports-root", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260930)
    args = parser.parse_args()
    result = process_root(args.input_root, args.output_root, args.reports_root, args.seed)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
