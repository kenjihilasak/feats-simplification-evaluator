#!/usr/bin/env python3
"""Build the deterministic MEANING/MOD/ILLOC source pools for mmi_en_v2."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl
from phase6_degraded_corpus.src.selection.freeze_evaluation_originals import strong_key

TOKEN = re.compile(r"\w+(?:[-’']\w+)*|[^\w\s]", re.UNICODE)
WORD = re.compile(r"[^\W_]+", re.UNICODE)
NUMBER = re.compile(r"\b\d+(?:[.,]\d+)?%?\b")
MONTHS = {
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
}
NEGATIONS = {"no", "not", "never", "neither", "nor", "without", "n't"}
BAD_PREFIXES = ("file:", "category:", "template:", "image:")
AXES = ("MEANING", "MOD", "ILLOC")
PRIORITY = ("MOD", "MEANING", "ILLOC")
CORPORA = ("WikiAutoEN", "ASSET", "Wikipedia-Vikidia")


def words(text: str) -> set[str]:
    return {token.casefold() for token in WORD.findall(text)}


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


class ReservedMatcher:
    def __init__(self, rows: list[dict], threshold: float = 0.8):
        self.threshold = threshold
        self.by_key = {row["strong_key"]: row["original"] for row in rows}
        self.word_sets = {key: words(text) for key, text in self.by_key.items()}
        self.index: dict[str, set[str]] = defaultdict(set)
        for key, tokens in self.word_sets.items():
            for token in tokens:
                self.index[token].add(key)

    def match(self, text: str) -> dict | None:
        key = strong_key(text)
        if key in self.by_key:
            return {"type": "exact", "score": 1.0, "reserved_original": self.by_key[key]}
        tokens = words(text)
        candidates: set[str] = set()
        for token in tokens:
            candidates.update(self.index.get(token, ()))
        best_key = None
        best_score = 0.0
        for candidate in candidates:
            score = jaccard(tokens, self.word_sets[candidate])
            if score > best_score:
                best_key, best_score = candidate, score
        if best_key is not None and best_score >= self.threshold:
            return {
                "type": "near",
                "score": best_score,
                "reserved_original": self.by_key[best_key],
            }
        return None


def assert_materializable(row: dict) -> None:
    if row.get("usage") == "reserved_evaluation":
        raise ValueError("reserved evaluation rows cannot be materialized")


def corpus_of(row: dict) -> str | None:
    corpora = row.get("corpora") or []
    if len(corpora) != 1:
        return None
    return corpora[0].get("corpus")


def alignment_features(original: str, simplified: str) -> dict:
    original_tokens = [x.casefold() for x in TOKEN.findall(original)]
    simple_tokens = [x.casefold() for x in TOKEN.findall(simplified)]
    matcher = difflib.SequenceMatcher(None, original_tokens, simple_tokens, autojunk=False)
    return {
        "overlap": matcher.ratio(),
        "len_ratio": len(simple_tokens) / len(original_tokens) if original_tokens else 0.0,
        "edit_blocks": sum(1 for tag, *_ in matcher.get_opcodes() if tag != "equal"),
        "original_tokens": len(original_tokens),
    }


def sentence_count(text: str) -> int:
    chunks = [part for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part]
    return max(1, len(chunks))


def meaning_cues(text: str) -> list[str]:
    cues = []
    tokens = text.split()
    lowered = {token.strip(".,;:!?()[]{}\"'").casefold() for token in tokens}
    if NUMBER.search(text):
        cues.append("number")
    if lowered & MONTHS:
        cues.append("date")
    if lowered & NEGATIONS or "n't" in text.casefold():
        cues.append("negation")
    for index, token in enumerate(tokens):
        clean = token.strip(".,;:!?()[]{}\"'")
        if index > 0 and clean[:1].isupper() and any(char.isalpha() for char in clean):
            cues.append("entity")
            break
    return cues


def eligible_axes(row: dict) -> dict[str, dict]:
    original = row["original"].strip()
    simplified = row["simple"].strip()
    features = alignment_features(original, simplified)
    result = {}
    cues = meaning_cues(simplified)
    if (
        features["overlap"] >= 0.4
        and 0.5 <= features["len_ratio"] <= 1.6
        and features["edit_blocks"] <= 4
        and cues
    ):
        result["MEANING"] = {"cue_types": cues, **features}
    if (
        sentence_count(simplified) > sentence_count(original)
        and features["overlap"] >= 0.6
        and 0.8 <= features["len_ratio"] <= 1.4
    ):
        result["MOD"] = features
    if (
        features["overlap"] >= 0.4
        and 0.5 <= features["len_ratio"] <= 1.6
        and features["edit_blocks"] <= 4
        and simplified.endswith(".")
        and "?" not in simplified
    ):
        result["ILLOC"] = features
    return result


def build_pools(config: dict) -> tuple[dict[tuple[str, str], list[dict]], dict]:
    strategy = {
        row["canonical_pair_id"]: row
        for row in read_jsonl(Path(config["strategy_file"]))
    }
    reserved_rows = read_jsonl(Path(config["reserved_membership_file"]))
    matcher = ReservedMatcher(reserved_rows, config["near_duplicate_jaccard"])
    counters = Counter()
    near_matches = []
    exact_matches = []
    candidates: dict[str, list[tuple[str, dict, dict]]] = defaultdict(list)
    allowed = set(config["corpora"])

    seen_pairs = set()
    for row in read_jsonl(Path(config["phase2b_file"])):
        pair_id = row["canonical_pair_id"]
        if pair_id in seen_pairs:
            raise ValueError(f"duplicate canonical_pair_id: {pair_id}")
        seen_pairs.add(pair_id)
        counters["input"] += 1
        if row.get("repaired_duplicate_of"):
            counters["repaired_duplicate"] += 1
            continue
        corpus = corpus_of(row)
        if corpus not in allowed:
            counters["corpus"] += 1
            continue
        original = row.get("original", "").strip()
        simplified = row.get("simple", "").strip()
        match = matcher.match(original)
        if match:
            excluded = {
                "canonical_pair_id": pair_id,
                "canonical_original_id": row["canonical_original_id"],
                "corpus": corpus,
                "original": original,
                "reserved_original": match["reserved_original"],
                "reserved_match": match["type"],
                "jaccard": round(match["score"], 6),
                "usage": "reserved_evaluation",
            }
            (exact_matches if match["type"] == "exact" else near_matches).append(excluded)
            counters[f"reserved_{match['type']}"] += 1
            continue
        if not original or not simplified:
            counters["empty"] += 1
            continue
        if strong_key(original) == strong_key(simplified):
            counters["identical"] += 1
            continue
        if original.casefold().startswith(BAD_PREFIXES) or simplified.casefold().startswith(BAD_PREFIXES):
            counters["markup"] += 1
            continue
        length = len(TOKEN.findall(original))
        if not config["original_token_range"][0] <= length <= config["original_token_range"][1]:
            counters["length"] += 1
            continue
        axes = eligible_axes(row)
        if corpus == "Wikipedia-Vikidia" and "MOD" not in axes:
            fallback = alignment_features(original, simplified)
            if (
                sentence_count(simplified) > sentence_count(original)
                and fallback["overlap"] >= 0.4
                and 0.5 <= fallback["len_ratio"] <= 1.6
            ):
                axes["MOD"] = {**fallback, "fallback": True}
        if not axes:
            counters["no_axis"] += 1
            continue
        metadata = strategy.get(pair_id)
        strategy_code = metadata.get("candidate_strategy_code") if metadata else None
        base = {
            "schema": "feats-phase6-mmi-pool-v1",
            "canonical_pair_id": pair_id,
            "canonical_original_id": row["canonical_original_id"],
            "language": "en",
            "original": original,
            "clean_simplification": simplified,
            "original_raw": row.get("original_raw"),
            "clean_simplification_raw": row.get("simple_raw"),
            "glue_repaired": bool(row.get("text_repaired")),
            "source": row["corpora"][0].get("source"),
            "corpus": corpus,
            "source_strategy": strategy_code,
            "source_strategy_count": 1 if strategy_code else 0,
            "phase3a_quality_tier": metadata.get("quality_tier") if metadata else None,
            "usage": "pipeline_selection",
        }
        for axis, details in axes.items():
            candidates[row["canonical_original_id"]].append((axis, base, details))

    selected: dict[tuple[str, str], list[dict]] = {(a, c): [] for a in AXES for c in CORPORA}
    for original_id, choices in candidates.items():
        choices.sort(
            key=lambda item: (
                PRIORITY.index(item[0]),
                stable_key(config["seed"], item[1]["canonical_pair_id"]),
            )
        )
        axis, base, details = choices[0]
        output = {**base, "target_axis": axis, "selection_features": details}
        selected[(axis, base["corpus"])].append(output)

    # ASSET references and any remaining repeated original are reduced deterministically.
    for cell, rows in selected.items():
        by_original: dict[str, dict] = {}
        for row in rows:
            key = row["canonical_original_id"]
            previous = by_original.get(key)
            if previous is None or stable_key(config["seed"], row["canonical_pair_id"]) < stable_key(
                config["seed"], previous["canonical_pair_id"]
            ):
                by_original[key] = row
        selected[cell] = sorted(by_original.values(), key=lambda row: row["canonical_pair_id"])

    report = {
        "schema": "feats-phase6-mmi-pool-report-v1",
        "experiment_id": config["experiment_id"],
        "quality_gates": "pending NLI and acceptability checker stage",
        "filters": dict(sorted(counters.items())),
        "reserved": {
            "exact_count": len(exact_matches),
            "near_count": len(near_matches),
            "near_duplicate_jaccard": config["near_duplicate_jaccard"],
            "exact_matches": exact_matches,
            "near_matches": near_matches,
        },
        "cells": {},
    }
    for (axis, corpus), rows in selected.items():
        report["cells"][f"{axis}_{corpus}"] = {
            "records": len(rows),
            "unique_originals": len({row["canonical_original_id"] for row in rows}),
            "source_strategy_count": dict(
                sorted(Counter(str(row["source_strategy_count"]) for row in rows).items())
            ),
            "source_strategy": dict(
                sorted(Counter(row["source_strategy"] or "null" for row in rows).items())
            ),
            "underpowered": len(rows) < 60,
        }
    return selected, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    pools, report = build_pools(config)
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    for (axis, corpus), rows in pools.items():
        write_jsonl(output_dir / f"{axis.lower()}_{corpus.lower().replace('-', '_')}.jsonl", rows)
    report["input_sha256"] = hashlib.sha256(Path(config["phase2b_file"]).read_bytes()).hexdigest()
    (output_dir / "pool_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: value["records"] for key, value in report["cells"].items()}, indent=2))


if __name__ == "__main__":
    main()
