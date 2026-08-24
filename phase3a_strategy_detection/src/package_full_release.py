#!/usr/bin/env python3
"""Build a deterministic release ZIP from a validated Phase 3a full run."""

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
    / "phase3a_strategy_detection"
    / "runs"
    / "2026-08-20_three_models_phase2b_full_v1"
)
MANIFEST_FIELDS = (
    "phase",
    "experiment_id",
    "model_alias",
    "language",
    "archive_path",
    "pairs",
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


def validated_rows(run_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    experiment = load_json(run_root / "experiment_config.json")
    experiment_id = str(experiment["experiment_id"])
    expected_pairs = int(experiment["expected_pairs"])
    model_aliases = sorted(experiment["models"])
    if not model_aliases:
        raise RuntimeError("Phase 3a experiment has no configured models")

    rows: list[dict[str, Any]] = []
    for model_alias in model_aliases:
        model_root = run_root / "models" / model_alias
        run_config = load_json(model_root / "run_config.json")
        validation = load_json(model_root / "reports" / "validation.json")
        if run_config.get("status") != "complete":
            raise RuntimeError(f"Model {model_alias} is not complete")
        if int(run_config.get("processed_pairs", -1)) != expected_pairs:
            raise RuntimeError(f"Model {model_alias} processed count is inconsistent")
        if validation.get("valid") is not True:
            raise RuntimeError(f"Model {model_alias} did not pass validation")
        if (
            int(validation.get("expected_pairs", -1)) != expected_pairs
            or int(validation.get("observed_pairs", -1)) != expected_pairs
        ):
            raise RuntimeError(f"Model {model_alias} validation count is inconsistent")

        expected_outputs: set[str] = set()
        model_pairs = 0
        for item in validation.get("files", []):
            relative = Path(str(item["output_file"]))
            expected_outputs.add(relative.as_posix())
            source = model_root / relative
            if not source.is_file():
                raise FileNotFoundError(source)
            expected = int(item["expected_pairs"])
            observed = int(item["observed_pairs"])
            actual = line_count(source)
            if expected != observed or actual != observed:
                raise RuntimeError(f"Prediction count changed after validation: {source}")
            language = Path(str(item["input_file"])).parent.as_posix()
            rows.append(
                {
                    "phase": "phase3a_strategy_detection",
                    "experiment_id": experiment_id,
                    "model_alias": model_alias,
                    "language": language,
                    "archive_path": (
                        Path("models") / model_alias / relative
                    ).as_posix(),
                    "pairs": actual,
                    "bytes": source.stat().st_size,
                    "sha256": sha256(source),
                }
            )
            model_pairs += actual
        observed_outputs = {
            path.relative_to(model_root).as_posix()
            for path in (model_root / "predictions").glob("*/*.jsonl")
            if path.is_file()
        }
        if observed_outputs != expected_outputs:
            raise RuntimeError(
                f"Prediction layout changed for {model_alias}; "
                f"missing={sorted(expected_outputs - observed_outputs)}, "
                f"extra={sorted(observed_outputs - expected_outputs)}"
            )
        if model_pairs != expected_pairs:
            raise RuntimeError(f"Model {model_alias} total differs from the experiment")
    return experiment, sorted(
        rows, key=lambda row: (row["model_alias"], row["language"])
    )


def support_members(run_root: Path, model_aliases: list[str]) -> list[tuple[Path, str]]:
    members = [
        (run_root / "experiment_config.json", "experiment_config.json"),
        (run_root / "input_manifest.csv", "input_manifest.csv"),
    ]
    reports_root = run_root / "reports"
    if reports_root.is_dir():
        for report in sorted(path for path in reports_root.iterdir() if path.is_file()):
            members.append((report, f"reports/{report.name}"))
    for model_alias in model_aliases:
        model_root = run_root / "models" / model_alias
        members.append(
            (
                model_root / "run_config.json",
                f"models/{model_alias}/run_config.json",
            )
        )
        for report in sorted((model_root / "reports").glob("*.json")):
            members.append(
                (report, f"models/{model_alias}/reports/{report.name}")
            )
    for source, _ in members:
        if not source.is_file():
            raise FileNotFoundError(source)
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
        copy_member(archive, manifest_path, "PHASE3A_MANIFEST.csv", timestamp)
        for source, archive_path in support:
            copy_member(archive, source, archive_path, timestamp)
        for row in rows:
            relative = Path(row["archive_path"])
            source = run_root / relative
            copy_member(archive, source, relative.as_posix(), timestamp)
    temporary.replace(path)


def package(
    run_root: Path,
    output_dir: Path,
    version: str,
    archive_date: str,
) -> dict[str, Any]:
    experiment, rows = validated_rows(run_root)
    model_aliases = sorted(experiment["models"])
    support = support_members(run_root, model_aliases)
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"feats-phase3a-strategy-detection-{version}.zip"
    with tempfile.TemporaryDirectory(
        prefix="feats-phase3a-package-", dir=output_dir
    ) as temp_dir:
        temporary = Path(temp_dir)
        manifest_path = temporary / "PHASE3A_MANIFEST.csv"
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
        "experiment_id": experiment["experiment_id"],
        "models": model_aliases,
        "prediction_files": len(rows),
        "predictions_per_model": int(experiment["expected_pairs"]),
        "total_predictions": sum(int(row["pairs"]) for row in rows),
        "zip": str(zip_path),
        "zip_bytes": zip_path.stat().st_size,
        "zip_sha256": sha256(zip_path),
        "embedded_manifest": "PHASE3A_MANIFEST.csv",
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
