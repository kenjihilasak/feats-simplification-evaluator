"""Run one model-agnostic Phase 3 strategy-detection configuration."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from model_registry import create_backend
from strategy_backend import materialize_prediction


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_INPUT_FIELDS = {
    "id", "language", "source", "corpus", "original", "simple"
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def read_jsonl(path: Path, limit: int | None = None) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if limit is not None and index >= limit:
                break
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON at {path}:{index + 1}: {error}"
                ) from error
            missing = REQUIRED_INPUT_FIELDS - set(record)
            if missing:
                raise ValueError(
                    f"{path}:{index + 1} missing fields: {sorted(missing)}"
                )
            yield record


def line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def environment_versions() -> dict[str, Any]:
    packages = (
        "torch", "transformers", "peft", "bitsandbytes", "accelerate",
        "huggingface-hub", "PyYAML", "safetensors",
    )
    versions: dict[str, str] = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not-installed"
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": versions,
    }


def build_manifest(
    input_root: Path,
    relative_files: list[str],
    limit_per_file: int | None,
    run_root: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relative in relative_files:
        input_path = input_root / relative
        if not input_path.is_file():
            raise FileNotFoundError(f"Phase 3 input does not exist: {input_path}")
        total = line_count(input_path)
        selected = total if limit_per_file is None else min(total, limit_per_file)
        relative_path = Path(relative)
        output_relative = Path("predictions") / relative_path
        rows.append(
            {
                "input_file": relative_path.as_posix(),
                "output_file": output_relative.as_posix(),
                "language": relative_path.parent.as_posix(),
                "total_pairs": total,
                "selected_pairs": selected,
                "input_sha256": sha256(input_path),
            }
        )

    manifest_path = run_root / "input_manifest.csv"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = manifest_path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, manifest_path)
    return rows


def run(config_path: Path) -> Path:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    input_root = resolve_project_path(config["input_root"])
    runs_root = resolve_project_path(config["runs_root"])
    cache_root = resolve_project_path(config["cache_root"])
    run_root = runs_root / config["run_id"]
    reports_root = run_root / "reports"
    reports_root.mkdir(parents=True, exist_ok=True)

    selection = config["selection"]
    limit = selection.get("limit_per_file")
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise ValueError(
            "selection.limit_per_file must be null or a positive integer."
        )
    relative_files = [str(value) for value in selection["files"]]
    if not relative_files:
        raise ValueError("selection.files cannot be empty.")

    manifest = build_manifest(input_root, relative_files, limit, run_root)
    backend = create_backend(config["model"], cache_root=cache_root)
    backend.prepare()

    started = datetime.now(timezone.utc)
    resolved_config = {
        "schema": "feats-phase3-run-v1",
        "status": "running",
        "started_at": started.isoformat(),
        "requested_config": config,
        "requested_config_sha256": sha256(config_path),
        "input_manifest_sha256": sha256(run_root / "input_manifest.csv"),
        "model": dict(backend.provenance()),
        "environment": environment_versions(),
    }
    atomic_json(run_root / "run_config.json", resolved_config)

    processed = 0
    output_rows: list[dict[str, Any]] = []
    wall_start = time.monotonic()
    try:
        backend.load()
        for manifest_row in manifest:
            input_path = input_root / manifest_row["input_file"]
            output_path = run_root / manifest_row["output_file"]
            if output_path.exists():
                raise FileExistsError(
                    "Refusing to overwrite an existing Phase 3 prediction: "
                    f"{output_path}"
                )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = output_path.with_suffix(output_path.suffix + ".tmp")
            file_start = time.monotonic()
            file_count = 0
            with temporary.open("w", encoding="utf-8") as output_handle:
                for record in read_jsonl(input_path, limit=limit):
                    print(
                        f"Predicting {record['id']} with {backend.alias}",
                        flush=True,
                    )
                    prediction = backend.predict_pair(
                        str(record["original"]), str(record["simple"])
                    )
                    result = materialize_prediction(
                        pair_id=str(record["id"]),
                        model_alias=backend.alias,
                        prediction=prediction,
                        thresholds=backend.thresholds,
                    )
                    output_handle.write(
                        json.dumps(
                            result,
                            ensure_ascii=False,
                            separators=(",", ":"),
                        )
                        + "\n"
                    )
                    file_count += 1
                    processed += 1
            os.replace(temporary, output_path)
            output_rows.append(
                {
                    "input_file": manifest_row["input_file"],
                    "output_file": manifest_row["output_file"],
                    "pairs": file_count,
                    "seconds": time.monotonic() - file_start,
                    "output_sha256": sha256(output_path),
                }
            )
    finally:
        backend.close()

    elapsed = time.monotonic() - wall_start
    completed = datetime.now(timezone.utc)
    resolved_config.update(
        {
            "status": "complete",
            "completed_at": completed.isoformat(),
            "elapsed_seconds": elapsed,
            "processed_pairs": processed,
            "outputs": output_rows,
        }
    )
    atomic_json(run_root / "run_config.json", resolved_config)
    atomic_json(
        reports_root / "smoke_summary.json",
        {
            "run_id": config["run_id"],
            "processed_pairs": processed,
            "binary_decisions": processed * 6,
            "elapsed_seconds": elapsed,
            "seconds_per_pair": elapsed / processed if processed else None,
            "outputs": output_rows,
        },
    )
    return run_root


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    run_root = run(args.config.resolve())
    print(f"Completed Phase 3 run: {run_root}", flush=True)


if __name__ == "__main__":
    main()
