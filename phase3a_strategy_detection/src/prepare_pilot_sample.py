"""Build a deterministic random-plus-longest Phase 3a pilot sample."""

from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import os
import random
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_FIELDS = {
    "id", "language", "source", "corpus", "original", "simple"
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_seed(seed: int, relative_path: str) -> int:
    payload = f"{seed}:{relative_path}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def select_records(
    path: Path,
    random_count: int,
    longest_count: int,
    seed: int,
) -> tuple[list[tuple[int, dict[str, Any], str, int]], int]:
    """Reservoir-sample records and retain the longest pairs in one pass."""

    rng = random.Random(seed)
    reservoir: list[tuple[int, dict[str, Any], int]] = []
    longest: list[tuple[int, int, dict[str, Any]]] = []
    total = 0

    with path.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            record = json.loads(line)
            missing = REQUIRED_FIELDS - set(record)
            if missing:
                raise ValueError(
                    f"{path}:{index + 1} missing fields: {sorted(missing)}"
                )
            pair_length = len(str(record["original"])) + len(str(record["simple"]))
            if len(reservoir) < random_count:
                reservoir.append((index, record, pair_length))
            else:
                replacement = rng.randint(0, index)
                if replacement < random_count:
                    reservoir[replacement] = (index, record, pair_length)

            candidate = (pair_length, index, record)
            if len(longest) < longest_count:
                heapq.heappush(longest, candidate)
            elif candidate[:2] > longest[0][:2]:
                heapq.heapreplace(longest, candidate)
            total += 1

    selected: dict[int, tuple[dict[str, Any], set[str], int]] = {}
    for index, record, pair_length in reservoir:
        selected[index] = (record, {"random"}, pair_length)
    for pair_length, index, record in longest:
        if index in selected:
            selected[index][1].add("longest")
        else:
            selected[index] = (record, {"longest"}, pair_length)

    ordered = [
        (
            index,
            record,
            "+".join(sorted(reasons)),
            pair_length,
        )
        for index, (record, reasons, pair_length) in sorted(selected.items())
    ]
    return ordered, total


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def prepare(
    source_root: Path,
    output_root: Path,
    random_count: int,
    longest_count: int,
    seed: int,
) -> dict[str, Any]:
    files = sorted(source_root.glob("*/*.jsonl"))
    if not files:
        raise FileNotFoundError(f"No language-level JSONL files under {source_root}")
    if any(output_root.rglob("*.jsonl")):
        raise FileExistsError(
            f"Refusing to overwrite an existing pilot sample: {output_root}"
        )
    output_root.mkdir(parents=True, exist_ok=True)

    file_rows: list[dict[str, Any]] = []
    pair_rows: list[dict[str, Any]] = []
    for source_path in files:
        relative = source_path.relative_to(source_root)
        derived_seed = file_seed(seed, relative.as_posix())
        selected, total = select_records(
            source_path,
            random_count=random_count,
            longest_count=longest_count,
            seed=derived_seed,
        )
        output_path = output_root / relative
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = output_path.with_suffix(".jsonl.tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            for index, record, reason, pair_length in selected:
                handle.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    + "\n"
                )
                pair_rows.append(
                    {
                        "input_file": relative.as_posix(),
                        "source_row_index": index,
                        "id": record["id"],
                        "selection_reason": reason,
                        "character_count": pair_length,
                    }
                )
        os.replace(temporary, output_path)
        file_rows.append(
            {
                "input_file": relative.as_posix(),
                "total_pairs": total,
                "selected_pairs": len(selected),
                "random_target": random_count,
                "longest_target": longest_count,
                "seed": derived_seed,
                "input_sha256": sha256(source_path),
                "sample_sha256": sha256(output_path),
            }
        )

    file_manifest = output_root / "sample_files.csv"
    with file_manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(file_rows[0]))
        writer.writeheader()
        writer.writerows(file_rows)

    pair_manifest = output_root / "sample_pairs.csv"
    with pair_manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pair_rows[0]))
        writer.writeheader()
        writer.writerows(pair_rows)

    summary = {
        "schema": "feats-phase3-stratified-sample-v1",
        "source_root": str(source_root),
        "output_root": str(output_root),
        "seed": seed,
        "random_per_file": random_count,
        "longest_per_file": longest_count,
        "source_files": len(file_rows),
        "source_pairs": sum(row["total_pairs"] for row in file_rows),
        "selected_pairs": sum(row["selected_pairs"] for row in file_rows),
        "languages": sorted({Path(row["input_file"]).parent.as_posix() for row in file_rows}),
        "sample_files_sha256": sha256(file_manifest),
        "sample_pairs_sha256": sha256(pair_manifest),
    }
    atomic_json(output_root / "sample_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--random-per-file", type=int, default=25)
    parser.add_argument("--longest-per-file", type=int, default=5)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    if args.random_per_file < 1 or args.longest_per_file < 0:
        raise ValueError("Sample counts must be positive/non-negative.")
    summary = prepare(
        source_root=args.source_root.resolve(),
        output_root=args.output_root.resolve(),
        random_count=args.random_per_file,
        longest_count=args.longest_per_file,
        seed=args.seed,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
