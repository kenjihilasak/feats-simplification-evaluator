#!/usr/bin/env python3
"""Prepare the complete Phase 4a annotation pool with a streaming merge join."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import tempfile
from collections import Counter, defaultdict
from itertools import zip_longest
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

try:
    from .data_contracts import (
        CSV_FIELDS,
        MODEL_ALIASES,
        MODEL_KEYS,
        PAYLOAD_SCHEMA,
        POOL_CONFIG_SCHEMA,
        POOL_MANIFEST_SCHEMA,
        POOL_VALIDATION_SCHEMA,
        PRIMARY_POOL_TYPE,
        STRATEGY_CODES,
        STRATEGY_LABELS,
        canonical_json,
        flattened_values,
        load_json,
        make_review_task_id,
        payload_hash,
        project_path,
        read_jsonl,
        sha256,
        source_and_corpus_values,
        spreadsheet_safe_cell,
        text_sha256,
        with_payload_hash,
        write_jsonl_record,
    )
except ImportError:
    from data_contracts import (
        CSV_FIELDS,
        MODEL_ALIASES,
        MODEL_KEYS,
        PAYLOAD_SCHEMA,
        POOL_CONFIG_SCHEMA,
        POOL_MANIFEST_SCHEMA,
        POOL_VALIDATION_SCHEMA,
        PRIMARY_POOL_TYPE,
        STRATEGY_CODES,
        STRATEGY_LABELS,
        canonical_json,
        flattened_values,
        load_json,
        make_review_task_id,
        payload_hash,
        project_path,
        read_jsonl,
        sha256,
        source_and_corpus_values,
        spreadsheet_safe_cell,
        text_sha256,
        with_payload_hash,
        write_jsonl_record,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = (
    PROJECT_ROOT / "phase4a_gold_standard" / "configs" / "annotation_pool_full_v1.json"
)
CANDIDATE_FILENAME = "single_strategy_candidates.jsonl"
ALIGNMENT_FILENAME = "feats_word_alignments.jsonl"
CSV_FILENAME = "annotation_pool.csv"
SAFE_CSV_FILENAME = "annotation_pool.spreadsheet_safe.csv"
PAYLOAD_FILENAME = "annotation_tasks.jsonl"
MANIFEST_CSV_FILENAME = "POOL_MANIFEST.csv"
MANIFEST_JSON_FILENAME = "pool_manifest.json"
MODEL_VOTE_FIELDS = {
    "e5": "e5_supports_strategy",
    "qwen": "qwen_supports_strategy",
    "xlmr": "xlmr_supports_strategy",
}
QUEUE_STRATA = ("candidate_strategy_code", "quality_tier", "primary_source")


def canonical_pair_id(record: Mapping[str, Any]) -> str:
    return str(record.get("canonical_pair_id") or record.get("id") or "")


def _next_or_none(iterator: Iterator[dict[str, Any]]) -> dict[str, Any] | None:
    try:
        return next(iterator)
    except StopIteration:
        return None


def stream_join_candidates(
    candidate_path: Path, alignment_path: Path, language: str
) -> Iterator[tuple[dict[str, Any], dict[str, Any]]]:
    """Merge a sorted candidate subset with the sorted full Phase 3b stream."""

    alignments = iter(read_jsonl(alignment_path))
    alignment = _next_or_none(alignments)
    previous_candidate = ""
    previous_alignment = ""
    for candidate in read_jsonl(candidate_path):
        pair_id = canonical_pair_id(candidate)
        if not pair_id:
            raise ValueError(f"Missing candidate ID in {candidate_path}")
        if pair_id <= previous_candidate:
            raise ValueError(f"Candidate IDs are not strictly sorted at {pair_id}")
        previous_candidate = pair_id
        if candidate.get("language") != language:
            raise ValueError(f"Candidate language/path mismatch for {pair_id}")

        while alignment is not None:
            alignment_id = canonical_pair_id(alignment)
            if not alignment_id:
                raise ValueError(f"Missing alignment ID in {alignment_path}")
            if alignment_id <= previous_alignment:
                raise ValueError(
                    f"Alignment IDs are not strictly sorted at {alignment_id}"
                )
            if alignment_id >= pair_id:
                break
            previous_alignment = alignment_id
            alignment = _next_or_none(alignments)

        if alignment is None or canonical_pair_id(alignment) != pair_id:
            found = None if alignment is None else canonical_pair_id(alignment)
            raise ValueError(
                f"Candidate {pair_id} has no Phase 3b match; next alignment={found!r}"
            )
        if alignment.get("language") != language:
            raise ValueError(f"Alignment language/path mismatch for {pair_id}")
        yield candidate, alignment
        previous_alignment = pair_id
        alignment = _next_or_none(alignments)


def model_votes(candidate: Mapping[str, Any], strategy: str) -> dict[str, str]:
    predictions = candidate.get("model_predictions")
    if not isinstance(predictions, dict):
        raise ValueError(f"Missing model predictions for {canonical_pair_id(candidate)}")
    votes: dict[str, str] = {}
    for key in MODEL_KEYS:
        alias = MODEL_ALIASES[key]
        prediction = predictions.get(alias)
        if not isinstance(prediction, dict):
            raise ValueError(f"Missing prediction {alias} for {canonical_pair_id(candidate)}")
        codes = prediction.get("predicted_codes")
        if not isinstance(codes, list) or any(code not in STRATEGY_CODES for code in codes):
            raise ValueError(f"Invalid predicted codes for {alias}")
        votes[key] = "yes" if strategy in codes else "no"
    return votes


def _base_tokens(
    text: str,
    token_values: Any,
    offset_values: Any,
    parent_values: Any,
    *,
    pair_id: str,
    side: str,
) -> list[dict[str, Any]]:
    if not all(isinstance(value, list) for value in (token_values, offset_values, parent_values)):
        raise ValueError(f"Invalid {side} token arrays for {pair_id}")
    if not (len(token_values) == len(offset_values) == len(parent_values)):
        raise ValueError(f"Non-1:1 {side} token arrays for {pair_id}")
    result = []
    for index, (token, offset, parent) in enumerate(
        zip(token_values, offset_values, parent_values)
    ):
        if (
            not isinstance(token, str)
            or not isinstance(offset, list)
            or len(offset) != 2
        ):
            raise ValueError(f"Invalid {side} token {index} for {pair_id}")
        start, end = int(offset[0]), int(offset[1])
        if start < 0 or end < start or end > len(text) or text[start:end] != token:
            raise ValueError(f"Inexact {side} token offset {index} for {pair_id}")
        parent_index = int(parent)
        if parent_index < 0:
            raise ValueError(f"Negative {side} orthographic parent for {pair_id}")
        result.append(
            {
                "index": index,
                "text": token,
                "start": start,
                "end": end,
                "orthographic_parent_index": parent_index,
                "sentence_id": None,
                "sentence_token_index": None,
                "lemma": None,
                "upos": None,
                "xpos": None,
                "feats": {},
                "head_index": None,
                "deprel": None,
                "parse_status": "not_parsed",
            }
        )
    return result


def alignment_tokens(
    candidate: Mapping[str, Any], alignment: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, int]]]:
    pair_id = canonical_pair_id(candidate)
    source_text = candidate.get("original")
    target_text = candidate.get("simple")
    if not isinstance(source_text, str) or not isinstance(target_text, str):
        raise ValueError(f"Missing exact source texts for {pair_id}")
    if alignment.get("schema") != "feats-phase3b-word-alignment-v2":
        raise ValueError(f"Unexpected alignment schema for {pair_id}")
    if alignment.get("original_text_sha256") != text_sha256(source_text):
        raise ValueError(f"Original text hash mismatch for {pair_id}")
    if alignment.get("simple_text_sha256") != text_sha256(target_text):
        raise ValueError(f"Simplification text hash mismatch for {pair_id}")

    source_tokens = _base_tokens(
        source_text,
        alignment.get("original_tokens"),
        alignment.get("original_token_offsets"),
        alignment.get("original_token_parent_indices"),
        pair_id=pair_id,
        side="source",
    )
    target_tokens = _base_tokens(
        target_text,
        alignment.get("simple_tokens"),
        alignment.get("simple_token_offsets"),
        alignment.get("simple_token_parent_indices"),
        pair_id=pair_id,
        side="target",
    )
    raw_links = alignment.get("alignment")
    if not isinstance(raw_links, list):
        raise ValueError(f"Invalid alignment links for {pair_id}")
    seen: set[tuple[int, int]] = set()
    links: list[dict[str, int]] = []
    for raw in raw_links:
        if not isinstance(raw, list) or len(raw) != 2:
            raise ValueError(f"Invalid alignment link for {pair_id}")
        source_index, target_index = int(raw[0]), int(raw[1])
        key = (source_index, target_index)
        if (
            source_index < 0
            or source_index >= len(source_tokens)
            or target_index < 0
            or target_index >= len(target_tokens)
            or key in seen
        ):
            raise ValueError(f"Out-of-range or duplicate alignment link for {pair_id}")
        seen.add(key)
        links.append({"source_index": source_index, "target_index": target_index})
    links.sort(key=lambda item: (item["source_index"], item["target_index"]))
    return source_tokens, target_tokens, links


def candidate_to_records(
    candidate: Mapping[str, Any],
    alignment: Mapping[str, Any],
    *,
    pool_type: str = PRIMARY_POOL_TYPE,
) -> tuple[dict[str, Any], dict[str, Any], tuple[str, str, str]]:
    pair_id = canonical_pair_id(candidate)
    strategy = str(candidate.get("candidate_strategy_code") or "")
    if strategy not in STRATEGY_CODES:
        raise ValueError(f"Unknown candidate strategy for {pair_id}")
    if candidate.get("candidate_strategy_label") != STRATEGY_LABELS[strategy]:
        raise ValueError(f"Strategy code/label mismatch for {pair_id}")
    votes = model_votes(candidate, strategy)
    majority = sum(value == "yes" for value in votes.values())
    if majority < 2 or int(candidate.get("majority_votes", -1)) != majority:
        raise ValueError(f"Stored/recomputed majority differs for {pair_id}/{strategy}")
    sources, corpora = source_and_corpus_values(candidate)
    if not sources:
        raise ValueError(f"No source provenance for {pair_id}")
    source_tokens, target_tokens, links = alignment_tokens(candidate, alignment)
    review_id = str(
        candidate.get("review_task_id")
        or make_review_task_id(pair_id, strategy, pool_type)
    )
    quality_tier = str(candidate.get("quality_tier") or "")
    csv_record: dict[str, Any] = {
        "review_task_id": review_id,
        "queue_rank": None,
        "canonical_pair_id": pair_id,
        "language": candidate["language"],
        "sources": flattened_values(sources),
        "corpora": flattened_values(corpora),
        "original": candidate["original"],
        "simplification": candidate["simple"],
        "candidate_strategy_code": strategy,
        "candidate_strategy_label": STRATEGY_LABELS[strategy],
        **{
            MODEL_VOTE_FIELDS[key]: votes[key]
            for key in MODEL_KEYS
        },
        "majority_votes": majority,
        "quality_tier": quality_tier,
        "pool_type": pool_type,
    }
    payload = {
        "schema": PAYLOAD_SCHEMA,
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
            "candidate_strategy_label": STRATEGY_LABELS[strategy],
            "corpora": corpora,
            "majority_votes": majority,
            "quality_tier": quality_tier,
            "pool_type": pool_type,
            "alignment_schema": alignment["schema"],
            "alignment_status": alignment.get("status"),
            "alignment_tokenizer_id": alignment.get("tokenizer_id"),
            "phase3a_candidate_schema": candidate.get("candidate_schema"),
        },
        "model_votes": votes,
        "queue_rank": None,
    }
    stratum = (strategy, quality_tier, sources[0])
    return csv_record, payload, stratum


def stratified_queue_ranks(
    descriptors: Sequence[tuple[str, tuple[str, str, str]]], seed: str
) -> dict[str, int]:
    """Deterministically round-robin strategy/quality/source strata."""

    buckets: dict[tuple[str, str, str], list[tuple[str, str]]] = defaultdict(list)
    for review_id, stratum in descriptors:
        digest = hashlib.sha256(f"{seed}\0{review_id}".encode("utf-8")).hexdigest()
        buckets[stratum].append((digest, review_id))
    for values in buckets.values():
        values.sort()
    ordered_keys = sorted(buckets)
    ranks: dict[str, int] = {}
    offsets = {key: 0 for key in ordered_keys}
    while len(ranks) < len(descriptors):
        progressed = False
        for key in ordered_keys:
            position = offsets[key]
            values = buckets[key]
            if position < len(values):
                review_id = values[position][1]
                if review_id in ranks:
                    raise ValueError(f"Duplicate review task ID: {review_id}")
                ranks[review_id] = len(ranks)
                offsets[key] = position + 1
                progressed = True
        if not progressed:
            raise RuntimeError("Queue stratification made no progress")
    return ranks


def write_csv_header(handle: Any) -> csv.DictWriter:
    writer = csv.DictWriter(
        handle,
        fieldnames=list(CSV_FIELDS),
        dialect="excel",
        lineterminator="\r\n",
        extrasaction="raise",
    )
    writer.writeheader()
    return writer


def _spreadsheet_safe_record(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: spreadsheet_safe_cell(value) for key, value in record.items()}


def resolve_inputs(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    selection = config.get("selection")
    if isinstance(selection, list):
        result = []
        for item in selection:
            if not isinstance(item, dict):
                raise ValueError("selection entries must be objects")
            result.append(
                {
                    "language": str(item["language"]),
                    "candidate_path": project_path(item["candidate_file"]),
                    "alignment_path": project_path(item["alignment_file"]),
                    "expected_tasks": (
                        None
                        if item.get("expected_tasks") is None
                        else int(item["expected_tasks"])
                    ),
                }
            )
        return sorted(result, key=lambda item: item["language"])

    candidate_root = project_path(config["candidate_root"])
    alignment_root = project_path(config["alignment_root"])
    languages = [str(value) for value in config["languages"]]
    expected = config.get("expected_counts", {})
    return [
        {
            "language": language,
            "candidate_path": candidate_root / "data" / language / CANDIDATE_FILENAME,
            "alignment_path": alignment_root / language / "alignments" / ALIGNMENT_FILENAME,
            "expected_tasks": (
                None if language not in expected else int(expected[language])
            ),
        }
        for language in sorted(languages)
    ]


def _write_language(
    temporary: Path,
    item: Mapping[str, Any],
    *,
    seed: str,
    pool_type: str,
    spreadsheet_safe: bool,
) -> dict[str, Any]:
    language = str(item["language"])
    candidate_path = Path(item["candidate_path"])
    alignment_path = Path(item["alignment_path"])
    if not candidate_path.is_file() or not alignment_path.is_file():
        missing = [str(path) for path in (candidate_path, alignment_path) if not path.is_file()]
        raise FileNotFoundError(", ".join(missing))

    data_dir = temporary / "data" / language
    payload_dir = temporary / "payloads" / language
    data_dir.mkdir(parents=True)
    payload_dir.mkdir(parents=True)
    spool = temporary / f".{language}.unranked.jsonl"
    descriptors: list[tuple[str, tuple[str, str, str]]] = []
    with spool.open("w", encoding="utf-8", newline="\n") as handle:
        for candidate, alignment in stream_join_candidates(
            candidate_path, alignment_path, language
        ):
            csv_record, payload, stratum = candidate_to_records(
                candidate, alignment, pool_type=pool_type
            )
            descriptors.append((csv_record["review_task_id"], stratum))
            write_jsonl_record(
                handle,
                {"csv": csv_record, "payload": payload},
            )

    expected = item.get("expected_tasks")
    if expected is not None and len(descriptors) != int(expected):
        raise ValueError(
            f"{language}: observed {len(descriptors)} tasks, expected {expected}"
        )
    ranks = stratified_queue_ranks(descriptors, f"{seed}\0{language}")
    csv_path = data_dir / CSV_FILENAME
    safe_path = data_dir / SAFE_CSV_FILENAME
    payload_path = payload_dir / PAYLOAD_FILENAME
    counts: Counter[str] = Counter()
    safe_context = (
        safe_path.open("w", encoding="utf-8", newline="")
        if spreadsheet_safe
        else None
    )
    try:
        with (
            csv_path.open("w", encoding="utf-8", newline="") as csv_handle,
            payload_path.open("w", encoding="utf-8", newline="\n") as payload_handle,
        ):
            writer = write_csv_header(csv_handle)
            safe_writer = write_csv_header(safe_context) if safe_context else None
            for value in read_jsonl(spool):
                csv_record = value["csv"]
                payload = value["payload"]
                review_id = str(csv_record["review_task_id"])
                rank = ranks[review_id]
                csv_record["queue_rank"] = rank
                payload["queue_rank"] = rank
                payload = with_payload_hash(payload)
                writer.writerow(csv_record)
                if safe_writer:
                    safe_writer.writerow(_spreadsheet_safe_record(csv_record))
                write_jsonl_record(payload_handle, payload)
                counts[f"strategy:{payload['candidate_strategy']}"] += 1
                counts[f"quality:{payload['public_metadata']['quality_tier']}"] += 1
    finally:
        if safe_context:
            safe_context.close()
    spool.unlink()

    record = {
        "language": language,
        "candidate_file": str(candidate_path),
        "candidate_sha256": sha256(candidate_path),
        "alignment_file": str(alignment_path),
        "alignment_sha256": sha256(alignment_path),
        "tasks": len(descriptors),
        "csv_file": csv_path.relative_to(temporary).as_posix(),
        "csv_bytes": csv_path.stat().st_size,
        "csv_sha256": sha256(csv_path),
        "payload_file": payload_path.relative_to(temporary).as_posix(),
        "payload_bytes": payload_path.stat().st_size,
        "payload_sha256": sha256(payload_path),
        "spreadsheet_safe_file": (
            safe_path.relative_to(temporary).as_posix() if spreadsheet_safe else ""
        ),
        "spreadsheet_safe_bytes": safe_path.stat().st_size if spreadsheet_safe else 0,
        "spreadsheet_safe_sha256": sha256(safe_path) if spreadsheet_safe else "",
        "counts": dict(sorted(counts.items())),
    }
    return record


def _write_manifest_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fields = (
        "language",
        "candidate_file",
        "candidate_sha256",
        "alignment_file",
        "alignment_sha256",
        "tasks",
        "csv_file",
        "csv_bytes",
        "csv_sha256",
        "payload_file",
        "payload_bytes",
        "payload_sha256",
        "spreadsheet_safe_file",
        "spreadsheet_safe_bytes",
        "spreadsheet_safe_sha256",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fields})


def _validate_token_array(
    tokens: Any, text: str, pair_id: str, side: str
) -> None:
    if not isinstance(tokens, list):
        raise ValueError(f"{side} tokens are not a list for {pair_id}")
    for expected_index, token in enumerate(tokens):
        if not isinstance(token, dict) or int(token.get("index", -1)) != expected_index:
            raise ValueError(f"Non-global {side} token index for {pair_id}")
        start, end = int(token["start"]), int(token["end"])
        if text[start:end] != token.get("text"):
            raise ValueError(f"Token/text mismatch on {side} for {pair_id}")


def validate_pool(
    pool_root: Path, expected_total: int | None = None, *, write_report: bool = True
) -> dict[str, Any]:
    pool_root = pool_root.resolve()
    config = load_json(pool_root / "pool_config.json")
    manifest = load_json(pool_root / MANIFEST_JSON_FILENAME)
    if config.get("schema") != POOL_CONFIG_SCHEMA:
        raise ValueError("Unexpected annotation-pool config schema")
    if manifest.get("schema") != POOL_MANIFEST_SCHEMA:
        raise ValueError("Unexpected annotation-pool manifest schema")
    rows = manifest.get("files")
    if not isinstance(rows, list) or len(rows) != 12 and config.get("require_12_languages", True):
        raise ValueError("The primary pool must contain exactly 12 language exports")

    seen_tasks: set[str] = set()
    total = 0
    languages: dict[str, int] = {}
    missing = object()
    for item in rows:
        language = str(item["language"])
        csv_path = pool_root / item["csv_file"]
        payload_path = pool_root / item["payload_file"]
        for path, size_key, hash_key in (
            (csv_path, "csv_bytes", "csv_sha256"),
            (payload_path, "payload_bytes", "payload_sha256"),
        ):
            if path.stat().st_size != int(item[size_key]) or sha256(path) != item[hash_key]:
                raise ValueError(f"Manifest integrity failure: {path}")
        with csv_path.open(encoding="utf-8", newline="") as csv_handle:
            csv_reader = csv.DictReader(csv_handle)
            if tuple(csv_reader.fieldnames or ()) != CSV_FIELDS:
                raise ValueError(f"Unexpected CSV fields: {csv_path}")
            payload_reader = read_jsonl(payload_path)
            count = 0
            ranks: set[int] = set()
            for csv_record, payload in zip_longest(
                csv_reader, payload_reader, fillvalue=missing
            ):
                if csv_record is missing or payload is missing:
                    raise ValueError(f"CSV/payload lengths differ for {language}")
                review_id = str(csv_record["review_task_id"])
                if review_id in seen_tasks:
                    raise ValueError(f"Duplicate review task ID: {review_id}")
                seen_tasks.add(review_id)
                rank = int(csv_record["queue_rank"])
                ranks.add(rank)
                if (
                    payload.get("schema") != PAYLOAD_SCHEMA
                    or payload.get("task_id") != review_id
                    or payload.get("review_task_id") != review_id
                    or payload.get("canonical_pair_id") != csv_record["canonical_pair_id"]
                    or payload.get("language") != language
                    or payload.get("source_text") != csv_record["original"]
                    or payload.get("target_text") != csv_record["simplification"]
                    or payload.get("candidate_strategy")
                    != csv_record["candidate_strategy_code"]
                    or int(payload.get("queue_rank", -1)) != rank
                    or payload_hash(payload) != payload.get("payload_hash")
                ):
                    raise ValueError(f"CSV/payload contract mismatch for {review_id}")
                for key, field in MODEL_VOTE_FIELDS.items():
                    vote = csv_record[field]
                    if vote not in {"yes", "no"} or payload["model_votes"].get(key) != vote:
                        raise ValueError(f"Invalid lowercase vote for {review_id}")
                _validate_token_array(
                    payload["source_tokens"], payload["source_text"], review_id, "source"
                )
                _validate_token_array(
                    payload["target_tokens"], payload["target_text"], review_id, "target"
                )
                count += 1
            if ranks != set(range(count)):
                raise ValueError(f"Queue ranks are not contiguous for {language}")
        if count != int(item["tasks"]):
            raise ValueError(f"Manifest count mismatch for {language}")
        languages[language] = count
        total += count

    configured_total = config.get("expected_total")
    target_total = expected_total if expected_total is not None else configured_total
    if target_total is not None and total != int(target_total):
        raise ValueError(f"Observed {total} tasks, expected {target_total}")
    report = {
        "schema": POOL_VALIDATION_SCHEMA,
        "valid": True,
        "pool_id": config["pool_id"],
        "pool_type": config["pool_type"],
        "tasks": total,
        "languages": languages,
        "unique_review_task_ids": len(seen_tasks),
        "canonical_text_preserved": True,
        "csv_dialect": "RFC4180",
        "votes": "lowercase_yes_no",
        "queue_rank": "deterministic_contiguous_per_language",
    }
    if write_report:
        reports = pool_root / "reports"
        reports.mkdir(exist_ok=True)
        (reports / "validation.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return report


def build(
    config_path: Path = DEFAULT_CONFIG,
    output_root_override: Path | None = None,
    overwrite: bool = False,
    spreadsheet_safe_override: bool | None = None,
) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = load_json(config_path)
    if config.get("schema") != POOL_CONFIG_SCHEMA:
        raise ValueError("Unexpected annotation-pool config schema")
    pool_type = str(config.get("pool_type"))
    if pool_type != PRIMARY_POOL_TYPE:
        raise ValueError("Primary builder requires the primary pool type")
    inputs = resolve_inputs(config)
    if config.get("require_12_languages", True) and len(inputs) != 12:
        raise ValueError("Primary pool configuration must select 12 languages")
    if len({item["language"] for item in inputs}) != len(inputs):
        raise ValueError("Each language must appear exactly once")

    output_base = (
        output_root_override.resolve()
        if output_root_override is not None
        else project_path(config["output_root"])
    )
    output_base.mkdir(parents=True, exist_ok=True)
    pool_id = str(config["pool_id"])
    pool_root = output_base / pool_id
    if pool_root.exists() and not overwrite:
        raise FileExistsError(f"Pool exists: {pool_root}; use --overwrite")
    spreadsheet_safe = (
        bool(config.get("spreadsheet_safe_export", False))
        if spreadsheet_safe_override is None
        else spreadsheet_safe_override
    )
    temporary = Path(tempfile.mkdtemp(prefix=f".{pool_id}-", dir=output_base))
    try:
        manifest_rows = [
            _write_language(
                temporary,
                item,
                seed=str(config.get("queue_seed", "phase4a-v1")),
                pool_type=pool_type,
                spreadsheet_safe=spreadsheet_safe,
            )
            for item in inputs
        ]
        total = sum(int(row["tasks"]) for row in manifest_rows)
        expected_total = config.get("expected_total")
        if expected_total is not None and total != int(expected_total):
            raise ValueError(f"Observed {total} primary tasks, expected {expected_total}")
        stored_config = dict(config)
        stored_config["source_config"] = str(config_path)
        stored_config["spreadsheet_safe_export"] = spreadsheet_safe
        (temporary / "pool_config.json").write_text(
            json.dumps(stored_config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest = {
            "schema": POOL_MANIFEST_SCHEMA,
            "pool_id": pool_id,
            "pool_type": pool_type,
            "tasks": total,
            "languages": [row["language"] for row in manifest_rows],
            "files": manifest_rows,
        }
        (temporary / MANIFEST_JSON_FILENAME).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        _write_manifest_csv(temporary / MANIFEST_CSV_FILENAME, manifest_rows)
        validation = validate_pool(
            temporary,
            int(expected_total) if expected_total is not None else None,
        )
        summary = {
            "schema": "feats-phase4a-annotation-pool-summary-v1",
            "pool_id": pool_id,
            "pool_type": pool_type,
            "tasks": total,
            "languages": {
                row["language"]: int(row["tasks"]) for row in manifest_rows
            },
            "spreadsheet_safe_export": spreadsheet_safe,
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
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    safe = parser.add_mutually_exclusive_group()
    safe.add_argument(
        "--spreadsheet-safe",
        action="store_true",
        dest="spreadsheet_safe",
        help="Also write formula-neutralized copies; canonical exports remain exact.",
    )
    safe.add_argument(
        "--no-spreadsheet-safe",
        action="store_false",
        dest="spreadsheet_safe",
    )
    parser.set_defaults(spreadsheet_safe=None)
    parser.add_argument(
        "--validate-only",
        type=Path,
        help="Validate an existing pool instead of building it.",
    )
    args = parser.parse_args()
    if args.validate_only:
        result = validate_pool(args.validate_only)
    else:
        result = build(
            args.config,
            args.output_root,
            args.overwrite,
            args.spreadsheet_safe,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
