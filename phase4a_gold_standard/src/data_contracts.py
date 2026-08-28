#!/usr/bin/env python3
"""Shared, dependency-free contracts for Phase 4a data preparation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PRIMARY_POOL_TYPE = "primary_single_strategy_majority_vote"
SUPPLEMENTAL_POOL_TYPE = "supplemental_sparse_language"
POOL_TYPES = frozenset({PRIMARY_POOL_TYPE, SUPPLEMENTAL_POOL_TYPE})

STRATEGY_CODES = ("SYN", "MOD", "COMP", "EXPL", "SYNT", "OMIT")
STRATEGY_LABELS = {
    "SYN": "Synonymy",
    "MOD": "Modulation",
    "COMP": "Compression",
    "EXPL": "Explanation",
    "SYNT": "Syntactic Change",
    "OMIT": "Omission",
}
MODEL_KEYS = ("e5", "qwen", "xlmr")
MODEL_ALIASES = {
    "e5": "multilingual_e5_large_bce",
    "qwen": "qwen2p5_7b_pairwise_qlora",
    "xlmr": "xlmr_large_focal",
}
CSV_FIELDS = (
    "review_task_id",
    "queue_rank",
    "canonical_pair_id",
    "language",
    "sources",
    "corpora",
    "original",
    "simplification",
    "candidate_strategy_code",
    "candidate_strategy_label",
    "e5_supports_strategy",
    "qwen_supports_strategy",
    "xlmr_supports_strategy",
    "majority_votes",
    "quality_tier",
    "pool_type",
)

PAYLOAD_SCHEMA = "feats-phase4a-annotation-payload-v1"
SYNTAX_SCHEMA = "feats-phase4a-stanza-ud-syntax-v1"
SUPPLEMENTAL_SCHEMA = "feats-phase4a-supplemental-candidate-v1"
POOL_CONFIG_SCHEMA = "feats-phase4a-annotation-pool-config-v1"
POOL_MANIFEST_SCHEMA = "feats-phase4a-annotation-pool-manifest-v1"
POOL_VALIDATION_SCHEMA = "feats-phase4a-annotation-pool-validation-v1"
SYNTAX_CONFIG_SCHEMA = "feats-phase4a-stanza-ud-config-v1"
SYNTAX_MANIFEST_SCHEMA = "feats-phase4a-stanza-ud-manifest-v1"


def project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON at {path}:{line_number}") from error
            if not isinstance(value, dict):
                raise ValueError(f"Expected an object at {path}:{line_number}")
            yield value


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def write_jsonl_record(handle: Any, value: Mapping[str, Any]) -> None:
    handle.write(canonical_json(value) + "\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_strings(values: Iterable[Any]) -> list[str]:
    return sorted({str(value) for value in values if str(value).strip()})


def source_and_corpus_values(record: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    raw_sources = record.get("sources", [])
    if not isinstance(raw_sources, list):
        raise ValueError("sources must be a list")
    sources: list[Any] = list(raw_sources)
    corpora: list[Any] = []
    provenance = record.get("provenance", [])
    if not isinstance(provenance, list):
        raise ValueError("provenance must be a list")
    for item in provenance:
        if not isinstance(item, dict):
            raise ValueError("provenance items must be objects")
        if item.get("source") is not None:
            sources.append(item["source"])
        if item.get("corpus") is not None:
            corpora.append(item["corpus"])
    return stable_strings(sources), stable_strings(corpora)


def flattened_values(values: Iterable[str]) -> str:
    return " | ".join(values)


def spreadsheet_safe_cell(value: Any) -> Any:
    """Neutralize formulas only in the optional spreadsheet-safe copy."""

    if not isinstance(value, str) or not value:
        return value
    stripped = value.lstrip(" \t\r\n")
    if value[0] in "\t\r\n" or (stripped and stripped[0] in "=+-@"):
        return "'" + value
    return value


def task_id(record: Mapping[str, Any]) -> str:
    value = record.get("review_task_id") or record.get("canonical_pair_id")
    return str(value or "")


def make_review_task_id(
    canonical_pair_id: str, strategy_code: str, pool_type: str
) -> str:
    """Return a stable task identifier which also supports pair-strategy pools."""

    if not canonical_pair_id or strategy_code not in STRATEGY_CODES:
        raise ValueError("A canonical pair ID and known strategy code are required")
    if pool_type not in POOL_TYPES:
        raise ValueError(f"Unknown pool type: {pool_type}")
    parts = canonical_pair_id.split(":", 2)
    language = parts[1] if len(parts) > 1 else "und"
    value = f"{pool_type}\0{canonical_pair_id}\0{strategy_code}"
    suffix = hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
    return f"review:{language}:{strategy_code.lower()}:{suffix}"


def payload_hash(record: Mapping[str, Any]) -> str:
    """Hash a payload independent of its stored payload-hash value."""

    value = dict(record)
    value.pop("payload_hash", None)
    return text_sha256(canonical_json(value))


def with_payload_hash(record: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(record)
    value["payload_hash"] = payload_hash(value)
    return value
