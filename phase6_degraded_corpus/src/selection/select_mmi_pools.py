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
from phase6_degraded_corpus.src.planning.plan_mmi_operations import split_sentences
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
    # Shared splitter: does not break after initials or common titles ("Thomas E. Donilon").
    return max(1, len(split_sentences(text)))


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


def load_phase3(config: dict) -> tuple[dict[str, dict[str, list[str]]], dict[str, int], set[str]]:
    per_pair: dict[str, dict[str, list[str]]] = defaultdict(dict)
    gemma_counts = {}
    for alias, filename in config["phase3a_prediction_files"].items():
        for row in read_jsonl(Path(filename)):
            pair_id = row["canonical_pair_id"]
            per_pair[pair_id][alias] = list(row.get("predicted_codes") or [])
            if alias == config["gemma_alias"]:
                gemma_counts[pair_id] = int(row.get("strategy_count", len(row.get("predicted_codes") or [])))
    strict = {
        row["canonical_pair_id"]
        for row in read_jsonl(Path(config["strict_candidate_file"]))
    }
    return per_pair, gemma_counts, strict


def prepare_candidates(config: dict) -> tuple[list[dict], dict]:
    phase3_codes, gemma_counts, strict = load_phase3(config)
    reserved_rows = read_jsonl(Path(config["reserved_membership_file"]))
    matcher = ReservedMatcher(reserved_rows, config["near_duplicate_jaccard"])
    all_rows = read_jsonl(Path(config["phase2b_file"]))
    asset_choice = {}
    for row in all_rows:
        if corpus_of(row) != "ASSET":
            continue
        original_id = row["canonical_original_id"]
        old = asset_choice.get(original_id)
        if old is None or stable_key(config["seed"], row["canonical_pair_id"]) < stable_key(
            config["seed"], old
        ):
            asset_choice[original_id] = row["canonical_pair_id"]

    counters = Counter()
    near_matches = []
    exact_matches = []
    candidates = []
    seen_pairs = set()
    for row in all_rows:
        pair_id = row["canonical_pair_id"]
        if pair_id in seen_pairs:
            raise ValueError(f"duplicate canonical_pair_id: {pair_id}")
        seen_pairs.add(pair_id)
        counters["input"] += 1
        if row.get("repaired_duplicate_of"):
            counters["repaired_duplicate"] += 1
            continue
        corpus = corpus_of(row)
        if corpus not in set(config["corpora"]):
            counters["corpus"] += 1
            continue
        if corpus == "ASSET" and asset_choice[row["canonical_original_id"]] != pair_id:
            counters["asset_reference_dedup"] += 1
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
        candidates.append(
            {
                "schema": "feats-phase6-mmi-candidate-v2",
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
                "eligible_axes": sorted(axes),
                "selection_features_by_axis": axes,
                "phase3a_predicted_codes": phase3_codes.get(pair_id, {}),
                "gemma_strategy_count": gemma_counts.get(pair_id),
                "strict_single_strategy_candidate": pair_id in strict,
                "usage": "pipeline_selection",
            }
        )
    candidates.sort(key=lambda row: row["canonical_pair_id"])
    report = {
        "schema": "feats-phase6-mmi-pool-report-v2",
        "experiment_id": config["experiment_id"],
        "filters_before_quality": dict(sorted(counters.items())),
        "reserved": {
            "exact_count": len(exact_matches),
            "near_count": len(near_matches),
            "near_duplicate_jaccard": config["near_duplicate_jaccard"],
            "exact_matches": exact_matches,
            "near_matches": near_matches,
        },
        "structural_candidates": len(candidates),
    }
    return candidates, report


def allocate_source(rows: list[dict], seed: int, quota: int) -> tuple[dict[str, list[dict]], dict]:
    allocated = {axis: [] for axis in AXES}
    remaining = list(rows)
    used_originals = set()
    pass1_counts = {}

    while True:
        deficits = {axis: max(0, quota - len(allocated[axis])) for axis in AXES}
        short = {axis for axis, deficit in deficits.items() if deficit}
        if not short:
            break
        available = [
            row for row in remaining
            if row["canonical_original_id"] not in used_originals
            and short.intersection(row["eligible_axes"])
        ]
        if not available:
            break
        supply = {
            axis: sum(axis in row["eligible_axes"] for row in available)
            for axis in short
        }
        available.sort(
            key=lambda row: (
                len(short.intersection(row["eligible_axes"])),
                stable_key(seed, row["canonical_pair_id"]),
            )
        )
        row = available[0]
        possible = short.intersection(row["eligible_axes"])
        axis = min(
            possible,
            key=lambda value: (
                -(deficits[value] / max(1, supply[value])),
                stable_key(seed, row["canonical_pair_id"] + value),
            ),
        )
        allocated[axis].append(
            {
                **row,
                "target_axis": axis,
                "selection_features": row["selection_features_by_axis"][axis],
                "allocation_pass": 1,
            }
        )
        used_originals.add(row["canonical_original_id"])

    pass1_counts = {axis: len(allocated[axis]) for axis in AXES}
    remaining.sort(key=lambda row: stable_key(seed, row["canonical_pair_id"]))
    for row in remaining:
        if row["canonical_original_id"] in used_originals:
            continue
        axis = next((value for value in PRIORITY if value in row["eligible_axes"]), None)
        if axis is None:
            continue
        allocated[axis].append(
            {
                **row,
                "target_axis": axis,
                "selection_features": row["selection_features_by_axis"][axis],
                "allocation_pass": 2,
            }
        )
        used_originals.add(row["canonical_original_id"])
    for rows_for_axis in allocated.values():
        rows_for_axis.sort(key=lambda row: row["canonical_pair_id"])
    return allocated, pass1_counts


def passes_nli_gate(score: dict, config: dict, exclusions: Counter) -> bool:
    """Apply the configured clean-input NLI gate and count what each criterion rejects.

    `non_contradiction` keeps elaborative simplifications (neutral w.r.t. the original);
    `entailment` is the stricter v2.0 gate, still reported for comparison.
    """
    mode = config.get("nli_gate", "entailment")
    if score["entailment"] < config["nli_entailment_threshold"]:
        exclusions["would_fail_entailment_gate"] += 1
    if mode == "entailment":
        if score["entailment"] < config["nli_entailment_threshold"]:
            exclusions["nli_entailment"] += 1
            return False
        return True
    if mode != "non_contradiction":
        raise ValueError(f"unknown nli_gate: {mode}")
    probabilities = score.get("nli_probabilities")
    if not probabilities:
        raise ValueError(f"non_contradiction gate needs nli_probabilities: {score['canonical_pair_id']}")
    if probabilities["contradiction"] >= config["nli_contradiction_threshold"]:
        exclusions["nli_contradiction"] += 1
        return False
    return True


def allocate_candidates(
    candidates: list[dict], scores: dict[str, dict], config: dict, base_report: dict
) -> tuple[dict[tuple[str, str], list[dict]], dict]:
    passed = []
    exclusions = Counter()
    for row in candidates:
        score = scores.get(row["canonical_pair_id"])
        if score is None:
            raise ValueError(f"missing checker score: {row['canonical_pair_id']}")
        if score["acceptability"] < config["tau_accept"]:
            exclusions["acceptability"] += 1
            continue
        if not passes_nli_gate(score, config, exclusions):
            continue
        passed.append(
            {
                **row,
                "clean_acceptability": score["acceptability"],
                "clean_entailment": score["entailment"],
                "clean_nli_probabilities": score.get("nli_probabilities"),
            }
        )

    passed_before_dedup = len(passed)
    source_supply = Counter(row["corpus"] for row in passed)
    by_original: dict[str, list[dict]] = defaultdict(list)
    for row in passed:
        by_original[row["canonical_original_id"]].append(row)
    deduplicated = []
    cross_source_dedup = 0
    for rows_for_original in by_original.values():
        rows_for_original.sort(
            key=lambda row: (
                source_supply[row["corpus"]],
                stable_key(config["seed"], row["canonical_pair_id"]),
            )
        )
        deduplicated.append(rows_for_original[0])
        cross_source_dedup += len(rows_for_original) - 1
    passed = deduplicated
    pools = {(axis, corpus): [] for axis in AXES for corpus in CORPORA}
    pass1_counts = {}
    for corpus in CORPORA:
        source_rows = [row for row in passed if row["corpus"] == corpus]
        allocated, counts = allocate_source(source_rows, config["seed"], config["split_quota"])
        for axis, rows in allocated.items():
            pools[(axis, corpus)] = rows
            pass1_counts[f"{axis}_{corpus}"] = counts[axis]

    report = dict(base_report)
    report["quality_gates"] = {
        "nli_model": config["nli_model"],
        "nli_revision": config["nli_revision"],
        "nli_entailment_threshold": config["nli_entailment_threshold"],
        "nli_gate": config.get("nli_gate", "entailment"),
        "nli_contradiction_threshold": config.get("nli_contradiction_threshold"),
        "acceptability_model": config["acceptability_model"],
        "acceptability_revision": config["acceptability_revision"],
        "tau_accept": config["tau_accept"],
        "delta": config["delta"],
        "calibration_report": "checker_calibration.json",
        "candidate_count": len(candidates),
        "passed_before_original_dedup": passed_before_dedup,
        "passed_count": len(passed),
        "cross_source_original_dedup": cross_source_dedup,
        "exclusions": dict(sorted(exclusions.items())),
    }
    report["cells"] = {}
    for (axis, corpus), rows in pools.items():
        alias_names = sorted(config["phase3a_prediction_files"])
        report["cells"][f"{axis}_{corpus}"] = {
            "records": len(rows),
            "unique_originals": len({row["canonical_original_id"] for row in rows}),
            "allocation_pass_1": pass1_counts[f"{axis}_{corpus}"],
            "allocation_pass_2": sum(row["allocation_pass"] == 2 for row in rows),
            "underpowered": pass1_counts[f"{axis}_{corpus}"] < config["split_quota"],
            "gemma_strategy_count": dict(
                sorted(Counter(str(row["gemma_strategy_count"]) for row in rows).items())
            ),
            "strict_single_strategy_candidate": dict(
                sorted(Counter(str(row["strict_single_strategy_candidate"]).lower() for row in rows).items())
            ),
            "phase3a_predicted_codes": {
                alias: {
                    "code_counts": dict(
                        sorted(
                            Counter(
                                code
                                for row in rows
                                for code in row["phase3a_predicted_codes"].get(alias, [])
                            ).items()
                        )
                    ),
                    "set_counts": dict(
                        sorted(
                            Counter(
                                "+".join(row["phase3a_predicted_codes"].get(alias, [])) or "<none>"
                                for row in rows
                            ).items()
                        )
                    ),
                }
                for alias in alias_names
            },
        }
    return pools, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--stage", choices=("prepare", "allocate"), required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.stage == "prepare":
        candidates, report = prepare_candidates(config)
        write_jsonl(output_dir / "structural_candidates.jsonl", candidates)
        (output_dir / "pool_report_pre_quality.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"structural_candidates": len(candidates)}, indent=2))
        return

    candidates = read_jsonl(output_dir / "structural_candidates.jsonl")
    scores = {
        row["canonical_pair_id"]: row
        for row in read_jsonl(Path(config["quality_scores_file"]))
    }
    base_report = json.loads((output_dir / "pool_report_pre_quality.json").read_text())
    pools, report = allocate_candidates(candidates, scores, config, base_report)
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
