#!/usr/bin/env python3
"""Build a deterministic release ZIP from a validated Phase 3b full run."""

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
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_ROOT = (
    PROJECT_ROOT
    / "phase3b_word_alignment"
    / "runs"
    / "2026-08-23_simalign_xlmr_large_itermax_full_v2"
)
MANIFEST_FIELDS = (
    "phase",
    "run_id",
    "language",
    "tokenizer_id",
    "archive_path",
    "pairs",
    "aligned_pairs",
    "skipped_model_length",
    "alignment_links",
    "bytes",
    "sha256",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def parse_date(value: str) -> tuple[int, int, int, int, int, int]:
    parsed = date.fromisoformat(value)
    if parsed.year < 1980:
        raise ValueError("ZIP dates must be 1980 or later")
    return parsed.year, parsed.month, parsed.day, 0, 0, 0


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def validated_rows(run_root: Path) -> tuple[str, list[dict[str, Any]]]:
    language_roots = sorted(path for path in run_root.iterdir() if path.is_dir())
    if not language_roots:
        raise RuntimeError("Phase 3b run has no language outputs")
    rows: list[dict[str, Any]] = []
    run_ids: set[str] = set()
    for language_root in language_roots:
        language = language_root.name
        run_config = load_json(language_root / "run_config.json")
        summary = load_json(language_root / "reports" / "summary.json")
        validation = load_json(language_root / "reports" / "validation.json")
        if run_config.get("status") != "complete":
            raise RuntimeError(f"Language {language} is not complete")
        if validation.get("valid") is not True:
            raise RuntimeError(f"Language {language} did not pass validation")
        expected = int(validation.get("expected_pairs", -1))
        observed = int(validation.get("observed_pairs", -1))
        if expected != observed or int(summary.get("processed_pairs", -1)) != observed:
            raise RuntimeError(f"Language {language} validation count is inconsistent")
        source = language_root / "alignments" / "feats_word_alignments.jsonl"
        if not source.is_file():
            raise FileNotFoundError(source)
        if line_count(source) != observed:
            raise RuntimeError(f"Alignment count changed after validation: {source}")
        digest = sha256(source)
        if digest != summary.get("output_sha256"):
            raise RuntimeError(f"Alignment changed after validation: {source}")
        status_counts = validation["status_counts"]
        if sum(int(value) for value in status_counts.values()) != observed:
            raise RuntimeError(f"Language {language} status counts are inconsistent")
        run_id = str(validation["run_id"])
        run_ids.add(run_id)
        rows.append(
            {
                "phase": "phase3b_word_alignment",
                "run_id": run_id,
                "language": language,
                "tokenizer_id": validation["tokenizer_id"],
                "archive_path": f"{language}/alignments/{source.name}",
                "pairs": observed,
                "aligned_pairs": int(status_counts["aligned"]),
                "skipped_model_length": int(status_counts["skipped_model_length"]),
                "alignment_links": int(summary["alignment_links"]),
                "bytes": source.stat().st_size,
                "sha256": digest,
            }
        )
    if len(run_ids) != 1:
        raise RuntimeError(f"Phase 3b language outputs have different run IDs: {run_ids}")
    return next(iter(run_ids)), rows


def support_members(run_root: Path, languages: list[str]) -> list[tuple[Path, str]]:
    members: list[tuple[Path, str]] = []
    for language in languages:
        language_root = run_root / language
        relative_paths = (
            "input_manifest.json",
            "run_config.json",
            "reports/summary.json",
            "reports/validation.json",
        )
        for relative in relative_paths:
            source = language_root / relative
            if not source.is_file():
                raise FileNotFoundError(source)
            members.append((source, f"{language}/{relative}"))
    return members


def write_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def copy_member(
    archive: zipfile.ZipFile,
    source: Path,
    archive_path: str,
    timestamp: tuple[int, ...],
) -> None:
    info = zipfile.ZipInfo(archive_path, date_time=timestamp)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    with source.open("rb") as input_handle, archive.open(
        info, "w", force_zip64=True
    ) as output_handle:
        shutil.copyfileobj(input_handle, output_handle, length=1024 * 1024)


def write_zip(
    path: Path,
    run_root: Path,
    rows: list[dict[str, Any]],
    support: list[tuple[Path, str]],
    manifest_path: Path,
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
        copy_member(archive, manifest_path, "PHASE3B_MANIFEST.csv", timestamp)
        for source, archive_path in support:
            copy_member(archive, source, archive_path, timestamp)
        for row in rows:
            source = run_root / row["archive_path"]
            copy_member(archive, source, row["archive_path"], timestamp)
    temporary.replace(path)


def package(
    run_root: Path,
    output_dir: Path,
    version: str,
    archive_date: str,
) -> dict[str, Any]:
    run_id, rows = validated_rows(run_root)
    languages = [str(row["language"]) for row in rows]
    support = support_members(run_root, languages)
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"feats-phase3b-word-alignment-{version}.zip"
    with tempfile.TemporaryDirectory(
        prefix="feats-phase3b-package-", dir=output_dir
    ) as temp_dir:
        temporary = Path(temp_dir)
        manifest_path = temporary / "PHASE3B_MANIFEST.csv"
        temporary_zip = temporary / zip_path.name
        write_manifest(manifest_path, rows)
        write_zip(
            temporary_zip,
            run_root,
            rows,
            support,
            manifest_path,
            parse_date(archive_date),
        )
        temporary_zip.replace(zip_path)
    return {
        "run_id": run_id,
        "languages": languages,
        "alignment_files": len(rows),
        "pairs": sum(int(row["pairs"]) for row in rows),
        "aligned_pairs": sum(int(row["aligned_pairs"]) for row in rows),
        "skipped_model_length": sum(
            int(row["skipped_model_length"]) for row in rows
        ),
        "alignment_links": sum(int(row["alignment_links"]) for row in rows),
        "zip": str(zip_path),
        "zip_bytes": zip_path.stat().st_size,
        "zip_sha256": sha256(zip_path),
        "embedded_manifest": "PHASE3B_MANIFEST.csv",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--archive-date", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            package(
                args.run_root.resolve(),
                args.output_dir.resolve(),
                args.version,
                args.archive_date,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
