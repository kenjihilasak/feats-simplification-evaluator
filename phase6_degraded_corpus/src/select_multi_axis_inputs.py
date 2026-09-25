#!/usr/bin/env python3
"""Build the deterministic Phase 6 English multi-axis candidate inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from contracts import read_jsonl, write_jsonl

TOKEN = re.compile(r"\w+(?:[-’']\w+)*|[^\w\s]", re.UNICODE)
BAD_PREFIXES = ("File:", "Category:", "Template:", "Image:")
VALID_STRATEGIES = {"OMIT", "SYN", "MOD", "EXPL", "COMP", "SYNT"}


def normal(text: str) -> str:
    return " ".join(text.lower().split())


def _single_corpus(row: dict) -> tuple[str | None, str | None]:
    corpora = row.get("corpora") or []
    if len(corpora) != 1:
        return None, None
    return corpora[0].get("source"), corpora[0].get("corpus")


def build_inventory(config: dict) -> tuple[list[dict], dict]:
    strict = {}
    for row in read_jsonl(Path(config["single_strategy_file"])):
        pair_id = row["canonical_pair_id"]
        if pair_id in strict:
            raise ValueError(f"duplicate strategy candidate: {pair_id}")
        strategy = row.get("candidate_strategy_code")
        if strategy in VALID_STRATEGIES:
            strict[pair_id] = row

    reserved = set()
    for filename in config.get("reserved_original_ids_files", []):
        path = Path(filename)
        if not path.exists():
            raise FileNotFoundError(f"reserved-original file not found: {path}")
        reserved.update(line.strip() for line in path.open(encoding="utf-8") if line.strip())

    allowed = set(config["allowed_corpora"])
    excluded = set(config["excluded_corpora"])
    lower, upper = config["original_token_range"]
    exclusions: Counter = Counter()
    output = []
    seen = set()
    for row in read_jsonl(Path(config["phase2b_file"])):
        pair_id = row["canonical_pair_id"]
        if pair_id in seen:
            raise ValueError(f"duplicate canonical_pair_id in Phase 2b: {pair_id}")
        seen.add(pair_id)
        if row.get("language") != config["language"]:
            exclusions["language"] += 1
            continue
        strategy_row = strict.get(pair_id)
        if not strategy_row:
            exclusions["not_strict_single_strategy"] += 1
            continue
        original_id = row["canonical_original_id"]
        if original_id in reserved:
            exclusions["reserved_evaluation_original"] += 1
            continue
        source, corpus = _single_corpus(row)
        if corpus in excluded or corpus not in allowed:
            exclusions["corpus"] += 1
            continue
        original = row["original"].strip()
        simple = row["simple"].strip()
        if not original or not simple:
            exclusions["empty"] += 1
            continue
        if normal(original) == normal(simple):
            exclusions["identical"] += 1
            continue
        if any(original.startswith(prefix) or simple.startswith(prefix) for prefix in BAD_PREFIXES):
            exclusions["markup"] += 1
            continue
        length = len(TOKEN.findall(original))
        if not lower <= length <= upper:
            exclusions["length"] += 1
            continue
        output.append(
            {
                "schema": "feats-phase6-clean-candidate-v2",
                "canonical_pair_id": pair_id,
                "canonical_original_id": original_id,
                "language": "en",
                "original": original,
                "clean_simplification": simple,
                "source": source,
                "corpus": corpus,
                "source_strategy": strategy_row["candidate_strategy_code"],
                "source_strategy_quality_tier": strategy_row.get("quality_tier"),
                "source_strategy_confirmation_count": strategy_row.get("confirmation_count"),
                "clean_source_tier": "target_simple_strict_single_strategy_weak_supervision",
                "clean_review_status": "weak_supervision_candidate",
                "phase2b_variant_id": config["phase2b_variant_id"],
                "phase3a_candidate_set_id": config["phase3a_candidate_set_id"],
            }
        )
    output.sort(key=lambda row: row["canonical_pair_id"])
    report = {
        "schema": "feats-phase6-inventory-report-v2",
        "experiment_id": config["experiment_id"],
        "records": len(output),
        "unique_pair_ids": len({row["canonical_pair_id"] for row in output}),
        "unique_original_ids": len({row["canonical_original_id"] for row in output}),
        "by_strategy": dict(sorted(Counter(row["source_strategy"] for row in output).items())),
        "by_corpus": dict(sorted(Counter(row["corpus"] for row in output).items())),
        "exclusions": dict(sorted(exclusions.items())),
        "input_sha256": hashlib.sha256(Path(config["phase2b_file"]).read_bytes()).hexdigest(),
        "strategy_input_sha256": hashlib.sha256(Path(config["single_strategy_file"]).read_bytes()).hexdigest(),
        "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
    }
    return output, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    rows, report = build_inventory(config)
    output = Path(config["output_dir"])
    write_jsonl(output / "candidate_inventory.jsonl", rows)
    output.mkdir(parents=True, exist_ok=True)
    (output / "inventory_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

