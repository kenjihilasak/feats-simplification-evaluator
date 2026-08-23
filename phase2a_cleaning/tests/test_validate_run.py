import csv
import json
from pathlib import Path
import sys

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from validate_run import validate


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, separators=(",", ":")) + "\n" for record in records),
        encoding="utf-8",
    )


def fixture(tmp_path):
    input_root = tmp_path / "input"
    runs_root = tmp_path / "runs"
    config = {
        "run_id": "test_run",
        "input_root": str(input_root),
        "runs_root": str(runs_root),
        "limit_per_file": None,
        "filters": {"smp_threshold": 0.1, "labse_min": 0.62, "labse_max": 0.95},
    }
    source = [
        {"id": "keep", "language": "en", "source": "Test", "corpus": "Tiny", "original": "Long text.", "simple": "Short text."},
        {"id": "remove", "language": "en", "source": "Test", "corpus": "Tiny", "original": "Other text.", "simple": "Unrelated."},
    ]
    complexity = [
        {
            "id": row["id"],
            "original": {"predicted_label": "complex", "smp_max_mean_uncertainty": 0.01},
            "simple": {"predicted_label": "simple", "smp_max_mean_uncertainty": 0.01},
        }
        for row in source
    ]
    labse = [
        {"id": "keep", "labse_similarity": 0.8},
        {"id": "remove", "labse_similarity": 0.5},
    ]
    decisions = [
        {"id": "keep", "keep": True, "rejection_reasons": [], "labse_similarity": 0.8, "complexity": complexity[0]},
        {"id": "remove", "keep": False, "rejection_reasons": ["labse_below_min"], "labse_similarity": 0.5, "complexity": complexity[1]},
    ]
    run = runs_root / "test_run"
    filename = "test__Tiny.jsonl"
    write_jsonl(input_root / "en" / filename, source)
    write_jsonl(run / "scores/complexity/en" / filename, complexity)
    write_jsonl(run / "scores/labse/en" / filename, labse)
    write_jsonl(run / "decisions/en" / filename, decisions)
    write_jsonl(run / "cleaned/en" / filename, source[:1])
    report = run / "reports/cleaning_summary.csv"
    report.parent.mkdir(parents=True)
    fields = [
        "language", "source", "corpus", "file", "total_pairs", "kept_pairs",
        "removed_pairs", "removed_pct", "complexity_inversion",
        "complexity_inversion_pct", "labse_below_min", "labse_below_min_pct",
        "labse_above_max", "labse_above_max_pct",
    ]
    with report.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow({
            "language": "en", "source": "Test", "corpus": "Tiny", "file": filename,
            "total_pairs": 2, "kept_pairs": 1, "removed_pairs": 1, "removed_pct": 50.0,
            "complexity_inversion": 0, "complexity_inversion_pct": 0.0,
            "labse_below_min": 1, "labse_below_min_pct": 50.0,
            "labse_above_max": 0, "labse_above_max_pct": 0.0,
        })
    (run / "run_config.json").write_text(json.dumps(config), encoding="utf-8")
    return config, run / "decisions/en" / filename, decisions


def test_validate_accepts_consistent_run(tmp_path):
    config, _, _ = fixture(tmp_path)
    result = validate(config)
    assert result["valid"] is True
    assert result["totals"]["total_pairs"] == 2
    assert result["totals"]["kept_pairs"] == 1


def test_validate_rejects_changed_decision(tmp_path):
    config, path, decisions = fixture(tmp_path)
    decisions[1]["rejection_reasons"] = []
    write_jsonl(path, decisions)
    result = validate(config)
    assert result["valid"] is False
    assert any("Incorrect rejection reasons" in error for error in result["errors"])
