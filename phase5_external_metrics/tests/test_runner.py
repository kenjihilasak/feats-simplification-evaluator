import json
import sys
from pathlib import Path

import pytest


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import run_external_metrics
from consolidate_shards import consolidate
from metric_backend import MetricPrediction
from validate_run import validate


class FakeBackend:
    alias = "lens_salsa"
    batch_size = 2

    def prepare(self):
        pass

    def predict_batch(self, pairs):
        return [MetricPrediction(float(len(source) - len(target))) for source, target in pairs]

    def provenance(self):
        return {"backend": "fake", "revision": "test", "native_scale": True}

    def close(self):
        pass


class NanBackend(FakeBackend):
    def predict_batch(self, pairs):
        return [MetricPrediction(float("nan")) for _ in pairs]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def setup_experiment(tmp_path, count=5):
    input_path = tmp_path / "input.jsonl"
    rows = [{
        "id": f"pair:en:{index}",
        "canonical_pair_id": f"pair:en:{index}",
        "canonical_original_id": f"original:en:{index // 2}",
        "language": "en", "original": f"Original sentence {index}",
        "simple": f"Simple {index}", "sources": ["Test"],
        "corpora": [{"source": "Test", "corpus": "Fixture"}],
    } for index in range(count)]
    input_path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    model_path = tmp_path / "model.json"
    write_json(model_path, {
        "schema": "feats-phase5-external-metric-model-v1",
        "alias": "lens_salsa", "backend": "lens_salsa",
        "score_field": "lens_salsa_score", "batch_size": 2,
    })
    config_path = tmp_path / "experiment.json"
    write_json(config_path, {
        "schema": "feats-phase5-external-metrics-experiment-v1",
        "experiment_id": "test", "input_file": str(input_path),
        "expected_pairs": count, "runs_root": str(tmp_path / "runs"),
        "cache_root": str(tmp_path / "cache"),
        "metrics": {"lens_salsa": str(model_path)},
    })
    return config_path, input_path, rows


def patch_backend(monkeypatch, backend=None):
    value = backend or FakeBackend()
    monkeypatch.setattr(run_external_metrics, "create_backend", lambda *_args: value)
    monkeypatch.setattr(run_external_metrics, "environment_info", lambda *_args: {})


def test_runner_batches_writes_native_score_and_validates(tmp_path, monkeypatch):
    config, _, rows = setup_experiment(tmp_path, 3)
    patch_backend(monkeypatch)
    root = run_external_metrics.run(config, "lens_salsa")
    output = [json.loads(line) for line in (root / "predictions.jsonl").read_text().splitlines()]
    assert [row["canonical_pair_id"] for row in output] == [row["canonical_pair_id"] for row in rows]
    assert all(row["score"] == row["lens_salsa_score"] for row in output)
    assert all("original_sha256" in row and "simple_sha256" in row for row in output)
    _, report = validate(config, "lens_salsa")
    assert report == {**report, "valid": True, "observed_pairs": 3}
    assert run_external_metrics.run(config, "lens_salsa", resume=True) == root
    with pytest.raises(FileExistsError):
        run_external_metrics.run(config, "lens_salsa")


def test_shards_consolidate_in_original_order(tmp_path, monkeypatch):
    config, _, rows = setup_experiment(tmp_path, 7)
    patch_backend(monkeypatch)
    for index in range(3):
        run_external_metrics.run(config, "lens_salsa", index, 3)
        validate(config, "lens_salsa", index, 3)
    output_path = consolidate(config, "lens_salsa", 3)
    output = [json.loads(line) for line in output_path.read_text().splitlines()]
    assert [row["canonical_pair_id"] for row in output] == [row["canonical_pair_id"] for row in rows]
    assert all("shard_index" not in row for row in output)
    _, report = validate(config, "lens_salsa")
    assert report["observed_pairs"] == 7


def test_resume_rejects_non_prefix_partial(tmp_path, monkeypatch):
    config, _, _ = setup_experiment(tmp_path, 2)
    patch_backend(monkeypatch)
    partial = tmp_path / "runs/test/metrics/lens_salsa/predictions.jsonl.partial"
    partial.parent.mkdir(parents=True)
    partial.write_text(json.dumps({"canonical_pair_id": "wrong"}) + "\n")
    with pytest.raises(ValueError, match="canonical prefix"):
        run_external_metrics.run(config, "lens_salsa", resume=True)


def test_non_finite_scores_fail(tmp_path, monkeypatch):
    config, _, _ = setup_experiment(tmp_path, 1)
    patch_backend(monkeypatch, NanBackend())
    with pytest.raises(ValueError, match="Non-finite"):
        run_external_metrics.run(config, "lens_salsa")


def test_duplicate_and_non_english_inputs_fail(tmp_path, monkeypatch):
    config, input_path, rows = setup_experiment(tmp_path, 2)
    patch_backend(monkeypatch)
    input_path.write_text(json.dumps(rows[0]) + "\n" + json.dumps(rows[0]) + "\n")
    with pytest.raises(ValueError, match="Duplicate"):
        run_external_metrics.run(config, "lens_salsa")
    rows[0]["language"] = "es"
    input_path.write_text(json.dumps(rows[0]) + "\n")
    with pytest.raises(ValueError, match="English only"):
        run_external_metrics.run(config, "lens_salsa")

