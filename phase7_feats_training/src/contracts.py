"""Contracts and shared utilities for Phase 7 axis-model experiments."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable, Iterator


AXES = ("MEANING", "MOD", "ILLOC")
LABEL_SOURCES = ("weak", "synthetic", "human")
DATASET_SCHEMA = "feats-phase7-axis-example-v1"


@dataclass(frozen=True)
class AxisExample:
    example_id: str
    canonical_pair_id: str
    canonical_original_id: str
    language: str
    original: str
    candidate_simplification: str
    audience: str | None
    axis: str
    target_score: float
    target_scale: str
    label_source: str
    distortion_type: str | None
    split: str
    provenance: dict[str, Any]

    def validate(self) -> None:
        if self.axis not in AXES:
            raise ValueError(f"Unsupported axis: {self.axis}")
        if self.label_source not in LABEL_SOURCES:
            raise ValueError(f"Unsupported label_source: {self.label_source}")
        if not 0.0 <= self.target_score <= 1.0:
            raise ValueError("Synthetic target_score must be in [0, 1]")
        for name in ("example_id", "canonical_pair_id", "canonical_original_id", "language",
                     "original", "candidate_simplification", "target_scale", "split"):
            if not getattr(self, name):
                raise ValueError(f"Missing required field: {name}")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {"schema": DATASET_SCHEMA, **asdict(self)}


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number}: invalid JSON") from exc


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def strong_key(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return "".join(character for character in normalized if character.isalnum())


def word_set(text: str) -> set[str]:
    return set(re.findall(r"\w+", unicodedata.normalize("NFKC", text).casefold()))


def jaccard(left: str, right: str) -> float:
    a, b = word_set(left), word_set(right)
    return len(a & b) / len(a | b) if a or b else 1.0
