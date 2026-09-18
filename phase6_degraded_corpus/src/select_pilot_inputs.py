#!/usr/bin/env python3
"""Select deterministic clean candidates and backups for the Phase 6 pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict, deque
from pathlib import Path

from contracts import SCHEMA, read_jsonl, stable_key, validate_candidate, write_jsonl

TOKEN_RE = re.compile(r"\w+(?:[-’']\w+)*|[^\w\s]", re.UNICODE)
BAD_PREFIXES = ("File:", "Category:", "Template:", "Image:")


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def normal(text: str) -> str:
    return " ".join(text.lower().split())


def length_bin(count: int, bins: dict[str, list[int]]) -> str | None:
    for name, (lower, upper) in bins.items():
        if lower <= count <= upper:
            return name
    return None


def corpus_name(row: dict) -> str | None:
    corpora = row.get("corpora") or []
    return corpora[0].get("corpus") if len(corpora) == 1 else None


def source_name(row: dict) -> str | None:
    corpora = row.get("corpora") or []
    return corpora[0].get("source") if len(corpora) == 1 else None


def load_strategies(path: Path) -> dict[str, str]:
    result = {}
    for row in read_jsonl(path):
        codes = row.get("predicted_codes") or []
        result[row["canonical_pair_id"]] = {
            "codes": codes,
            "count": len(codes),
            "strategy": codes[0] if len(codes) == 1 else "OTHER",
        }
    return result


def round_robin(rows: list[dict], count: int, seed: int) -> list[dict]:
    groups: dict[tuple[str, str], deque] = defaultdict(deque)
    for row in sorted(rows, key=lambda x: stable_key(seed, x["canonical_pair_id"])):
        groups[(row["corpus"], row["predicted_strategy"])].append(row)
    keys = sorted(groups, key=lambda x: stable_key(seed, "|".join(x)))
    selected = []
    while len(selected) < count and keys:
        next_keys = []
        for key in keys:
            if groups[key] and len(selected) < count:
                selected.append(groups[key].popleft())
            if groups[key]:
                next_keys.append(key)
        keys = next_keys
    return selected


def build(config: dict) -> tuple[list[dict], list[dict], dict]:
    seed = int(config["seed"])
    bins = config["length_bins"]
    allowed = set(config["allowed_corpora"])
    excluded = set(config["excluded_corpora"])
    strategies = load_strategies(Path(config["strategy_predictions_file"]))
    judgments = {r["canonical_pair_id"]: r for r in read_jsonl(Path(config["human_judgments_file"]))}
    positives = {k for k, r in judgments.items() if r.get("human_label") == "positive"}
    reserved = set()
    if config.get("reserved_original_ids_file"):
        reserved = {line.strip() for line in Path(config["reserved_original_ids_file"]).open() if line.strip()}

    anchors, candidates = [], []
    exclusions = Counter()
    target_rows = read_jsonl(Path(config["phase2b_file"]))
    target_ids = {row["canonical_pair_id"] for row in target_rows}
    anchor_path = Path(config.get("anchor_phase2b_file", config["phase2b_file"]))
    anchor_rows = [
        row for row in read_jsonl(anchor_path)
        if row["canonical_pair_id"] in positives
    ]
    input_rows = [(row, True) for row in anchor_rows] + [(row, False) for row in target_rows]
    for row, is_anchor_source in input_rows:
        if row.get("language") != config["language"]:
            continue
        pair_id = row["canonical_pair_id"]
        if is_anchor_source and pair_id not in positives:
            continue
        if not is_anchor_source and pair_id in positives:
            continue
        original_id = row["canonical_original_id"]
        corpus = corpus_name(row)
        source = source_name(row)
        if original_id in reserved:
            exclusions["reserved_original"] += 1
            continue
        if corpus in excluded or corpus not in allowed:
            exclusions["corpus"] += 1
            continue
        original, simple = row["original"].strip(), row["simple"].strip()
        if normal(original) == normal(simple):
            exclusions["identical"] += 1
            continue
        if any(original.startswith(x) or simple.startswith(x) for x in BAD_PREFIXES):
            exclusions["markup"] += 1
            continue
        strategy_info = strategies.get(
            pair_id, {"codes": [], "count": 0, "strategy": "UNKNOWN"}
        )
        if config.get("require_single_strategy", False) and strategy_info["count"] != 1:
            exclusions["not_single_strategy"] += 1
            continue
        bucket = length_bin(len(tokens(original)), bins)
        if bucket is None:
            exclusions["length"] += 1
            continue
        item = {
            "schema": SCHEMA,
            "selection_tier": "reviewed_anchor" if is_anchor_source else "candidate",
            "canonical_pair_id": pair_id,
            "canonical_original_id": original_id,
            "language": row["language"],
            "original": original,
            "clean_simplification": simple,
            "source": source,
            "corpus": corpus,
            "length_bin": bucket,
            "predicted_strategy": strategy_info["strategy"],
            "predicted_strategy_count": strategy_info["count"],
            "predicted_strategy_codes": strategy_info["codes"],
            "clean_review_status": "pending",
            "clean_source_tier": "phase4a_reviewed" if is_anchor_source else "target_simple_candidate",
            "target_simple_pass": pair_id in target_ids,
            "phase2a_run_id": config.get("phase2a_run_id", "test"),
            "phase2b_variant_id": config.get("phase2b_variant_id", "test"),
        }
        (anchors if is_anchor_source else candidates).append(item)

    anchors.sort(key=lambda x: stable_key(seed, x["canonical_pair_id"]))
    used_originals = {x["canonical_original_id"] for x in anchors}
    candidates = [x for x in candidates if x["canonical_original_id"] not in used_originals]

    targets = config["primary_length_targets"]
    primary = list(anchors)
    for bucket, target in targets.items():
        existing = sum(x["length_bin"] == bucket for x in primary)
        pool = [x for x in candidates if x["length_bin"] == bucket and x["canonical_original_id"] not in used_originals]
        chosen = round_robin(pool, max(0, target - existing), seed)
        for item in chosen:
            used_originals.add(item["canonical_original_id"])
        primary.extend(chosen)
    if len(primary) != config["primary_size"]:
        raise ValueError(f"selected {len(primary)} primary rows, expected {config['primary_size']}")

    backup_pool = [x for x in candidates if x["canonical_original_id"] not in used_originals]
    backup = round_robin(backup_pool, config["backup_size"], seed + 1)
    for item in backup:
        item["selection_tier"] = "backup"
    if len(backup) != config["backup_size"]:
        raise ValueError(f"selected {len(backup)} backups, expected {config['backup_size']}")

    for row in primary + backup:
        validate_candidate(row)
    report = {
        "schema": "feats-phase6-selection-report-v1",
        "experiment_id": config["experiment_id"],
        "seed": seed,
        "primary": len(primary),
        "backups": len(backup),
        "reviewed_anchors": sum(x["selection_tier"] == "reviewed_anchor" for x in primary),
        "pending_clean_review": sum(x["clean_review_status"] == "pending" for x in primary),
        "primary_by_clean_source_tier": dict(Counter(x["clean_source_tier"] for x in primary)),
        "primary_target_simple_pass": sum(bool(x["target_simple_pass"]) for x in primary),
        "anchors_target_simple_pass": sum(
            bool(x["target_simple_pass"]) for x in primary
            if x["selection_tier"] == "reviewed_anchor"
        ),
        "primary_by_corpus": dict(Counter(x["corpus"] for x in primary)),
        "primary_by_length": dict(Counter(x["length_bin"] for x in primary)),
        "primary_by_strategy": dict(Counter(x["predicted_strategy"] for x in primary)),
        "exclusions": dict(exclusions),
        "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
    }
    return primary, backup, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    primary, backup, report = build(config)
    output = Path(config["output_dir"])
    write_jsonl(output / "sampled_primary_50.jsonl", primary)
    write_jsonl(output / f"sampled_backup_{len(backup)}.jsonl", backup)
    review_rows = [{
        "canonical_pair_id": row["canonical_pair_id"],
        "reviewer": "",
        "meaning_preserved": None,
        "no_unsupported_content": None,
        "fluent": None,
        "meaningfully_simpler": None,
        "clean_text": None,
        "decision": "pending",
        "notes": "",
    } for row in primary]
    write_jsonl(output / "clean_review_decisions.template.jsonl", review_rows)
    (output / "selection_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
