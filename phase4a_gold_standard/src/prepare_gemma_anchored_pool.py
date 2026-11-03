#!/usr/bin/env python3
"""Build the isolated Phase 4a v2 pool from strict Gemma-anchored candidates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import prepare_annotation_pool as base


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = (
    PROJECT_ROOT
    / "phase4a_gold_standard"
    / "configs"
    / "annotation_pool_gemma_anchored_strict_v2.json"
)
POOL_TYPE = "primary_single_strategy_gemma_anchored_strict"
GEMMA_ALIAS = "gemma3_12b_pairwise_qlora"
SELECTION_RULE = "gemma_singleton_plus_exact_singleton_confirmation"


def make_review_task_id(
    canonical_pair_id: str, strategy_code: str, pool_type: str
) -> str:
    parts = canonical_pair_id.split(":", 2)
    language = parts[1] if len(parts) > 1 else "und"
    value = f"{pool_type}\0{canonical_pair_id}\0{strategy_code}"
    suffix = hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
    return f"review:{language}:{strategy_code.lower()}:{suffix}"


def strict_votes(candidate: Mapping[str, Any], strategy: str) -> dict[str, str]:
    predictions = candidate.get("model_predictions")
    if not isinstance(predictions, dict):
        raise ValueError(f"Missing model predictions for {base.canonical_pair_id(candidate)}")
    votes: dict[str, str] = {}
    for key in base.MODEL_KEYS:
        alias = base.MODEL_ALIASES[key]
        prediction = predictions.get(alias)
        codes = prediction.get("predicted_codes") if isinstance(prediction, dict) else None
        if not isinstance(codes, list):
            raise ValueError(f"Missing prediction {alias}")
        votes[key] = "yes" if codes == [strategy] else "no"
    return votes


def candidate_to_records(
    candidate: Mapping[str, Any], alignment: Mapping[str, Any], pool_type: str
) -> tuple[dict[str, Any], dict[str, Any], tuple[str, str, str]]:
    pair_id = base.canonical_pair_id(candidate)
    strategy = str(candidate.get("candidate_strategy_code") or "")
    if strategy not in base.STRATEGY_CODES:
        raise ValueError(f"Unknown candidate strategy for {pair_id}")
    if candidate.get("candidate_strategy_label") != base.STRATEGY_LABELS[strategy]:
        raise ValueError(f"Strategy code/label mismatch for {pair_id}")
    predictions = candidate.get("model_predictions")
    gemma = predictions.get(GEMMA_ALIAS) if isinstance(predictions, dict) else None
    if (
        candidate.get("selection_rule") != SELECTION_RULE
        or candidate.get("anchor_model") != GEMMA_ALIAS
        or not isinstance(gemma, dict)
        or gemma.get("predicted_codes") != [strategy]
    ):
        raise ValueError(f"Invalid Gemma anchor for {pair_id}/{strategy}")
    votes = strict_votes(candidate, strategy)
    confirming_aliases = [
        base.MODEL_ALIASES[key] for key in base.MODEL_KEYS if votes[key] == "yes"
    ]
    if candidate.get("confirming_models") != confirming_aliases:
        raise ValueError(f"Stored/recomputed strict confirmations differ for {pair_id}")
    support_count = 1 + len(confirming_aliases)
    if support_count < 2 or int(candidate.get("majority_votes", -1)) != support_count:
        raise ValueError(f"Stored/recomputed anchored support differs for {pair_id}")

    sources, corpora = base.source_and_corpus_values(candidate)
    if not sources:
        raise ValueError(f"No source provenance for {pair_id}")
    source_tokens, target_tokens, links = base.alignment_tokens(candidate, alignment)
    review_id = make_review_task_id(pair_id, strategy, pool_type)
    quality_tier = str(candidate.get("quality_tier") or "")
    csv_record: dict[str, Any] = {
        "review_task_id": review_id,
        "queue_rank": None,
        "canonical_pair_id": pair_id,
        "language": candidate["language"],
        "sources": base.flattened_values(sources),
        "corpora": base.flattened_values(corpora),
        "original": candidate["original"],
        "simplification": candidate["simple"],
        "candidate_strategy_code": strategy,
        "candidate_strategy_label": base.STRATEGY_LABELS[strategy],
        **{base.MODEL_VOTE_FIELDS[key]: votes[key] for key in base.MODEL_KEYS},
        "majority_votes": support_count,
        "quality_tier": quality_tier,
        "pool_type": pool_type,
    }
    payload = {
        "schema": base.PAYLOAD_SCHEMA,
        "task_id": review_id,
        "review_task_id": review_id,
        "canonical_pair_id": pair_id,
        "language": candidate["language"],
        "sources": sources,
        "source_text": candidate["original"],
        "target_text": candidate["simple"],
        "candidate_strategy": strategy,
        "source_tokens": source_tokens,
        "target_tokens": target_tokens,
        "simalign_links": links,
        "public_metadata": {
            "candidate_strategy_label": base.STRATEGY_LABELS[strategy],
            "corpora": corpora,
            "majority_votes": support_count,
            "quality_tier": quality_tier,
            "pool_type": pool_type,
            "alignment_schema": alignment["schema"],
            "alignment_status": alignment.get("status"),
            "alignment_tokenizer_id": alignment.get("tokenizer_id"),
            "phase3a_candidate_schema": candidate.get("candidate_schema"),
        },
        "model_votes": {"gemma": "yes", **votes},
        "queue_rank": None,
    }
    return csv_record, payload, (strategy, quality_tier, sources[0])


def write_language(
    temporary: Path,
    item: Mapping[str, Any],
    seed: str,
    spreadsheet_safe: bool,
) -> dict[str, Any]:
    language = str(item["language"])
    candidate_path = Path(item["candidate_path"])
    alignment_path = Path(item["alignment_path"])
    data_dir = temporary / "data" / language
    payload_dir = temporary / "payloads" / language
    data_dir.mkdir(parents=True)
    payload_dir.mkdir(parents=True)
    spool = temporary / f".{language}.unranked.jsonl"
    descriptors: list[tuple[str, tuple[str, str, str]]] = []
    with spool.open("w", encoding="utf-8", newline="\n") as handle:
        for candidate, alignment in base.stream_join_candidates(
            candidate_path, alignment_path, language
        ):
            csv_record, payload, stratum = candidate_to_records(
                candidate, alignment, POOL_TYPE
            )
            descriptors.append((csv_record["review_task_id"], stratum))
            base.write_jsonl_record(handle, {"csv": csv_record, "payload": payload})
    expected = item.get("expected_tasks")
    if expected is not None and len(descriptors) != int(expected):
        raise ValueError(f"{language}: observed {len(descriptors)}, expected {expected}")
    ranks = base.stratified_queue_ranks(descriptors, f"{seed}\0{language}")
    csv_path = data_dir / base.CSV_FILENAME
    safe_path = data_dir / base.SAFE_CSV_FILENAME
    payload_path = payload_dir / base.PAYLOAD_FILENAME
    counts: Counter[str] = Counter()
    safe_handle = (
        safe_path.open("w", encoding="utf-8", newline="")
        if spreadsheet_safe
        else None
    )
    try:
        with (
            csv_path.open("w", encoding="utf-8", newline="") as csv_handle,
            payload_path.open("w", encoding="utf-8", newline="\n") as payload_handle,
        ):
            writer = base.write_csv_header(csv_handle)
            safe_writer = base.write_csv_header(safe_handle) if safe_handle else None
            for value in base.read_jsonl(spool):
                csv_record = value["csv"]
                payload = value["payload"]
                rank = ranks[str(csv_record["review_task_id"])]
                csv_record["queue_rank"] = rank
                payload["queue_rank"] = rank
                payload = base.with_payload_hash(payload)
                writer.writerow(csv_record)
                if safe_writer:
                    safe_writer.writerow(base._spreadsheet_safe_record(csv_record))
                base.write_jsonl_record(payload_handle, payload)
                counts[f"strategy:{payload['candidate_strategy']}"] += 1
                counts[f"quality:{payload['public_metadata']['quality_tier']}"] += 1
    finally:
        if safe_handle:
            safe_handle.close()
    spool.unlink()
    return {
        "language": language,
        "candidate_file": str(candidate_path),
        "candidate_sha256": base.sha256(candidate_path),
        "alignment_file": str(alignment_path),
        "alignment_sha256": base.sha256(alignment_path),
        "tasks": len(descriptors),
        "csv_file": csv_path.relative_to(temporary).as_posix(),
        "csv_bytes": csv_path.stat().st_size,
        "csv_sha256": base.sha256(csv_path),
        "payload_file": payload_path.relative_to(temporary).as_posix(),
        "payload_bytes": payload_path.stat().st_size,
        "payload_sha256": base.sha256(payload_path),
        "spreadsheet_safe_file": safe_path.relative_to(temporary).as_posix(),
        "spreadsheet_safe_bytes": safe_path.stat().st_size,
        "spreadsheet_safe_sha256": base.sha256(safe_path),
        "counts": dict(sorted(counts.items())),
    }


def build(config_path: Path, overwrite: bool = False) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = base.load_json(config_path)
    if config.get("schema") != base.POOL_CONFIG_SCHEMA or config.get("pool_type") != POOL_TYPE:
        raise ValueError("Unexpected Gemma-anchored Phase 4a config")
    inputs = base.resolve_inputs(config)
    if len(inputs) != 12:
        raise ValueError("The v2 pool requires exactly 12 languages")
    output_base = base.project_path(config["output_root"])
    output_base.mkdir(parents=True, exist_ok=True)
    pool_root = output_base / str(config["pool_id"])
    if pool_root.exists() and not overwrite:
        raise FileExistsError(f"Pool exists: {pool_root}")
    temporary = Path(tempfile.mkdtemp(prefix=f".{config['pool_id']}-", dir=output_base))
    try:
        rows = [
            write_language(
                temporary,
                item,
                str(config["queue_seed"]),
                bool(config.get("spreadsheet_safe_export", True)),
            )
            for item in inputs
        ]
        total = sum(int(row["tasks"]) for row in rows)
        if total != int(config["expected_total"]):
            raise ValueError(f"Observed {total} tasks, expected {config['expected_total']}")
        stored_config = dict(config)
        stored_config["source_config"] = str(config_path)
        (temporary / "pool_config.json").write_text(
            json.dumps(stored_config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest = {
            "schema": base.POOL_MANIFEST_SCHEMA,
            "pool_id": config["pool_id"],
            "pool_type": POOL_TYPE,
            "tasks": total,
            "languages": [row["language"] for row in rows],
            "files": rows,
        }
        (temporary / base.MANIFEST_JSON_FILENAME).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        base._write_manifest_csv(temporary / base.MANIFEST_CSV_FILENAME, rows)
        validation = base.validate_pool(temporary, total)
        summary = {
            "schema": "feats-phase4a-gemma-anchored-pool-summary-v1",
            "pool_id": config["pool_id"],
            "pool_type": POOL_TYPE,
            "tasks": total,
            "languages": {row["language"]: int(row["tasks"]) for row in rows},
            "validation": validation,
        }
        reports = temporary / "reports"
        (reports / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if pool_root.exists():
            shutil.rmtree(pool_root)
        temporary.replace(pool_root)
        summary["output_root"] = str(pool_root)
        return summary
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--validate-only", type=Path)
    args = parser.parse_args()
    result = (
        base.validate_pool(args.validate_only)
        if args.validate_only is not None
        else build(args.config, args.overwrite)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
