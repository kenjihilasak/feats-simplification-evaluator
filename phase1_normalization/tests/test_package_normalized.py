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

from package_normalized import package


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(tmp_path):
    data_root = tmp_path / "data"
    source = data_root / "en/test__Tiny.jsonl"
    source.parent.mkdir(parents=True)
    records = [
        {
            "id": "one",
            "language": "en",
            "source": "Test",
            "corpus": "Tiny",
            "upstream_split": "train",
            "original": "Long.",
            "simple": "Short.",
        },
        {
            "id": "two",
            "language": "en",
            "source": "Test",
            "corpus": "Tiny",
            "upstream_split": None,
            "original": "Other long.",
            "simple": "Other short.",
        },
    ]
    source.write_text(
        "".join(json.dumps(row) + "\n" for row in records),
        encoding="utf-8",
    )
    report = tmp_path / "overall_validation.json"
    report.write_text(
        json.dumps({"valid": True, "jsonl_files": 1, "normalized_pairs": 2}),
        encoding="utf-8",
    )
    return data_root, report, source


def test_package_is_deterministic_and_matches_manifest(tmp_path):
    data_root, report, _ = fixture(tmp_path)
    first = package(data_root, report, tmp_path / "first", "v0.1.0-rc2", "2026-08-17")
    second = package(data_root, report, tmp_path / "second", "v0.1.0-rc2", "2026-08-17")
    assert first["zip_sha256"] == second["zip_sha256"]
    assert first["files"] == 1
    assert first["pairs"] == 2
    assert [path.name for path in (tmp_path / "first").iterdir()] == [Path(first["zip"]).name]

    with zipfile.ZipFile(first["zip"]) as archive:
        assert archive.namelist() == [
            "NORMALIZED_MANIFEST.csv",
            "data/en/test__Tiny.jsonl",
        ]
        assert archive.getinfo(archive.namelist()[0]).date_time == (
            2026,
            8,
            17,
            0,
            0,
            0,
        )
        manifest_text = archive.read("NORMALIZED_MANIFEST.csv").decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(manifest_text)))
    assert rows[0]["pairs"] == "2"
    assert rows[0]["train_pairs"] == "1"
    assert rows[0]["no_upstream_split_pairs"] == "1"


def test_package_rejects_data_changed_after_validation(tmp_path):
    data_root, report, source = fixture(tmp_path)
    source.write_text(source.read_text(encoding="utf-8") + "{}\n", encoding="utf-8")
    with pytest.raises((KeyError, RuntimeError)):
        package(data_root, report, tmp_path / "output", "v0.1.0-rc2", "2026-08-17")


def test_manifest_hash_matches_source(tmp_path):
    data_root, report, source = fixture(tmp_path)
    result = package(data_root, report, tmp_path / "output", "v0.1.0-rc2", "2026-08-17")
    with zipfile.ZipFile(result["zip"]) as archive:
        manifest_text = archive.read("NORMALIZED_MANIFEST.csv").decode("utf-8")
    row = next(csv.DictReader(io.StringIO(manifest_text)))
    assert row["sha256"] == digest(source)


def test_package_can_exclude_non_redistributable_source(tmp_path):
    data_root, report, _ = fixture(tmp_path)
    result = package(
        data_root,
        report,
        tmp_path / "output",
        "v0.1.0-rc2",
        "2026-08-18",
        {"Test"},
    )
    assert result["files"] == 0
    assert result["pairs"] == 0
    assert result["excluded_sources"] == ["Test"]
    with zipfile.ZipFile(result["zip"]) as archive:
        assert archive.namelist() == ["NORMALIZED_MANIFEST.csv"]


def test_package_rejects_unknown_excluded_source(tmp_path):
    data_root, report, _ = fixture(tmp_path)
    with pytest.raises(RuntimeError, match="unknown source"):
        package(
            data_root,
            report,
            tmp_path / "output",
            "v0.1.0-rc2",
            "2026-08-18",
            {"Missing"},
        )
