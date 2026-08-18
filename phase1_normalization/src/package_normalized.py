"""Build deterministic release assets from a validated Phase 1 corpus."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import tempfile
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path

from common import DATA_ROOT, REPORT_ROOT, iter_jsonl, sha256


MANIFEST_FIELDS = (
    "path",
    "language",
    "source",
    "corpus",
    "pairs",
    "bytes",
    "sha256",
    "train_pairs",
    "validation_pairs",
    "test_pairs",
    "no_upstream_split_pairs",
)


def parse_date(value: str) -> tuple[int, int, int, int, int, int]:
    parsed = date.fromisoformat(value)
    if parsed.year < 1980:
        raise ValueError("ZIP dates must be 1980 or later")
    return parsed.year, parsed.month, parsed.day, 0, 0, 0


def validated_report(report_path: Path) -> dict:
    if not report_path.is_file():
        raise FileNotFoundError(f"Missing Phase 1 validation report: {report_path}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("valid") is not True:
        raise RuntimeError("Refusing to package a Phase 1 corpus that did not pass validation")
    return report


def manifest_row(path: Path, data_root: Path) -> dict:
    counts = Counter()
    identity = None
    for record in iter_jsonl(path):
        current = (record["language"], record["source"], record["corpus"])
        if identity is None:
            identity = current
        elif current != identity:
            raise RuntimeError(f"Mixed corpus identity in {path}")
        split = record.get("upstream_split")
        counts["pairs"] += 1
        counts["no_upstream_split" if split is None else str(split)] += 1
    if identity is None:
        raise RuntimeError(f"Empty normalized file: {path}")
    relative = path.relative_to(data_root).as_posix()
    return {
        "path": relative,
        "language": identity[0],
        "source": identity[1],
        "corpus": identity[2],
        "pairs": counts["pairs"],
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "train_pairs": counts["train"],
        "validation_pairs": counts["validation"],
        "test_pairs": counts["test"],
        "no_upstream_split_pairs": counts["no_upstream_split"],
    }


def manifest_rows(data_root: Path, report: dict) -> list[dict]:
    paths = sorted(data_root.glob("*/*.jsonl"))
    rows = [manifest_row(path, data_root) for path in paths]
    if len(rows) != int(report["jsonl_files"]):
        raise RuntimeError("Normalized file count changed after validation")
    if sum(int(row["pairs"]) for row in rows) != int(report["normalized_pairs"]):
        raise RuntimeError("Normalized pair count changed after validation")
    return rows


def write_manifest(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=MANIFEST_FIELDS,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_zip(
    path: Path,
    data_root: Path,
    rows: list[dict],
    timestamp: tuple[int, ...],
) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(
        temporary,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        allowZip64=True,
    ) as archive:
        for row in rows:
            source = data_root / row["path"]
            archive_path = f"data/{row['path']}"
            info = zipfile.ZipInfo(archive_path, date_time=timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            with source.open("rb") as input_handle, archive.open(
                info,
                "w",
                force_zip64=True,
            ) as output_handle:
                shutil.copyfileobj(input_handle, output_handle, length=1024 * 1024)
    temporary.replace(path)


def package(
    data_root: Path,
    report_path: Path,
    output_dir: Path,
    version: str,
    archive_date: str,
) -> dict:
    report = validated_report(report_path)
    rows = manifest_rows(data_root, report)
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"feats-phase1-normalized-{version}.zip"
    manifest_path = output_dir / "NORMALIZED_MANIFEST.csv"
    checksum_path = output_dir / "NORMALIZED_SHA256SUMS"

    with tempfile.TemporaryDirectory(
        prefix="feats-phase1-package-",
        dir=output_dir,
    ) as temp_dir:
        temporary = Path(temp_dir)
        temporary_zip = temporary / zip_path.name
        temporary_manifest = temporary / manifest_path.name
        write_manifest(temporary_manifest, rows)
        write_zip(temporary_zip, data_root, rows, parse_date(archive_date))
        temporary_zip.replace(zip_path)
        temporary_manifest.replace(manifest_path)

    checksum_path.write_text(
        f"{sha256(zip_path)}  {zip_path.name}\n"
        f"{sha256(manifest_path)}  {manifest_path.name}\n",
        encoding="utf-8",
    )
    return {
        "files": len(rows),
        "pairs": sum(int(row["pairs"]) for row in rows),
        "zip": str(zip_path),
        "zip_bytes": zip_path.stat().st_size,
        "zip_sha256": sha256(zip_path),
        "manifest": str(manifest_path),
        "checksums": str(checksum_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument(
        "--report",
        type=Path,
        default=REPORT_ROOT / "overall_validation.json",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--archive-date",
        required=True,
        help="Fixed YYYY-MM-DD timestamp for reproducible ZIP members",
    )
    args = parser.parse_args()
    result = package(
        args.data_root.resolve(),
        args.report.resolve(),
        args.output_dir.resolve(),
        args.version,
        args.archive_date,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
