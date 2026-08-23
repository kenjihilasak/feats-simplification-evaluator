"""Build deterministic release assets from a validated Phase 2a run."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import tempfile
import zipfile
from datetime import date
from pathlib import Path

from common import sha256


MANIFEST_FIELDS = (
    "phase",
    "language",
    "source",
    "corpus",
    "filename",
    "archive_path",
    "pairs",
    "bytes",
    "sha256",
)


def parse_date(value: str) -> tuple[int, int, int, int, int, int]:
    parsed = date.fromisoformat(value)
    if parsed.year < 1980:
        raise ValueError("ZIP dates must be 1980 or later")
    return parsed.year, parsed.month, parsed.day, 0, 0, 0


def validated_files(run_root: Path) -> tuple[dict, list[dict]]:
    validation_path = run_root / "reports/validation.json"
    if not validation_path.is_file():
        raise FileNotFoundError(f"Missing validation report: {validation_path}")
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    if validation.get("valid") is not True:
        raise RuntimeError("Refusing to package a run that did not pass validation")
    if validation.get("run_id") != run_root.name:
        raise RuntimeError("Validation run_id does not match the selected run directory")
    rows = validation.get("files", [])
    if len(rows) != int(validation.get("files_expected", -1)):
        raise RuntimeError("Validation report does not cover every expected corpus file")
    return validation, rows


def manifest_rows(
    run_root: Path,
    validated: list[dict],
    excluded_sources: set[str] | None = None,
) -> list[dict]:
    rows = []
    expected_paths = set()
    excluded = excluded_sources or set()
    observed_sources = {str(item["source"]) for item in validated}
    unknown = excluded - observed_sources
    if unknown:
        raise RuntimeError(f"Cannot exclude unknown source(s): {sorted(unknown)}")
    for item in validated:
        relative = Path(item["language"]) / item["file"]
        path = run_root / "cleaned" / relative
        expected_paths.add(relative.as_posix())
        if not path.is_file():
            raise FileNotFoundError(path)
        digest = sha256(path)
        if digest != item["cleaned_sha256"]:
            raise RuntimeError(f"Cleaned file changed after validation: {relative}")
        if item["source"] in excluded:
            continue
        rows.append(
            {
                "phase": "phase2a_cleaning",
                "language": item["language"],
                "source": item["source"],
                "corpus": item["corpus"],
                "filename": item["file"],
                "archive_path": f"cleaned/{relative.as_posix()}",
                "pairs": int(item["kept_pairs"]),
                "bytes": path.stat().st_size,
                "sha256": digest,
            }
        )

    observed_paths = {
        path.relative_to(run_root / "cleaned").as_posix()
        for path in (run_root / "cleaned").glob("*/*.jsonl")
        if path.is_file()
    }
    if observed_paths != expected_paths:
        raise RuntimeError(
            f"Cleaned layout changed after validation; "
            f"missing={sorted(expected_paths - observed_paths)}, "
            f"extra={sorted(observed_paths - expected_paths)}"
        )
    return sorted(rows, key=lambda row: (row["language"], row["filename"]))


def write_manifest(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_zip(
    path: Path,
    run_root: Path,
    rows: list[dict],
    manifest_path: Path,
    timestamp: tuple[int, ...],
) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as archive:
        manifest_info = zipfile.ZipInfo("CLEANED_MANIFEST.csv", date_time=timestamp)
        manifest_info.compress_type = zipfile.ZIP_DEFLATED
        manifest_info.create_system = 3
        manifest_info.external_attr = 0o100644 << 16
        with manifest_path.open("rb") as input_handle, archive.open(
            manifest_info, "w"
        ) as output_handle:
            shutil.copyfileobj(input_handle, output_handle, length=1024 * 1024)
        for row in rows:
            source = run_root / row["archive_path"]
            info = zipfile.ZipInfo(row["archive_path"], date_time=timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            with source.open("rb") as input_handle, archive.open(info, "w", force_zip64=True) as output_handle:
                shutil.copyfileobj(input_handle, output_handle, length=1024 * 1024)
    temporary.replace(path)


def package(
    run_root: Path,
    output_dir: Path,
    version: str,
    archive_date: str,
    excluded_sources: set[str] | None = None,
) -> dict:
    validation, validated = validated_files(run_root)
    excluded = excluded_sources or set()
    rows = manifest_rows(run_root, validated, excluded)
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"feats-phase2-cleaned-{version}.zip"
    manifest_name = "CLEANED_MANIFEST.csv"

    with tempfile.TemporaryDirectory(prefix="feats-phase2-package-", dir=output_dir) as temp_dir:
        temporary = Path(temp_dir)
        temporary_zip = temporary / zip_path.name
        temporary_manifest = temporary / manifest_name
        write_manifest(temporary_manifest, rows)
        write_zip(temporary_zip, run_root, rows, temporary_manifest, parse_date(archive_date))
        temporary_zip.replace(zip_path)

    return {
        "run_id": validation["run_id"],
        "files": len(rows),
        "pairs": sum(row["pairs"] for row in rows),
        "zip": str(zip_path),
        "zip_bytes": zip_path.stat().st_size,
        "zip_sha256": sha256(zip_path),
        "embedded_manifest": manifest_name,
        "excluded_sources": sorted(excluded),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--archive-date", required=True, help="Fixed YYYY-MM-DD timestamp for reproducible ZIP members")
    parser.add_argument(
        "--exclude-source",
        action="append",
        default=[],
        help="Exact source name to omit from the release package; repeat as needed",
    )
    args = parser.parse_args()
    result = package(
        args.run_root.resolve(),
        args.output_dir.resolve(),
        args.version,
        args.archive_date,
        set(args.exclude_source),
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
