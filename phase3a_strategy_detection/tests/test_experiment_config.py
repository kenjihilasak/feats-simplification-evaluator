import json
from pathlib import Path
import sys

import pytest


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from experiment_config import resolve_run


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_resolves_one_model_inside_shared_experiment(tmp_path):
    model_path = tmp_path / "models" / "encoder.json"
    write_json(
        model_path,
        {
            "schema": "feats-phase3-model-v1",
            "backend": "encoder_multilabel",
            "alias": "encoder",
        },
    )
    experiment_path = tmp_path / "experiment.json"
    write_json(
        experiment_path,
        {
            "schema": "feats-phase3-experiment-v2",
            "experiment_id": "three-model-pilot",
            "input_root": str(tmp_path / "input"),
            "runs_root": str(tmp_path / "runs"),
            "cache_root": str(tmp_path / "cache"),
            "models": {"encoder": str(model_path)},
            "selection": {"files": ["en/feats_consolidated.jsonl"]},
        },
    )

    resolved = resolve_run(experiment_path, model_alias="encoder")

    assert resolved.experiment_root == tmp_path / "runs" / "three-model-pilot"
    assert resolved.model_root == resolved.experiment_root / "models" / "encoder"
    assert resolved.manifest_path == resolved.experiment_root / "input_manifest.csv"
    assert resolved.model_config["backend"] == "encoder_multilabel"
    assert resolved.legacy is False


def test_shared_experiment_requires_model_alias(tmp_path):
    config = tmp_path / "experiment.json"
    write_json(
        config,
        {
            "schema": "feats-phase3-experiment-v2",
            "experiment_id": "pilot",
            "input_root": str(tmp_path),
            "runs_root": str(tmp_path),
            "cache_root": str(tmp_path),
            "models": {"encoder": "missing.json"},
            "selection": {"files": []},
        },
    )
    with pytest.raises(ValueError, match="--model-alias is required"):
        resolve_run(config)
