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
    language_root = run_root / "en"
    alignment = language_root / "alignments" / "feats_word_alignments.jsonl"
    alignment.parent.mkdir(parents=True)
    alignment.write_text('{"id":"pair:en:one"}\n', encoding="utf-8")
    (language_root / "input_manifest.json").write_text("{}\n", encoding="utf-8")
    (language_root / "run_config.json").write_text(
        json.dumps({"status": "complete"}), encoding="utf-8"
    )
    reports = language_root / "reports"
    reports.mkdir()
    summary = {
        "processed_pairs": 1,
        "alignment_links": 1,
        "output_sha256": digest(alignment),
    }
    validation = {
        "run_id": "full_v2",
        "language": "en",
        "tokenizer_id": "spacy:en:blank",
        "valid": True,
        "expected_pairs": 1,
        "observed_pairs": 1,
        "status_counts": {"aligned": 1, "skipped_model_length": 0},
    }
    (reports / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (reports / "validation.json").write_text(
        json.dumps(validation), encoding="utf-8"
    )
    return run_root, alignment


def test_package_is_deterministic_and_auditable(tmp_path: Path) -> None:
    run_root, alignment = validated_run(tmp_path)
    first = package(run_root, tmp_path / "first", "v0.2.0-rc1", "2026-08-23")
    second = package(run_root, tmp_path / "second", "v0.2.0-rc1", "2026-08-23")
    assert first["zip_sha256"] == second["zip_sha256"]
    assert first["pairs"] == 1
    with zipfile.ZipFile(first["zip"]) as archive:
        assert archive.namelist() == [
            "PHASE3B_MANIFEST.csv",
            "en/input_manifest.json",
            "en/run_config.json",
            "en/reports/summary.json",
            "en/reports/validation.json",
            "en/alignments/feats_word_alignments.jsonl",
        ]
        rows = list(
            csv.DictReader(
                io.StringIO(archive.read("PHASE3B_MANIFEST.csv").decode("utf-8"))
            )
        )
    assert rows[0]["pairs"] == "1"
    assert rows[0]["sha256"] == digest(alignment)


def test_package_rejects_alignment_changed_after_validation(tmp_path: Path) -> None:
    run_root, alignment = validated_run(tmp_path)
    alignment.write_text("changed\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="changed after validation"):
        package(run_root, tmp_path / "output", "v0.2.0-rc1", "2026-08-23")
