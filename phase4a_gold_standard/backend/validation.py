"""Canonical validation for imported tasks and human annotations.

The HTTP layer and command-line importer both use these functions.  Keeping
the rules here also makes it possible for the SQLite layer to defend itself
when it is called directly by maintenance scripts.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict, deque
from typing import Any, Iterable, Mapping, Sequence

from .constants import (
    ALIGNMENT_JUDGMENTS,
    BLINDED_METADATA_KEYS,
    CORRECTED_STRATEGIES,
    MAX_IMPORT_BATCH,
    MAX_NOTES_LENGTH,
    MAX_SKIP_REASON_LENGTH,
    SEMANTIC_ROLES,
    STRATEGIES,
    VERDICTS,
)
from .errors import ValidationError
from .security import canonical_json


def _nonempty_string(value: Any, field: str, *, maximum: int = 10_000) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} must be a non-empty string")
    value = value.strip()
    if len(value) > maximum:
        raise ValidationError(f"{field} is longer than {maximum} characters")
    return value


def _first(record: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in record and record[name] is not None:
            return record[name]
    return default


def _token_list(value: Any, text: str, field: str) -> list[dict[str, Any]]:
    if value is None:
        value = [{"text": token} for token in text.split()]
    if not isinstance(value, list):
        raise ValidationError(f"{field} must be a list")
    result: list[dict[str, Any]] = []
    seen: set[int] = set()
    for position, raw in enumerate(value):
        if isinstance(raw, str):
            token: dict[str, Any] = {"text": raw}
        elif isinstance(raw, Mapping):
            token = dict(raw)
        else:
            raise ValidationError(f"{field}[{position}] must be an object or string")
        index_value = token.get("index", position)
        if isinstance(index_value, bool):
            raise ValidationError(f"{field}[{position}].index must be an integer")
        try:
            index = int(index_value)
        except (TypeError, ValueError) as error:
            raise ValidationError(f"{field}[{position}].index must be an integer") from error
        if index < 0 or index in seen:
            raise ValidationError(f"{field} token indices must be unique non-negative integers")
        seen.add(index)
        token_text = token.get("text")
        if not isinstance(token_text, str) or not token_text:
            raise ValidationError(f"{field}[{position}].text must be a non-empty string")
        token["index"] = index
        # Normalise common parser spellings while retaining useful parser data.
        if "upos" not in token and token.get("pos") is not None:
            token["upos"] = token["pos"]
        result.append(token)
    return sorted(result, key=lambda item: int(item["index"]))


def _nested_tokens(record: Mapping[str, Any], side: str) -> Any:
    direct = _first(
        record,
        f"{side}_tokens",
        "original_tokens" if side == "source" else "simplification_tokens",
    )
    if direct is not None:
        return direct
    syntax = record.get("syntax")
    if isinstance(syntax, Mapping):
        side_value = _first(
            syntax,
            side,
            "original" if side == "source" else "simplification",
        )
        if isinstance(side_value, Mapping):
            return side_value.get("tokens") or side_value.get("words")
        if isinstance(side_value, list):
            return side_value
    side_syntax = _first(
        record,
        f"{side}_syntax",
        "original_syntax" if side == "source" else "simplification_syntax",
    )
    if isinstance(side_syntax, Mapping):
        return side_syntax.get("tokens") or side_syntax.get("words")
    return None


def _pair(raw: Any, field: str) -> tuple[int, int, dict[str, Any]]:
    if isinstance(raw, (list, tuple)) and len(raw) == 2:
        source_value, target_value = raw
        extra: dict[str, Any] = {}
    elif isinstance(raw, Mapping):
        extra = dict(raw)
        link = raw.get("link")
        if isinstance(link, (list, tuple)) and len(link) == 2:
            source_value, target_value = link
        else:
            source_value = _first(
                raw, "source_index", "source_token_index", "source", "src", "i"
            )
            target_value = _first(
                raw, "target_index", "target_token_index", "target", "tgt", "j"
            )
    else:
        raise ValidationError(f"{field} entries must be link objects or [source, target] pairs")
    if isinstance(source_value, bool) or isinstance(target_value, bool):
        raise ValidationError(f"{field} indices must be integers")
    try:
        source_index = int(source_value)
        target_index = int(target_value)
    except (TypeError, ValueError) as error:
        raise ValidationError(f"{field} indices must be integers") from error
    if source_index < 0 or target_index < 0:
        raise ValidationError(f"{field} indices must be non-negative")
    return source_index, target_index, extra


def normalise_links(value: Any, field: str = "simalign_links") -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        value = value.get("links", value.get("alignments"))
    if not isinstance(value, list):
        raise ValidationError(f"{field} must be a list")
    result: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for raw in value:
        source_index, target_index, extra = _pair(raw, field)
        pair = (source_index, target_index)
        if pair in seen:
            raise ValidationError(f"{field} contains duplicate link {pair}")
        seen.add(pair)
        clean = {
            key: item
            for key, item in extra.items()
            if key
            not in {
                "link",
                "source_index",
                "source_token_index",
                "source",
                "src",
                "i",
                "target_index",
                "target_token_index",
                "target",
                "tgt",
                "j",
                "judgment",
            }
        }
        clean.update({"source_index": source_index, "target_index": target_index})
        result.append(clean)
    return sorted(result, key=lambda item: (item["source_index"], item["target_index"]))


def blind_metadata(value: Any) -> Any:
    """Recursively remove information that could reveal model consensus/tier."""

    if isinstance(value, Mapping):
        return {
            str(key): blind_metadata(item)
            for key, item in value.items()
            if str(key).lower() not in BLINDED_METADATA_KEYS
        }
    if isinstance(value, list):
        return [blind_metadata(item) for item in value]
    return value


def normalise_task(record: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise ValidationError("each imported task must be an object")
    task_id = _nonempty_string(
        _first(record, "task_id", "review_task_id", "canonical_pair_id"), "task_id", maximum=300
    )
    canonical_pair_id = _nonempty_string(
        _first(record, "canonical_pair_id", default=task_id),
        "canonical_pair_id",
        maximum=300,
    )
    language = _nonempty_string(record.get("language"), "language", maximum=32).lower()
    source_text = _nonempty_string(
        _first(record, "source_text", "original"), "source_text", maximum=100_000
    )
    target_text = _nonempty_string(
        _first(record, "target_text", "simplification"), "target_text", maximum=100_000
    )
    candidate_strategy = _nonempty_string(
        _first(record, "candidate_strategy", "candidate_strategy_code", "strategy"),
        "candidate_strategy",
        maximum=20,
    ).upper()
    if candidate_strategy not in STRATEGIES:
        raise ValidationError(f"unknown candidate strategy: {candidate_strategy}")

    raw_sources = record.get("sources", [])
    if isinstance(raw_sources, str):
        raw_sources = [raw_sources]
    if not isinstance(raw_sources, list):
        raise ValidationError("sources must be a list of strings")
    sources = sorted({_nonempty_string(item, "sources[]", maximum=300) for item in raw_sources})

    source_tokens = _token_list(
        _nested_tokens(record, "source"), source_text, "source_tokens"
    )
    target_tokens = _token_list(
        _nested_tokens(record, "target"), target_text, "target_tokens"
    )
    raw_links = _first(record, "simalign_links", "alignments")
    if raw_links is None:
        simalign = _first(record, "simalign", "word_alignment")
        raw_links = simalign.get("links") if isinstance(simalign, Mapping) else simalign
    simalign_links = normalise_links(raw_links)
    source_indices = {int(token["index"]) for token in source_tokens}
    target_indices = {int(token["index"]) for token in target_tokens}
    for link in simalign_links:
        if link["source_index"] not in source_indices or link["target_index"] not in target_indices:
            raise ValidationError("a SimAlign link refers to a token index that does not exist")

    private = dict(record.get("model_votes") or {})
    for key in BLINDED_METADATA_KEYS:
        if key in record and key != "model_votes":
            private[key] = record[key]
    metadata = dict(record.get("public_metadata") or record.get("metadata") or {})
    # Preserve blinded selection metadata for administrators/exports before it
    # is removed from the reviewer-facing payload.
    for key in BLINDED_METADATA_KEYS:
        if key in metadata and key != "model_votes":
            private.setdefault(key, metadata[key])
    for key in ("corpora", "provenance", "candidate_strategy_label", "taxonomy_version"):
        if key in record:
            metadata[key] = record[key]
    metadata = blind_metadata(metadata)

    normalised: dict[str, Any] = {
        "task_id": task_id,
        "canonical_pair_id": canonical_pair_id,
        "language": language,
        "sources": sources,
        "source_text": source_text,
        "target_text": target_text,
        "candidate_strategy": candidate_strategy,
        "source_tokens": source_tokens,
        "target_tokens": target_tokens,
        "simalign_links": simalign_links,
        "public_metadata": metadata,
        "model_votes": private,
    }
    if record.get("queue_rank") is not None:
        try:
            normalised["queue_rank"] = int(record["queue_rank"])
        except (TypeError, ValueError) as error:
            raise ValidationError("queue_rank must be an integer") from error
        if normalised["queue_rank"] < 0:
            raise ValidationError("queue_rank must be non-negative")
    hash_payload = {key: value for key, value in normalised.items() if key != "queue_rank"}
    normalised["payload_hash"] = hashlib.sha256(
        canonical_json(hash_payload).encode("utf-8")
    ).hexdigest()
    return normalised


def assign_stratified_queue_ranks(tasks: Sequence[dict[str, Any]]) -> None:
    """Assign deterministic per-language ranks by round-robin stratum.

    A stratum is candidate-strategy x source.  This avoids presenting long
    runs from one model/source while remaining stable across repeated imports.
    Explicit ranks are respected only when every record supplies one.
    """

    if tasks and all("queue_rank" in task for task in tasks):
        return
    by_language: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        by_language[task["language"]].append(task)
    for language in sorted(by_language):
        buckets: dict[tuple[str, str], deque[dict[str, Any]]] = defaultdict(deque)
        for task in sorted(by_language[language], key=lambda item: item["task_id"]):
            source = task["sources"][0] if task["sources"] else ""
            buckets[(task["candidate_strategy"], source)].append(task)
        rank = 0
        keys = sorted(buckets)
        while keys:
            next_keys: list[tuple[str, str]] = []
            for key in keys:
                task = buckets[key].popleft()
                task["queue_rank"] = rank
                rank += 1
                if buckets[key]:
                    next_keys.append(key)
            keys = next_keys


def normalise_tasks(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        if len(tasks) >= MAX_IMPORT_BATCH:
            raise ValidationError(f"an import may contain at most {MAX_IMPORT_BATCH} tasks")
        task = normalise_task(record)
        if task["task_id"] in seen:
            raise ValidationError(f"duplicate task_id in import: {task['task_id']}")
        seen.add(task["task_id"])
        tasks.append(task)
    assign_stratified_queue_ranks(tasks)
    return tasks


def _normalise_evidence(
    value: Any, field: str, valid_indices: set[int]
) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValidationError(f"{field} must be a list")
    result: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()
    for position, raw in enumerate(value):
        if not isinstance(raw, Mapping):
            raise ValidationError(f"{field}[{position}] must be an object")
        try:
            token_index = int(raw.get("token_index"))
        except (TypeError, ValueError) as error:
            raise ValidationError(f"{field}[{position}].token_index must be an integer") from error
        role = raw.get("role")
        if role not in SEMANTIC_ROLES:
            raise ValidationError(f"{field}[{position}] has unknown evidence role {role!r}")
        if token_index not in valid_indices:
            raise ValidationError(f"{field}[{position}] refers to a token that does not exist")
        key = (token_index, role)
        if key in seen:
            raise ValidationError(f"{field} contains duplicate evidence {key}")
        seen.add(key)
        result.append({"token_index": token_index, "role": role})
    return sorted(result, key=lambda item: (item["token_index"], item["role"]))


def normalise_annotation(
    annotation: Mapping[str, Any],
    *,
    source_tokens: Sequence[Mapping[str, Any]],
    target_tokens: Sequence[Mapping[str, Any]],
    simalign_links: Sequence[Mapping[str, Any]],
    candidate_strategy: str | None = None,
    final: bool = False,
) -> dict[str, Any]:
    if not isinstance(annotation, Mapping):
        raise ValidationError("annotation must be an object")
    verdict = annotation.get("verdict")
    if verdict == "unsure":
        verdict = "uncertain"
    if verdict in ("", None):
        verdict = None
    elif verdict not in VERDICTS:
        raise ValidationError(f"unknown verdict: {verdict}")
    if final and verdict is None:
        raise ValidationError("a verdict is required before submission")

    corrected = annotation.get("corrected_strategy")
    if isinstance(corrected, str):
        corrected = corrected.strip().upper() or None
    if verdict == "incorrect" and final and corrected is None:
        corrected = "NONE"
    if corrected is not None and corrected not in CORRECTED_STRATEGIES:
        raise ValidationError(f"unknown corrected strategy: {corrected}")
    if verdict in {"correct", "uncertain"} and corrected is not None:
        raise ValidationError("corrected_strategy is only valid for an incorrect verdict")

    notes = annotation.get("notes", "")
    if not isinstance(notes, str):
        raise ValidationError("notes must be a string")
    if len(notes) > MAX_NOTES_LENGTH:
        raise ValidationError(f"notes may contain at most {MAX_NOTES_LENGTH} characters")
    source_indices = {int(token["index"]) for token in source_tokens}
    target_indices = {int(token["index"]) for token in target_tokens}
    source_evidence = _normalise_evidence(
        annotation.get("source_evidence"), "source_evidence", source_indices
    )
    target_evidence = _normalise_evidence(
        annotation.get("target_evidence"), "target_evidence", target_indices
    )
    if final and verdict in {"correct", "incorrect"}:
        effective_strategy = (
            candidate_strategy if verdict == "correct" else corrected
        )
        if effective_strategy in STRATEGIES:
            if not source_evidence:
                raise ValidationError(
                    "submitted strategy judgments require source evidence"
                )
            if effective_strategy != "OMIT" and not target_evidence:
                raise ValidationError(
                    "submitted non-OMIT strategy judgments require target evidence"
                )

    existing = {
        (int(link["source_index"]), int(link["target_index"])) for link in simalign_links
    }
    judgments_value = annotation.get("alignment_judgments") or []
    if not isinstance(judgments_value, list):
        raise ValidationError("alignment_judgments must be a list")
    judgments: list[dict[str, Any]] = []
    judged: set[tuple[int, int]] = set()
    for raw in judgments_value:
        source_index, target_index, extra = _pair(raw, "alignment_judgments")
        pair = (source_index, target_index)
        judgment = extra.get("judgment") if isinstance(raw, Mapping) else None
        if isinstance(raw, Mapping):
            judgment = raw.get("judgment")
        if judgment not in ALIGNMENT_JUDGMENTS:
            raise ValidationError(f"unknown alignment judgment: {judgment}")
        if pair not in existing:
            raise ValidationError("alignment judgments may only reference SimAlign links")
        if pair in judged:
            raise ValidationError(f"duplicate alignment judgment for link {pair}")
        judged.add(pair)
        judgments.append(
            {
                "source_index": source_index,
                "target_index": target_index,
                "judgment": judgment,
            }
        )

    added_value = annotation.get("human_added_links") or []
    if not isinstance(added_value, list):
        raise ValidationError("human_added_links must be a list")
    added: list[dict[str, int]] = []
    added_seen: set[tuple[int, int]] = set()
    for raw in added_value:
        source_index, target_index, _ = _pair(raw, "human_added_links")
        pair = (source_index, target_index)
        if source_index not in source_indices or target_index not in target_indices:
            raise ValidationError("a human-added link refers to a token that does not exist")
        if pair in existing:
            raise ValidationError("a human-added link duplicates an existing SimAlign link")
        if pair in added_seen:
            raise ValidationError(f"duplicate human-added link {pair}")
        added_seen.add(pair)
        added.append({"source_index": source_index, "target_index": target_index})

    return {
        "verdict": verdict,
        "corrected_strategy": corrected,
        "source_evidence": source_evidence,
        "target_evidence": target_evidence,
        "alignment_judgments": sorted(
            judgments, key=lambda item: (item["source_index"], item["target_index"])
        ),
        "human_added_links": sorted(
            added, key=lambda item: (item["source_index"], item["target_index"])
        ),
        "notes": notes,
    }


def validate_skip_reason(reason: Any) -> str:
    return _nonempty_string(reason, "reason", maximum=MAX_SKIP_REASON_LENGTH)
