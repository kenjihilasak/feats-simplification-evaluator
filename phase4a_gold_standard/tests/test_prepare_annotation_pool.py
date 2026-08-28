from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from data_contracts import (  # noqa: E402
    MODEL_ALIASES,
    POOL_CONFIG_SCHEMA,
    PRIMARY_POOL_TYPE,
    STRATEGY_LABELS,
)
from prepare_annotation_pool import build, validate_pool  # noqa: E402


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def token_data(text: str) -> tuple[list[str], list[list[int]], list[int]]:
    values = text.split(" ")
    offsets = []
    position = 0
    for value in values:
        start = text.index(value, position)
        end = start + len(value)
        offsets.append([start, end])
        position = end
    return values, offsets, list(range(len(values)))


def candidate(
    pair_id: str,
    original: str,
    simple: str,
    strategy: str,
    supporters: tuple[str, ...],
    *,
    quality: str = "majority_exact_singleton",
) -> dict[str, object]:
    predictions = {}
    for key, alias in MODEL_ALIASES.items():
        yes = key in supporters
        predictions[alias] = {
            "predicted_codes": [strategy] if yes else [],
            "strategy_count": int(yes),
            "strategy_scores": {
                code: (0.9 if code == strategy and yes else 0.1)
                for code in STRATEGY_LABELS
            },
        }
    return {
        "candidate_schema": "feats-phase3a-single-strategy-candidate-v1",
        "canonical_pair_id": pair_id,
        "language": "en",
        "original": original,
        "simple": simple,
        "sources": ["Source"],
        "provenance": [{"source": "Source", "corpus": "Corpus"}],
        "candidate_strategy_code": strategy,
        "candidate_strategy_label": STRATEGY_LABELS[strategy],
        "majority_votes": len(supporters),
        "quality_tier": quality,
        "model_predictions": predictions,
    }


def alignment(row: dict[str, object]) -> dict[str, object]:
    original = str(row["original"])
    simple = str(row["simple"])
    source_tokens, source_offsets, source_parents = token_data(original)
    target_tokens, target_offsets, target_parents = token_data(simple)
    links = [
        [index, index]
        for index in range(min(len(source_tokens), len(target_tokens)))
    ]
    return {
        "schema": "feats-phase3b-word-alignment-v2",
        "canonical_pair_id": row["canonical_pair_id"],
        "language": row["language"],
        "original_text_sha256": digest(original),
        "simple_text_sha256": digest(simple),
        "status": "aligned",
        "tokenizer_id": "test:space",
        "original_tokens": source_tokens,
        "simple_tokens": target_tokens,
        "original_token_offsets": source_offsets,
        "simple_token_offsets": target_offsets,
        "original_token_parent_indices": source_parents,
        "simple_token_parent_indices": target_parents,
        "alignment": links,
    }


def fixture(tmp_path: Path) -> tuple[Path, Path]:
    rows = [
        candidate(
            "pair:en:2",
            "=Formula source",
            "Exact, target\nsecond line",
            "SYN",
            ("e5", "qwen"),
        ),
        candidate(
            "pair:en:4",
            "A longer source",
            "A target",
            "OMIT",
            ("e5", "qwen", "xlmr"),
            quality="unanimous_exact_singleton",
        ),
        candidate(
            "pair:en:5",
            "Another source",
            "Another target",
            "SYN",
            ("qwen", "xlmr"),
            quality="label_majority_only",
        ),
    ]
    all_rows = [
        candidate(
            "pair:en:1",
            "Skipped alignment",
            "Skipped",
            "MOD",
            ("e5", "qwen"),
        ),
        *rows,
        candidate(
            "pair:en:9",
            "Trailing alignment",
            "Trailing",
            "MOD",
            ("e5", "qwen"),
        ),
    ]
    candidate_path = tmp_path / "inputs" / "candidates.jsonl"
    alignment_path = tmp_path / "inputs" / "alignments.jsonl"
    write_jsonl(candidate_path, rows)
    write_jsonl(alignment_path, [alignment(row) for row in all_rows])
    config = {
        "schema": POOL_CONFIG_SCHEMA,
        "pool_id": "fixture",
        "pool_type": PRIMARY_POOL_TYPE,
        "output_root": str(tmp_path / "pools"),
        "expected_total": 3,
        "require_12_languages": False,
        "queue_seed": "test-seed",
        "spreadsheet_safe_export": True,
        "selection": [
            {
                "language": "en",
                "candidate_file": str(candidate_path),
                "alignment_file": str(alignment_path),
                "expected_tasks": 3,
            }
        ],
    }
    config_path = tmp_path / "config.json"
    write_json(config_path, config)
    return config_path, tmp_path / "pools" / "fixture"


def test_builds_import_ready_pool_and_preserves_text(tmp_path: Path) -> None:
    config_path, pool_root = fixture(tmp_path)
    result = build(config_path)
    assert result["tasks"] == 3

    csv_path = pool_root / "data" / "en" / "annotation_pool.csv"
    raw = csv_path.read_bytes()
    assert b"\r\n" in raw
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["original"] == "=Formula source"
    assert rows[0]["simplification"] == "Exact, target\nsecond line"
    assert {
        rows[0]["e5_supports_strategy"],
        rows[0]["qwen_supports_strategy"],
        rows[0]["xlmr_supports_strategy"],
    } <= {"yes", "no"}
    assert sorted(int(row["queue_rank"]) for row in rows) == [0, 1, 2]
    assert len({row["review_task_id"] for row in rows}) == 3

    safe_path = (
        pool_root / "data" / "en" / "annotation_pool.spreadsheet_safe.csv"
    )
    with safe_path.open(encoding="utf-8", newline="") as handle:
        safe_rows = list(csv.DictReader(handle))
    assert safe_rows[0]["original"] == "'=Formula source"
    assert rows[0]["original"] == "=Formula source"

    payload_path = (
        pool_root / "payloads" / "en" / "annotation_tasks.jsonl"
    )
    payloads = [json.loads(line) for line in payload_path.read_text().splitlines()]
    assert payloads[0]["task_id"] == rows[0]["review_task_id"]
    assert payloads[0]["source_text"] == rows[0]["original"]
    assert payloads[0]["target_text"] == rows[0]["simplification"]
    assert payloads[0]["candidate_strategy"] == rows[0]["candidate_strategy_code"]
    assert payloads[0]["source_tokens"][0]["index"] == 0
    assert payloads[0]["source_tokens"][0]["parse_status"] == "not_parsed"
    assert payloads[0]["simalign_links"][0] == {
        "source_index": 0,
        "target_index": 0,
    }
    assert validate_pool(pool_root)["valid"] is True


def test_queue_rank_is_reproducible(tmp_path: Path) -> None:
    config_path, first_root = fixture(tmp_path)
    build(config_path)
    first_payload = (
        first_root / "payloads" / "en" / "annotation_tasks.jsonl"
    ).read_bytes()
    second_base = tmp_path / "second"
    build(config_path, second_base)
    second_payload = (
        second_base / "fixture" / "payloads" / "en" / "annotation_tasks.jsonl"
    ).read_bytes()
    assert first_payload == second_payload


def test_rejects_text_hash_mismatch(tmp_path: Path) -> None:
    config_path, _ = fixture(tmp_path)
    config = json.loads(config_path.read_text())
    path = Path(config["selection"][0]["alignment_file"])
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[2]["original_text_sha256"] = "0" * 64
    write_jsonl(path, rows)
    with pytest.raises(ValueError, match="text hash mismatch"):
        build(config_path)
