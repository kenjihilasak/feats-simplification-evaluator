from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

import pytest


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from analyze_full_run import analyze


MODELS = ("model_a", "model_b")
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
        "predicted_labels": [],
        "strategy_count": len(codes),
        "strategy_scores": {
            code: (0.8 if code in codes else 0.2) for code in CODES
        },
    }


def fixture(tmp_path: Path) -> tuple[Path, Path]:
    input_root = tmp_path / "input"
    runs_root = tmp_path / "runs"
    experiment_id = "full"
    experiment_root = runs_root / experiment_id
    records = {
        "en/feats_consolidated.jsonl": [
            {
                "id": "pair:en:1",
                "canonical_pair_id": "pair:en:1",
                "language": "en",
                "sources": ["SourceA"],
                "corpora": [{"source": "SourceA", "corpus": "Corpus1"}],
                "provenance": [],
            },
            {
                "id": "pair:en:2",
                "canonical_pair_id": "pair:en:2",
                "language": "en",
                "sources": ["SourceA", "SourceB", "SourceA"],
                "corpora": [
                    {"source": "SourceA", "corpus": "Corpus1"},
                    {"source": "SourceB", "corpus": "Corpus2"},
                ],
                "provenance": [],
            },
        ],
        "es/feats_consolidated.jsonl": [
            {
                "id": "pair:es:1",
                "canonical_pair_id": "pair:es:1",
                "language": "es",
                "sources": ["SourceC"],
                "corpora": [{"source": "SourceC", "corpus": "Corpus3"}],
                "provenance": [],
            }
        ],
    }
    model_codes = {
        "model_a": [["SYN"], ["SYN", "OMIT"], []],
        "model_b": [["SYN"], ["OMIT"], ["EXPL"]],
    }
    flat_ids = ["pair:en:1", "pair:en:2", "pair:es:1"]
    for relative, rows in records.items():
        write_jsonl(input_root / relative, rows)
    for alias in MODELS:
        offset = 0
        for relative, rows in records.items():
            count = len(rows)
            write_jsonl(
                experiment_root / "models" / alias / "predictions" / relative,
                [
                    prediction(pair_id, alias, codes)
                    for pair_id, codes in zip(
                        flat_ids[offset : offset + count],
                        model_codes[alias][offset : offset + count],
                    )
                ],
            )
            offset += count
        write_json(
            experiment_root / "models" / alias / "reports" / "validation.json",
            {"valid": True, "expected_pairs": 3, "observed_pairs": 3},
        )
    config_path = tmp_path / "experiment.json"
    write_json(
        config_path,
        {
            "schema": "feats-phase3-experiment-v2",
            "experiment_id": experiment_id,
            "input_root": str(input_root),
            "runs_root": str(runs_root),
            "expected_pairs": 3,
            "models": {alias: f"{alias}.json" for alias in MODELS},
            "selection": {"files": list(records)},
        },
    )
    return config_path, experiment_root


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_full_analysis_answers_language_source_and_agreement(tmp_path: Path) -> None:
    config_path, experiment_root = fixture(tmp_path)
    result = analyze(config_path)
    assert result["canonical_pairs"] == 3
    reports = experiment_root / "reports"

    overall = csv_rows(reports / "strategy_cardinality_overall.csv")
    model_a = next(row for row in overall if row["model_alias"] == "model_a")
    assert float(model_a["mean_strategy_count"]) == pytest.approx(1.0)
    assert float(model_a["zero_strategy_pct"]) == pytest.approx(100 / 3)

    sources = csv_rows(reports / "strategy_cardinality_by_language_source.csv")
    source_a = next(
        row
        for row in sources
        if row["model_alias"] == "model_a"
        and row["language"] == "en"
        and row["source"] == "SourceA"
    )
    source_b = next(
        row
        for row in sources
        if row["model_alias"] == "model_a" and row["source"] == "SourceB"
    )
    assert int(source_a["pairs"]) == 2
    assert float(source_a["mean_strategy_count"]) == pytest.approx(1.5)
    assert int(source_b["pairs"]) == 1
    assert float(source_b["mean_strategy_count"]) == pytest.approx(2.0)

    prevalence = csv_rows(reports / "strategy_prevalence_overall.csv")
    model_a_syn = next(
        row
        for row in prevalence
        if row["model_alias"] == "model_a" and row["strategy_code"] == "SYN"
    )
    assert float(model_a_syn["predicted_pct"]) == pytest.approx(200 / 3)

    agreement = csv_rows(reports / "model_agreement_overall.csv")[0]
    assert float(agreement["exact_set_match_pct"]) == pytest.approx(100 / 3)
    assert float(agreement["mean_jaccard"]) == pytest.approx(0.5)
    report = (reports / "full_analysis.md").read_text(encoding="utf-8")
    assert "Pairs with exactly one detected strategy" in report
    assert "| en | 2 | 1 | 2 |" in report
    assert "| **Total** | **3** | **1** | **3** |" in report
    assert "by source within language" in report
    assert "SourceA" in report


def test_full_analysis_rejects_prediction_id_mismatch(tmp_path: Path) -> None:
    config_path, experiment_root = fixture(tmp_path)
    path = (
        experiment_root
        / "models"
        / "model_b"
        / "predictions"
        / "en"
        / "feats_consolidated.jsonl"
    )
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["id"] = "wrong"
    rows[0]["canonical_pair_id"] = "wrong"
    write_jsonl(path, rows)
    with pytest.raises(ValueError, match="ID mismatch"):
        analyze(config_path)
