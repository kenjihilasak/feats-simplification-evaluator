"""Shared file and configuration utilities for Phase 2a."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class CorpusFile:
    language: str
    path: Path

    @property
    def filename(self) -> str:
        return self.path.name


def load_config(path: Path) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))
    config["_config_path"] = str(path.resolve())
    return config


def project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def input_files(config: dict) -> list[CorpusFile]:
    root = project_path(config["input_root"])
    patterns = config.get("include_files", ["*/*.jsonl"])
    paths: set[Path] = set()
    for pattern in patterns:
        matches = set(root.glob(pattern))
        if not matches:
            raise FileNotFoundError(f"Input pattern matched no JSONL files: {root / pattern}")
        paths.update(matches)
    files = [CorpusFile(path.parent.name, path) for path in paths]
    files.sort(key=lambda item: (item.language, item.filename))
    if not files:
        raise FileNotFoundError(f"No JSONL files under {root}/<language>/")
    return files


def run_root(config: dict) -> Path:
    return project_path(config["runs_root"]) / config["run_id"]


def output_path(config: dict, section: str, corpus_file: CorpusFile) -> Path:
    return run_root(config) / section / corpus_file.language / corpus_file.filename


def score_path(config: dict, score_type: str, corpus_file: CorpusFile) -> Path:
    """Resolve scores, optionally reusing them from an earlier versioned run."""
    score_run_id = config.get("score_source_run_id", config["run_id"])
    return (
        project_path(config["runs_root"])
        / str(score_run_id)
        / "scores"
        / score_type
        / corpus_file.language
        / corpus_file.filename
    )


def iter_jsonl(path: Path, limit: int | None = None) -> Iterator[dict]:
    with path.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if limit is not None and index >= limit:
                break
            if line.strip():
                yield json.loads(line)


def chunks(items: Iterable[dict], size: int) -> Iterator[list[dict]]:
    chunk: list[dict] = []
    for item in items:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def atomic_jsonl(path: Path, records: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    count = 0
    with temporary.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            count += 1
    temporary.replace(path)
    return count


def jsonl_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def reusable(path: Path, expected: int) -> bool:
    return path.is_file() and jsonl_count(path) == expected


def input_limit(config: dict) -> int | None:
    value = config.get("limit_per_file")
    return None if value is None else int(value)


def expected_count(corpus_file: CorpusFile, config: dict) -> int:
    limit = input_limit(config)
    count = jsonl_count(corpus_file.path)
    return min(count, limit) if limit is not None else count


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
