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

from package_consolidated import package


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validated_data(tmp_path):
    data = tmp_path / "data"
    source = data / "en/feats_consolidated.jsonl"
    source.parent.mkdir(parents=True)
    source.write_text(
        '{"id":"pair:en:one","provenance":[{"id":"one"}]}\n',
        encoding="utf-8",
    )
    validation = {
        "valid": True,
        "output_files": 1,
        "consolidated_pairs": 1,
        "cleaned_observations": 1,
        "files": [{
            "language": "en",
            "file": source.name,
            "consolidated_pairs": 1,
            "cleaned_observations": 1,
            "bytes": source.stat().st_size,
            "sha256": sha256(source),
        }],
    }
    report = tmp_path / "validation.json"
    report.write_text(json.dumps(validation), encoding="utf-8")
    return data, report, source


def test_package_is_deterministic_and_auditable(tmp_path):
    data, report, source = validated_data(tmp_path)
    first = package(data, report, tmp_path / "first", "v0.1.0-rc2", "2026-08-20")
    second = package(data, report, tmp_path / "second", "v0.1.0-rc2", "2026-08-20")
    assert first["zip_sha256"] == second["zip_sha256"]
    assert first["consolidated_pairs"] == 1

    with zipfile.ZipFile(first["zip"]) as archive:
        assert archive.namelist() == [
            "CONSOLIDATED_MANIFEST.csv",
            "data/en/feats_consolidated.jsonl",
        ]
        assert archive.getinfo(archive.namelist()[0]).date_time == (
            2026, 8, 20, 0, 0, 0
        )
        rows = list(csv.DictReader(io.StringIO(
            archive.read("CONSOLIDATED_MANIFEST.csv").decode("utf-8")
        )))
    assert rows[0]["consolidated_pairs"] == "1"
    assert rows[0]["sha256"] == sha256(source)


def test_package_rejects_data_changed_after_validation(tmp_path):
    data, report, source = validated_data(tmp_path)
    source.write_text("changed\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="changed after validation"):
        package(data, report, tmp_path / "output", "v0.1.0-rc2", "2026-08-20")
