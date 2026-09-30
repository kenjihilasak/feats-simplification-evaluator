#!/usr/bin/env python3
"""Materialize selected MMI full-run pairs, optionally withholding hedged ILLOC rows."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, write_jsonl


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_for(original_id: str, seed: int, validation_fraction: float) -> str:
    value = int(hashlib.sha256(f"{seed}:{original_id}".encode()).hexdigest(), 16) / 2**256
    return "validation" if value < validation_fraction else "train"


def materialize(
    plan_rows: list[dict], scored_rows: list[dict], excluded_originals: set[str], seed: int,
    validation_fraction: float = 0.1, include_hedged: bool = False,
) -> tuple[list[dict], list[dict], dict]:
    plan = {}
    for row in plan_rows:
        pair_id = row["canonical_pair_id"]
        if pair_id in plan:
            raise ValueError(f"duplicate plan pair: {pair_id}")
        plan[pair_id] = row
    scored = {}
    for row in scored_rows:
        pair_id = row["canonical_pair_id"]
        if pair_id in scored:
            raise ValueError(f"duplicate scored pair: {pair_id}")
        scored[pair_id] = row
    unknown = set(scored) - set(plan)
    if unknown:
        raise ValueError(f"scored pairs absent from plan: {sorted(unknown)[:3]}")

    instances, withheld = [], []
    drops = Counter()
    selected_counts = Counter()
    original_splits = {}
    for pair_id, planned in sorted(plan.items()):
        if planned.get("usage") == "reserved_evaluation":
            raise ValueError(f"reserved evaluation row reached materializer: {pair_id}")
        original_id = planned["canonical_original_id"]
        if original_id in excluded_originals:
            # Text-matched audited originals (see expand_audited_exclusions.py) are dropped, not fatal.
            drops["excluded_audited_original"] += 1
            continue
        if planned.get("plan_status") != "ready":
            drops[f"plan:{planned.get('plan_status')}"] += 1
            continue
        result = scored.get(pair_id)
        if result is None:
            raise ValueError(f"missing scored row: {pair_id}")
        selected_index = result.get("selected_index")
        if selected_index is None:
            first = result.get("candidates", [{}])[0]
            failed = [name for name, passed in (first.get("checks") or {}).items() if not passed]
            drops["checks:" + ("+".join(failed) if failed else "no_valid_candidate")] += 1
            continue
        candidate = result["candidates"][selected_index]
        if not candidate.get("valid") or not candidate.get("degraded"):
            raise ValueError(f"invalid selected candidate: {pair_id}")
        if planned.get("operation") == "assertion_to_hedged" and not include_hedged:
            withheld.append({
                "canonical_pair_id": pair_id,
                "canonical_original_id": original_id,
                "reason": "pending_hedged_human_gate",
                "selected_index": selected_index,
            })
            drops["withheld:pending_hedged_human_gate"] += 1
            continue
        split = split_for(original_id, seed, validation_fraction)
        if original_splits.setdefault(original_id, split) != split:
            raise AssertionError("canonical_original_id crossed splits")
        common = {
            "schema": "feats-phase6-mmi-training-instance-v2",
            "canonical_pair_id": pair_id,
            "canonical_original_id": original_id,
            "language": planned.get("language", "en"),
            "original": planned["original"],
            "axis": planned["target_axis"],
            "target_axis": planned["target_axis"],
            "operation": planned["operation"],
            "source": planned.get("source"),
            "corpus": planned["corpus"],
            "split": split,
            "gemma_strategy_count": planned.get("gemma_strategy_count"),
            "phase3a_predicted_codes": planned.get("phase3a_predicted_codes", {}),
            "strict_single_strategy_candidate": planned.get("strict_single_strategy_candidate", False),
            "generation": {
                "config_id": result.get("config_id"),
                "model": result.get("model"),
                "model_revision": result.get("model_revision"),
                "prompt_id": result.get("prompt_id"),
                "prompt_sha256": result.get("prompt_sha256"),
                "decoding": result.get("decoding"),
                "versions": result.get("versions"),
                "selected_index": selected_index,
                "checks": candidate.get("checks"),
            },
        }
        instances.append({**common, "variant": "simplified", "text": planned["clean_simplification"], "score": 1})
        instances.append({**common, "variant": "degraded", "text": candidate["degraded"], "score": 0})
        selected_counts[(planned["target_axis"], planned["corpus"], planned["operation"], split)] += 1

    instances.sort(key=lambda row: (row["canonical_pair_id"], row["variant"]))
    withheld.sort(key=lambda row: row["canonical_pair_id"])
    pair_count = len(instances) // 2
    if len(instances) != 2 * len({row["canonical_pair_id"] for row in instances}):
        raise AssertionError("each selected pair must create exactly two instances")
    report = {
        "schema": "feats-phase6-mmi-full-corpus-report-v1",
        "hedged_policy": "included_after_human_gate" if include_hedged else "withheld_pending_human_gate",
        "plan_pairs": len(plan), "scored_pairs": len(scored), "selected_pairs": pair_count,
        "training_instances": len(instances), "withheld_hedged_pairs": len(withheld),
        "instances_by_split": dict(sorted(Counter(row["split"] for row in instances).items())),
        "instances_by_axis": dict(sorted(Counter(row["axis"] for row in instances).items())),
        "selected_pairs_by_axis_source_operation_split": {
            "|".join(key): value for key, value in sorted(selected_counts.items())
        },
        "drop_reasons": dict(sorted(drops.items())),
    }
    return instances, withheld, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--scored-dir", type=Path, required=True)
    parser.add_argument("--excluded-originals", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260930)
    parser.add_argument("--validation-fraction", type=float, default=0.1)
    parser.add_argument("--include-hedged", action="store_true")
    args = parser.parse_args()
    if not 0 < args.validation_fraction < 1:
        raise ValueError("validation fraction must be between zero and one")
    scored_paths = sorted(args.scored_dir.glob("*.jsonl"))
    scored = [row for path in scored_paths for row in read_jsonl(path)]
    excluded = {line.strip() for line in args.excluded_originals.read_text().splitlines() if line.strip()}
    instances, withheld, report = materialize(
        read_jsonl(args.plan), scored, excluded, args.seed, args.validation_fraction, args.include_hedged
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "train.jsonl", [row for row in instances if row["split"] == "train"])
    write_jsonl(args.output_dir / "validation.jsonl", [row for row in instances if row["split"] == "validation"])
    write_jsonl(args.output_dir / "withheld_hedged.jsonl", withheld)
    report["input_sha256"] = {
        "plan": sha256(args.plan), "excluded_originals": sha256(args.excluded_originals),
        "scored_shards": {str(path): sha256(path) for path in scored_paths},
    }
    for filename in ("train.jsonl", "validation.jsonl", "withheld_hedged.jsonl"):
        report.setdefault("output_sha256", {})[filename] = sha256(args.output_dir / filename)
    (args.output_dir / "corpus_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: report[k] for k in (
        "hedged_policy", "selected_pairs", "training_instances", "withheld_hedged_pairs",
        "instances_by_split", "instances_by_axis", "drop_reasons",
    )}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
