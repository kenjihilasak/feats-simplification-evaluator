from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

import pytest


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from build_single_strategy_gold_candidates import build
from validate_single_strategy_gold_candidates import validate


MODELS = ("e5", "qwen", "xlmr")
CODES = ("SYN", "MOD", "COMP", "EXPL", "SYNT", "OMIT")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )


def prediction(
    pair_id: str, model_alias: str, codes: list[str]
) -> dict[str, object]:
    return {
        "id": pair_id,
        "canonical_pair_id": pair_id,
        "model_alias": model_alias,
        "predicted_codes": codes,
        "strategy_count": len(codes),
        "strategy_scores": {
            code: (0.8 if code in codes else 0.2) for code in CODES
        },
    }


def fixture(tmp_path: Path) -> tuple[Path, Path]:
    input_root = tmp_path / "input"
    runs_root = tmp_path / "runs"
    output_root = tmp_path / "candidates"
    experiment_id = "full"
    candidate_id = "single_strategy_v1"
    ids = [f"pair:en:{index}" for index in range(1, 6)]
    metadata = [
        {
            "id": pair_id,
            "canonical_pair_id": pair_id,
            "language": "en",
            "original": f"Original {index}",
            "simple": f"Simple {index}",
            "sources": ["SourceA"] if index < 5 else ["SourceB"],
            "provenance": [],
        }
        for index, pair_id in enumerate(ids, start=1)
    ]
    model_codes = {
        "e5": [
            ["SYN"],
            ["SYN", "MOD"],
            ["SYN", "MOD"],
            ["SYN"],
            ["COMP"],
        ],
        "qwen": [
            ["SYN"],
            ["SYN", "EXPL"],
            ["SYN", "MOD"],
            ["EXPL"],
            ["COMP"],
        ],
        "xlmr": [
            ["EXPL"],
            [],
            [],
            ["OMIT"],
            ["COMP"],
        ],
    }
    relative = Path("en/feats_consolidated.jsonl")
    write_jsonl(input_root / relative, metadata)
    experiment_root = runs_root / experiment_id
    for alias in MODELS:
        model_root = experiment_root / "models" / alias
        write_jsonl(
            model_root / "predictions" / relative,
            [
                prediction(pair_id, alias, codes)
                for pair_id, codes in zip(ids, model_codes[alias])
            ],
        )
        write_json(
            model_root / "reports" / "validation.json",
            {
                "valid": True,
                "expected_pairs": len(ids),
                "observed_pairs": len(ids),
            },
        )
        write_json(
            model_root / "run_config.json",
            {
                "status": "complete",
                "processed_pairs": len(ids),
                "model": {
                    "model_id": f"owner/{alias}",
                    "revision": f"{alias}-revision",
                },
                "model_config_sha256": f"{alias}-config-sha",
                "input_manifest_sha256": "input-sha",
            },
        )
    experiment_config = tmp_path / "experiment.json"
    write_json(
        experiment_config,
        {
            "schema": "feats-phase3-experiment-v2",
            "experiment_id": experiment_id,
            "input_root": str(input_root),
            "runs_root": str(runs_root),
            "expected_pairs": len(ids),
            "models": {alias: f"{alias}.json" for alias in MODELS},
            "selection": {"files": [relative.as_posix()]},
        },
    )
    candidate_config = tmp_path / "candidate.json"
    write_json(
        candidate_config,
        {
            "schema": "feats-phase3a-gold-candidate-config-v1",
            "candidate_id": candidate_id,
            "source_experiment_config": str(experiment_config),
            "required_models": list(MODELS),
            "voting": {
                "unit": "strategy_label",
                "minimum_votes": 2,
                "required_consensus_cardinality": 1,
            },
            "output_root": str(output_root),
        },
    )
    return candidate_config, output_root / candidate_id


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_builds_label_majority_singleton_candidates(tmp_path: Path) -> None:
    config_path, candidate_root = fixture(tmp_path)
    result = build(config_path)

    assert result["input_pairs"] == 5
    assert result["candidate_pairs"] == 3
    assert result["excluded"] == {
        "no_majority_pairs": 1,
        "multiple_majority_pairs": 1,
    }
    assert result["quality_tiers"] == {
        "unanimous_exact_singleton": 1,
        "majority_exact_singleton": 1,
        "label_majority_only": 1,
    }

    output = candidate_root / "data" / "en" / "single_strategy_candidates.jsonl"
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert [row["canonical_pair_id"] for row in rows] == [
        "pair:en:1",
        "pair:en:2",
        "pair:en:5",
    ]
    assert [row["candidate_strategy_code"] for row in rows] == [
        "SYN",
        "SYN",
        "COMP",
    ]
    assert rows[0]["majority_votes"] == 2
    assert rows[1]["quality_tier"] == "label_majority_only"
    assert rows[2]["supporting_models"] == list(MODELS)
    assert rows[2]["candidate_status"] == "unreviewed_model_consensus"

    languages = csv_rows(
        candidate_root / "reports" / "candidates_by_language.csv"
    )
    assert languages[0]["input_pairs"] == "5"
    assert languages[0]["candidate_pairs"] == "3"
    sources = csv_rows(
        candidate_root / "reports" / "candidates_by_language_source.csv"
    )
    assert [(row["source"], row["candidate_pairs"]) for row in sources] == [
        ("SourceA", "2"),
        ("SourceB", "1"),
    ]
    manifest = csv_rows(candidate_root / "CANDIDATE_MANIFEST.csv")
    assert manifest[0]["candidate_pairs"] == "3"
    assert len(manifest[0]["sha256"]) == 64
    validation = validate(candidate_root)
    assert validation["valid"] is True
    assert validation["candidate_pairs"] == 3
    assert validation["unique_canonical_pair_ids"] == 3


def test_rejects_prediction_id_mismatch(tmp_path: Path) -> None:
    config_path, _ = fixture(tmp_path)
    path = (
        tmp_path
        / "runs"
        / "full"
        / "models"
        / "xlmr"
        / "predictions"
        / "en"
        / "feats_consolidated.jsonl"
    )
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["id"] = "wrong"
    rows[0]["canonical_pair_id"] = "wrong"
    write_jsonl(path, rows)
    with pytest.raises(ValueError, match="ID mismatch"):
        build(config_path)


def test_refuses_to_replace_existing_output_by_default(tmp_path: Path) -> None:
    config_path, _ = fixture(tmp_path)
    build(config_path)
    with pytest.raises(FileExistsError, match="--overwrite"):
        build(config_path)


def test_validation_rejects_modified_candidate_data(tmp_path: Path) -> None:
    config_path, candidate_root = fixture(tmp_path)
    build(config_path)
    path = candidate_root / "data" / "en" / "single_strategy_candidates.jsonl"
    path.write_text(path.read_text() + "{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="byte size differs"):
        validate(candidate_root)
