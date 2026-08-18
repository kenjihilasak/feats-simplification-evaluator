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

from package_cleaned import package


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validated_run(tmp_path):
    run = tmp_path / "test_run"
    cleaned = run / "cleaned/en/test__Tiny.jsonl"
    cleaned.parent.mkdir(parents=True)
    cleaned.write_text('{"id":"one","original":"Long.","simple":"Short."}\n', encoding="utf-8")
    report = {
        "valid": True,
        "run_id": "test_run",
        "files_expected": 1,
        "files": [{
            "language": "en",
            "source": "Test",
            "corpus": "Tiny",
            "file": "test__Tiny.jsonl",
            "kept_pairs": 1,
            "cleaned_sha256": sha256(cleaned),
        }],
    }
    reports = run / "reports"
    reports.mkdir()
    (reports / "validation.json").write_text(json.dumps(report), encoding="utf-8")
    return run, cleaned


def test_package_is_deterministic_and_auditable(tmp_path):
    run, _ = validated_run(tmp_path)
    first = package(run, tmp_path / "first", "v0.1.0-rc1", "2026-08-14")
    second = package(run, tmp_path / "second", "v0.1.0-rc1", "2026-08-14")
    assert first["zip_sha256"] == second["zip_sha256"]
    assert first["pairs"] == 1
    assert [path.name for path in (tmp_path / "first").iterdir()] == [Path(first["zip"]).name]

    with zipfile.ZipFile(first["zip"]) as archive:
        assert archive.namelist() == [
            "CLEANED_MANIFEST.csv",
            "cleaned/en/test__Tiny.jsonl",
        ]
        assert archive.getinfo(archive.namelist()[0]).date_time == (2026, 8, 14, 0, 0, 0)
        manifest_text = archive.read("CLEANED_MANIFEST.csv").decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(manifest_text)))
    assert rows[0]["pairs"] == "1"


def test_package_rejects_data_changed_after_validation(tmp_path):
    run, cleaned = validated_run(tmp_path)
    cleaned.write_text("changed\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="changed after validation"):
        package(run, tmp_path / "output", "v0.1.0-rc1", "2026-08-14")


def test_package_can_exclude_source(tmp_path):
    run, _ = validated_run(tmp_path)
    result = package(
        run,
        tmp_path / "output",
        "v0.1.0-rc2",
        "2026-08-18",
        {"Test"},
    )
    assert result["files"] == 0
    assert result["pairs"] == 0
    assert result["excluded_sources"] == ["Test"]
    with zipfile.ZipFile(result["zip"]) as archive:
        assert archive.namelist() == ["CLEANED_MANIFEST.csv"]


def test_package_rejects_unknown_excluded_source(tmp_path):
    run, _ = validated_run(tmp_path)
    with pytest.raises(RuntimeError, match="unknown source"):
        package(
            run,
            tmp_path / "output",
            "v0.1.0-rc2",
            "2026-08-18",
            {"Missing"},
        )
