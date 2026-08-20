#!/usr/bin/env python3
"""Build a deterministic release ZIP from validated Phase 2b data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import date
from pathlib import Path

from consolidate_cleaned import DEFAULT_OUTPUT, DEFAULT_REPORTS


MANIFEST_FIELDS = (
    "phase",
    "language",
    "filename",
    "archive_path",
    "consolidated_pairs",
    "cleaned_observations",
    "bytes",
    "sha256",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_date(value: str) -> tuple[int, int, int, int, int, int]:
    parsed = date.fromisoformat(value)
    if parsed.year < 1980:
        raise ValueError("ZIP dates must be 1980 or later")
    return parsed.year, parsed.month, parsed.day, 0, 0, 0


def validated_rows(data_root: Path, validation_path: Path) -> tuple[dict, list[dict]]:
    if not validation_path.is_file():
        raise FileNotFoundError(f"Missing validation report: {validation_path}")
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    if validation.get("valid") is not True:
        raise RuntimeError("Refusing to package Phase 2b data that did not pass validation")
    validated = validation.get("files", [])
    if len(validated) != int(validation.get("output_files", -1)):
        raise RuntimeError("Validation report does not cover every Phase 2b file")

    rows = []
    expected_paths = set()
    for item in validated:
        relative = Path(item["language"]) / item["file"]
        expected_paths.add(relative.as_posix())
        path = data_root / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        digest = sha256(path)
        if digest != item["sha256"] or path.stat().st_size != int(item["bytes"]):
            raise RuntimeError(f"Consolidated file changed after validation: {relative}")
        rows.append(
            {
                "phase": "phase2b_consolidation",
                "language": item["language"],
                "filename": item["file"],
                "archive_path": f"data/{relative.as_posix()}",
                "consolidated_pairs": int(item["consolidated_pairs"]),
                "cleaned_observations": int(item["cleaned_observations"]),
                "bytes": int(item["bytes"]),
                "sha256": digest,
            }
        )

    observed_paths = {
        path.relative_to(data_root).as_posix()
        for path in data_root.glob("*/*.jsonl")
        if path.is_file()
    }
    if observed_paths != expected_paths:
        raise RuntimeError(
            "Phase 2b layout changed after validation; "
            f"missing={sorted(expected_paths-observed_paths)}, "
            f"extra={sorted(observed_paths-expected_paths)}"
        )
    if sum(row["consolidated_pairs"] for row in rows) != int(
        validation["consolidated_pairs"]
    ):
        raise RuntimeError("Validated Phase 2b pair total is inconsistent")
    if sum(row["cleaned_observations"] for row in rows) != int(
        validation["cleaned_observations"]
    ):
        raise RuntimeError("Validated cleaned-observation total is inconsistent")
    return validation, sorted(rows, key=lambda row: row["language"])


def write_manifest(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def copy_member(archive, source: Path, archive_path: str, timestamp: tuple[int, ...]) -> None:
    info = zipfile.ZipInfo(archive_path, date_time=timestamp)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    with source.open("rb") as input_handle, archive.open(
        info, "w", force_zip64=True
    ) as output_handle:
        shutil.copyfileobj(input_handle, output_handle, length=1024 * 1024)


def write_zip(path: Path, data_root: Path, rows: list[dict],
              manifest_path: Path, timestamp: tuple[int, ...]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(
        temporary,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        allowZip64=True,
    ) as archive:
        copy_member(
            archive, manifest_path, "CONSOLIDATED_MANIFEST.csv", timestamp
        )
        for row in rows:
            relative = Path(row["archive_path"]).relative_to("data")
            copy_member(archive, data_root / relative, row["archive_path"], timestamp)
    temporary.replace(path)


def package(data_root: Path, validation_path: Path, output_dir: Path,
            version: str, archive_date: str) -> dict:
    validation, rows = validated_rows(data_root, validation_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"feats-phase2b-consolidated-{version}.zip"
    manifest_name = "CONSOLIDATED_MANIFEST.csv"
    with tempfile.TemporaryDirectory(
        prefix="feats-phase2b-package-", dir=output_dir
    ) as temp_dir:
        temporary = Path(temp_dir)
        temporary_zip = temporary / zip_path.name
        temporary_manifest = temporary / manifest_name
        write_manifest(temporary_manifest, rows)
        write_zip(
            temporary_zip, data_root, rows, temporary_manifest,
            parse_date(archive_date),
        )
        temporary_zip.replace(zip_path)
    return {
        "files": len(rows),
        "consolidated_pairs": int(validation["consolidated_pairs"]),
        "cleaned_observations": int(validation["cleaned_observations"]),
        "zip": str(zip_path),
        "zip_bytes": zip_path.stat().st_size,
        "zip_sha256": sha256(zip_path),
        "embedded_manifest": manifest_name,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--validation", type=Path, default=DEFAULT_REPORTS / "validation.json"
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--archive-date", required=True)
    args = parser.parse_args()
    print(json.dumps(
        package(
            args.data_root.resolve(),
            args.validation.resolve(),
            args.output_dir.resolve(),
            args.version,
            args.archive_date,
        ),
        indent=2,
    ))


if __name__ == "__main__":
    main()
