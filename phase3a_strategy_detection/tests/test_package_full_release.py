from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

import pytest


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from package_full_release import package


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validated_run(tmp_path: Path) -> tuple[Path, Path]:
    run_root = tmp_path / "run"
    model = run_root / "models" / "model_a"
    prediction = model / "predictions" / "en" / "feats_consolidated.jsonl"
    prediction.parent.mkdir(parents=True)
    prediction.write_text('{"id":"pair:en:one"}\n', encoding="utf-8")
    experiment = {
        "experiment_id": "full_v1",
        "expected_pairs": 1,
        "models": {"model_a": "configs/model_a.json"},
    }
    (run_root / "experiment_config.json").write_text(
        json.dumps(experiment), encoding="utf-8"
    )
    (run_root / "input_manifest.csv").write_text("input_file\n", encoding="utf-8")
    (model / "run_config.json").write_text(
        json.dumps({"status": "complete", "processed_pairs": 1}), encoding="utf-8"
    )
    reports = model / "reports"
    reports.mkdir()
    validation = {
        "valid": True,
        "expected_pairs": 1,
        "observed_pairs": 1,
        "files": [
            {
                "input_file": "en/feats_consolidated.jsonl",
                "output_file": "predictions/en/feats_consolidated.jsonl",
                "expected_pairs": 1,
                "observed_pairs": 1,
            }
        ],
    }
    (reports / "validation.json").write_text(
        json.dumps(validation), encoding="utf-8"
    )
    (reports / "run_summary.json").write_text("{}\n", encoding="utf-8")
    return run_root, prediction


def test_package_is_deterministic_and_auditable(tmp_path: Path) -> None:
    run_root, prediction = validated_run(tmp_path)
    first = package(run_root, tmp_path / "first", "v0.2.0-rc1", "2026-08-23")
    second = package(run_root, tmp_path / "second", "v0.2.0-rc1", "2026-08-23")
    assert first["zip_sha256"] == second["zip_sha256"]
    assert first["total_predictions"] == 1
    with zipfile.ZipFile(first["zip"]) as archive:
        assert archive.namelist() == [
            "PHASE3A_MANIFEST.csv",
            "experiment_config.json",
            "input_manifest.csv",
            "models/model_a/run_config.json",
            "models/model_a/reports/run_summary.json",
            "models/model_a/reports/validation.json",
            "models/model_a/predictions/en/feats_consolidated.jsonl",
        ]
        rows = list(
            csv.DictReader(
                io.StringIO(archive.read("PHASE3A_MANIFEST.csv").decode("utf-8"))
            )
        )
    assert rows[0]["pairs"] == "1"
    assert rows[0]["sha256"] == digest(prediction)


def test_package_rejects_predictions_changed_after_validation(tmp_path: Path) -> None:
    run_root, prediction = validated_run(tmp_path)
    prediction.write_text("changed\nextra\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="changed after validation"):
        package(run_root, tmp_path / "output", "v0.2.0-rc1", "2026-08-23")
