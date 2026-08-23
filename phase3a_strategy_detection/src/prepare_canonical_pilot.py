"""Build a corpus-stratified pilot from canonical Phase 2b pairs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_FIELDS = {
    "id", "canonical_pair_id", "language", "original", "simple", "corpora"
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def derived_seed(seed: int, key: tuple[str, str, str]) -> int:
    payload = f"{seed}:{key[0]}:{key[1]}:{key[2]}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


@dataclass
class StratumSampler:
    random_target: int
    longest_target: int
    rng: random.Random
    seen: int = 0
    reservoir: list[tuple[int, int, dict[str, Any]]] = field(default_factory=list)
    longest: list[tuple[int, int, dict[str, Any]]] = field(default_factory=list)

    def consider(self, index: int, record: dict[str, Any], pair_length: int) -> None:
        self.seen += 1
        candidate = (index, pair_length, record)
        if len(self.reservoir) < self.random_target:
            self.reservoir.append(candidate)
        else:
            replacement = self.rng.randrange(self.seen)
            if replacement < self.random_target:
                self.reservoir[replacement] = candidate

        longest_candidate = (pair_length, index, record)
        if self.longest_target == 0:
            return
        if len(self.longest) < self.longest_target:
            heapq.heappush(self.longest, longest_candidate)
        elif longest_candidate[:2] > self.longest[0][:2]:
            heapq.heapreplace(self.longest, longest_candidate)

    def selected(self) -> dict[str, tuple[int, dict[str, Any], set[str]]]:
        chosen: dict[str, tuple[int, dict[str, Any], set[str]]] = {}
        for index, _, record in self.reservoir:
            chosen[record["canonical_pair_id"]] = (index, record, {"random"})
        for _, index, record in self.longest:
            pair_id = record["canonical_pair_id"]
            if pair_id in chosen:
                chosen[pair_id][2].add("longest")
            else:
                chosen[pair_id] = (index, record, {"longest"})
        return chosen


def corpus_keys(record: dict[str, Any]) -> set[tuple[str, str, str]]:
    language = str(record["language"])
    keys = {
        (language, str(item["source"]), str(item["corpus"]))
        for item in record["corpora"]
    }
    if not keys:
        raise ValueError(f"Canonical pair has no corpus provenance: {record['id']}")
    return keys


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
    files = sorted(source_root.glob("*/feats_consolidated.jsonl"))
    if not files:
        raise FileNotFoundError(
            f"No Phase 2b files under {source_root}/<language>/"
        )
    if any(output_root.rglob("*.jsonl")):
        raise FileExistsError(
            f"Refusing to overwrite an existing canonical pilot: {output_root}"
        )
    output_root.mkdir(parents=True, exist_ok=True)

    samplers: dict[tuple[str, str, str], StratumSampler] = {}
    file_rows = []
    total_pairs = 0
    for source_path in files:
        language = source_path.parent.name
        file_count = 0
        with source_path.open(encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                record = json.loads(line)
                missing = REQUIRED_FIELDS - set(record)
                if missing:
                    raise ValueError(
                        f"{source_path}:{index + 1} missing fields: {sorted(missing)}"
                    )
                if record["language"] != language:
                    raise ValueError(f"Language/path mismatch: {record['id']}")
                if record["id"] != record["canonical_pair_id"]:
                    raise ValueError(f"Non-canonical Phase 2b ID: {record['id']}")
                pair_length = len(record["original"]) + len(record["simple"])
                for key in corpus_keys(record):
                    if key not in samplers:
                        samplers[key] = StratumSampler(
                            random_target=random_count,
                            longest_target=longest_count,
                            rng=random.Random(derived_seed(seed, key)),
                        )
                    samplers[key].consider(index, record, pair_length)
                file_count += 1
        total_pairs += file_count
        file_rows.append(
            {
                "input_file": source_path.relative_to(source_root).as_posix(),
                "input_pairs": file_count,
                "input_sha256": sha256(source_path),
            }
        )

    selected: dict[str, tuple[str, int, dict[str, Any], set[str]]] = {}
    stratum_rows = []
    for key in sorted(samplers):
        sampler = samplers[key]
        chosen = sampler.selected()
        language, source, corpus = key
        for pair_id, (index, record, reasons) in chosen.items():
            tags = {f"{source} / {corpus} / {reason}" for reason in reasons}
            if pair_id in selected:
                selected[pair_id][3].update(tags)
            else:
                selected[pair_id] = (language, index, record, tags)
        stratum_rows.append(
            {
                "language": language,
                "source": source,
                "corpus": corpus,
                "available_pairs": sampler.seen,
                "selected_pairs_before_cross_stratum_deduplication": len(chosen),
                "random_target": random_count,
                "longest_target": longest_count,
                "seed": derived_seed(seed, key),
            }
        )

    by_language: dict[str, list[tuple[int, dict[str, Any], set[str]]]] = {}
    for language, index, record, reasons in selected.values():
        by_language.setdefault(language, []).append((index, record, reasons))

    pair_rows = []
    for language in sorted(by_language):
        output_path = output_root / language / "feats_consolidated.jsonl"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = output_path.with_suffix(".jsonl.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            for index, record, reasons in sorted(
                by_language[language], key=lambda item: (item[0], item[1]["id"])
            ):
                handle.write(
                    json.dumps(record, ensure_ascii=False, separators=(",", ":"))
                    + "\n"
                )
                pair_rows.append(
                    {
                        "language": language,
                        "source_row_index": index,
                        "canonical_pair_id": record["canonical_pair_id"],
                        "selection_strata": json.dumps(
                            sorted(reasons), ensure_ascii=False, separators=(",", ":")
                        ),
                        "character_count": len(record["original"]) + len(record["simple"]),
                    }
                )
        os.replace(temporary, output_path)

    for filename, rows in (
        ("sample_files.csv", file_rows),
        ("sample_strata.csv", stratum_rows),
        ("sample_pairs.csv", pair_rows),
    ):
        path = output_root / filename
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    summary = {
        "schema": "feats-phase3-canonical-pilot-v1",
        "source_root": str(source_root),
        "output_root": str(output_root),
        "seed": seed,
        "random_per_language_source_corpus": random_count,
        "longest_per_language_source_corpus": longest_count,
        "source_files": len(files),
        "source_pairs": total_pairs,
        "strata": len(stratum_rows),
        "selected_canonical_pairs": len(selected),
        "languages": sorted(by_language),
    }
    atomic_json(output_root / "sample_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root",
        type=Path,
        default=PROJECT_ROOT / "phase2b_consolidation" / "data",
    )
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--random-per-stratum", type=int, default=25)
    parser.add_argument("--longest-per-stratum", type=int, default=5)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    if args.random_per_stratum < 1 or args.longest_per_stratum < 0:
        raise ValueError("Sample counts must be positive/non-negative.")
    result = prepare(
        args.source_root.resolve(),
        args.output_root.resolve(),
        args.random_per_stratum,
        args.longest_per_stratum,
        args.seed,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
