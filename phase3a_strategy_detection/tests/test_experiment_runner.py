import json
from pathlib import Path
import sys


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import run_strategy_detection
from consolidate_shards import consolidate
from strategy_backend import BackendPrediction, LABELS
from validate_run import validate


class FakeBackend:
    alias = "fake_encoder"
    batch_size = 2
    thresholds = {label: 0.5 for label in LABELS}

    def prepare(self):
        pass

    def load(self):
        pass

    def predict_batch(self, pairs):
        return [
            BackendPrediction(scores={label: 0.6 for label in LABELS})
            for _ in pairs
        ]

    def provenance(self):
        return {
            "backend": "fake",
            "alias": self.alias,
            "thresholds": dict(self.thresholds),
            "label_order": list(LABELS),
        }

    def close(self):
        pass


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_shared_experiment_runner_batches_and_validates_canonical_ids(
    tmp_path, monkeypatch
):
    input_path = tmp_path / "input" / "en" / "feats_consolidated.jsonl"
    input_path.parent.mkdir(parents=True)
    records = []
    for index in range(3):
        pair_id = f"pair:en:{index}"
        records.append(
            {
                "id": pair_id,
                "canonical_pair_id": pair_id,
                "language": "en",
                "original": f"Original {index}",
                "simple": f"Simple {index}",
            }
        )
    input_path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )

    model_path = tmp_path / "fake_model.json"
    write_json(
        model_path,
        {
            "schema": "feats-phase3-model-v1",
            "backend": "fake",
            "alias": "fake_encoder",
        },
    )
    experiment_path = tmp_path / "experiment.json"
    write_json(
        experiment_path,
        {
            "schema": "feats-phase3-experiment-v2",
            "experiment_id": "pilot",
            "input_schema": "feats-phase2b-consolidated",
            "input_root": str(tmp_path / "input"),
            "runs_root": str(tmp_path / "runs"),
            "cache_root": str(tmp_path / "cache"),
            "models": {"fake_encoder": str(model_path)},
            "selection": {
                "files": ["en/feats_consolidated.jsonl"],
                "limit_per_file": None,
            },
        },
    )

    monkeypatch.setattr(
        run_strategy_detection, "create_backend", lambda *_args, **_kwargs: FakeBackend()
    )
    monkeypatch.setattr(run_strategy_detection, "environment_versions", lambda: {})
    monkeypatch.setattr(run_strategy_detection, "hardware_info", lambda: {})

    model_root = run_strategy_detection.run(
        experiment_path, model_alias="fake_encoder"
    )
    prediction_path = (
        model_root / "predictions" / "en" / "feats_consolidated.jsonl"
    )
    predictions = [
        json.loads(line)
        for line in prediction_path.read_text(encoding="utf-8").splitlines()
    ]
    assert len(predictions) == 3
    assert all(row["id"] == row["canonical_pair_id"] for row in predictions)

    _, report = validate(experiment_path, model_alias="fake_encoder")
    assert report["valid"] is True
    assert report["observed_pairs"] == 3

    shard_root = run_strategy_detection.run(
        experiment_path,
        model_alias="fake_encoder",
        shard_index=0,
        num_shards=2,
    )
    shard_prediction_path = (
        shard_root / "predictions" / "en" / "feats_consolidated.jsonl"
    )
    shard_predictions = [
        json.loads(line)
        for line in shard_prediction_path.read_text(encoding="utf-8").splitlines()
    ]
    assert [row["id"] for row in shard_predictions] == [
        "pair:en:0",
        "pair:en:2",
    ]

    _, shard_report = validate(
        experiment_path,
        model_alias="fake_encoder",
        shard_index=0,
        num_shards=2,
    )
    assert shard_report["valid"] is True
    assert shard_report["observed_pairs"] == 2

    resumed_root = run_strategy_detection.run(
        experiment_path,
        model_alias="fake_encoder",
        shard_index=0,
        num_shards=2,
        resume=True,
    )
    assert resumed_root == shard_root



def test_shards_consolidate_in_canonical_order(tmp_path, monkeypatch):
    input_path = tmp_path / "input" / "en" / "feats_consolidated.jsonl"
    input_path.parent.mkdir(parents=True)
    records = []
    for index in range(5):
        pair_id = f"pair:en:{index}"
        records.append(
            {
                "id": pair_id,
                "canonical_pair_id": pair_id,
                "language": "en",
                "original": f"Original {index}",
                "simple": f"Simple {index}",
            }
        )
    input_path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )
    model_path = tmp_path / "fake_model.json"
    write_json(
        model_path,
        {
            "schema": "feats-phase3-model-v1",
            "backend": "fake",
            "alias": "fake_encoder",
        },
    )
    experiment_path = tmp_path / "experiment.json"
    write_json(
        experiment_path,
        {
            "schema": "feats-phase3-experiment-v2",
            "experiment_id": "full",
            "input_schema": "feats-phase2b-consolidated",
            "input_root": str(tmp_path / "input"),
            "expected_pairs": 5,
            "runs_root": str(tmp_path / "runs"),
            "cache_root": str(tmp_path / "cache"),
            "models": {"fake_encoder": str(model_path)},
            "selection": {
                "files": ["en/feats_consolidated.jsonl"],
                "limit_per_file": None,
            },
        },
    )
    monkeypatch.setattr(
        run_strategy_detection, "create_backend", lambda *_args, **_kwargs: FakeBackend()
    )
    monkeypatch.setattr(run_strategy_detection, "environment_versions", lambda: {})
    monkeypatch.setattr(run_strategy_detection, "hardware_info", lambda: {})

    for shard_index in range(2):
        run_strategy_detection.run(
            experiment_path,
            model_alias="fake_encoder",
            shard_index=shard_index,
            num_shards=2,
        )
        _, report = validate(
            experiment_path,
            model_alias="fake_encoder",
            shard_index=shard_index,
            num_shards=2,
        )
        assert report["valid"] is True

    _, report = consolidate(
        experiment_path,
        model_alias="fake_encoder",
        num_shards=2,
    )
    assert report["processed_pairs"] == 5
    _, validation = validate(experiment_path, model_alias="fake_encoder")
    assert validation["valid"] is True
    output_path = (
        tmp_path
        / "runs"
        / "full"
        / "models"
        / "fake_encoder"
        / "predictions"
        / "en"
        / "feats_consolidated.jsonl"
    )
    outputs = [json.loads(line) for line in output_path.read_text().splitlines()]
    assert [row["id"] for row in outputs] == [record["id"] for record in records]
