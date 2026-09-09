"""Build deterministic 32-case smoke and stratified English pilot inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable

from common import atomic_json, project_path, read_jsonl, sha256


def stable_id(kind: str, source_id: str, index: int) -> str:
    digest = hashlib.sha256(f"{kind}\0{source_id}\0{index}".encode()).hexdigest()
    return f"phase5-smoke:en:{digest}"


def transform(record: dict[str, Any], kind: str) -> tuple[str, str]:
    original, simple = str(record["original"]), str(record["simple"])
    if kind == "valid_simplification":
        return original, simple
    if kind == "identity":
        return original, original
    if kind == "strong_omission":
        words = simple.split()
        return original, " ".join(words[:max(1, min(5, len(words) // 3))])
    if kind == "contradiction":
        return original, f"It is not true that {simple[0].lower() + simple[1:] if simple else simple}"
    if kind == "long_input":
        return " ".join([original] * 12), " ".join([simple] * 12)
    raise ValueError(kind)


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def build_smoke(input_path: Path, output_path: Path) -> dict[str, Any]:
    bases = list(read_jsonl(input_path))[:32]
    if len(bases) < 32:
        raise ValueError("Smoke construction requires at least 32 canonical pairs.")
    kinds = (
        ["valid_simplification"] * 7
        + ["identity"] * 7
        + ["strong_omission"] * 6
        + ["contradiction"] * 6
        + ["long_input"] * 6
    )
    output = []
    for index, (base, kind) in enumerate(zip(bases, kinds)):
        original, simple = transform(base, kind)
        pair_id = stable_id(kind, str(base["canonical_pair_id"]), index)
        output.append({
            "id": pair_id,
            "canonical_pair_id": pair_id,
            "canonical_original_id": base.get("canonical_original_id"),
            "language": "en",
            "original": original,
            "simple": simple,
            "smoke_case_type": kind,
            "derived_from_canonical_pair_id": base["canonical_pair_id"],
            "sources": base.get("sources", []),
            "corpora": base.get("corpora", []),
        })
    count = write_jsonl(output_path, output)
    report = {"schema": "feats-phase5-smoke-input-v1", "pairs": count, "output_sha256": sha256(output_path)}
    atomic_json(output_path.with_suffix(".summary.json"), report)
    return report


def load_decisions(root: Path) -> dict[str, dict[str, Any]]:
    result = {}
    for path in sorted(root.glob("en/**/*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                result[str(row["id"])] = row
    return result


def load_strategies(path: Path) -> dict[str, str]:
    result = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            result[str(row["canonical_pair_id"])] = "+".join(row.get("predicted_codes", [])) or "NONE"
    return result


def bin_length(record: dict[str, Any]) -> str:
    length = max(len(str(record["original"]).split()), len(str(record["simple"]).split()))
    return "short" if length < 20 else "medium" if length < 40 else "long"


def bin_labse(value: float | None) -> str:
    if value is None:
        return "missing"
    if value < 0.75:
        return "low"
    if value < 0.85:
        return "medium"
    return "high"


def primary_corpus(record: dict[str, Any]) -> str:
    corpora = record.get("corpora", [])
    if not corpora:
        return "unknown"
    first = corpora[0]
    return f"{first.get('source', 'unknown')}::{first.get('corpus', 'unknown')}"


def build_pilot(
    input_path: Path,
    output_path: Path,
    target: int,
    seed: int,
    decisions_root: Path,
    strategies_path: Path,
) -> dict[str, Any]:
    decisions = load_decisions(decisions_root)
    strategies = load_strategies(strategies_path)
    strata: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for record in read_jsonl(input_path):
        occurrence_ids = [str(item.get("id")) for item in record.get("provenance", [])]
        decision_rows = [decisions[value] for value in occurrence_ids if value in decisions]
        values = [float(row["labse_similarity"]) for row in decision_rows if row.get("labse_similarity") is not None]
        labse = sum(values) / len(values) if values else None
        strategy = strategies.get(str(record["canonical_pair_id"]), "missing")
        key = (primary_corpus(record), bin_length(record), bin_labse(labse), strategy)
        enriched = dict(record)
        enriched["pilot_stratum"] = {
            "primary_corpus": key[0], "length_bin": key[1],
            "labse_bin": key[2], "strategy": key[3], "mean_labse": labse,
        }
        strata[key].append(enriched)
    queues = {}
    for key, values in strata.items():
        values.sort(key=lambda row: hashlib.sha256(f"{seed}\0{row['canonical_pair_id']}".encode()).hexdigest())
        queues[key] = deque(values)
    selected = []
    active = sorted(queues)
    while active and len(selected) < target:
        next_active = []
        for key in active:
            if queues[key] and len(selected) < target:
                selected.append(queues[key].popleft())
            if queues[key]:
                next_active.append(key)
        active = next_active
    selected.sort(key=lambda row: str(row["canonical_pair_id"]))
    count = write_jsonl(output_path, selected)
    report = {
        "schema": "feats-phase5-stratified-pilot-v1",
        "seed": seed,
        "requested_pairs": target,
        "pairs": count,
        "strata": len({(row["pilot_stratum"]["primary_corpus"], row["pilot_stratum"]["length_bin"], row["pilot_stratum"]["labse_bin"], row["pilot_stratum"]["strategy"]) for row in selected}),
        "input_sha256": sha256(input_path),
        "output_sha256": sha256(output_path),
    }
    atomic_json(output_path.with_suffix(".summary.json"), report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    smoke = sub.add_parser("smoke")
    smoke.add_argument("--input", type=Path, required=True)
    smoke.add_argument("--output", type=Path, required=True)
    pilot = sub.add_parser("pilot")
    pilot.add_argument("--input", type=Path, required=True)
    pilot.add_argument("--output", type=Path, required=True)
    pilot.add_argument("--target", type=int, default=2000)
    pilot.add_argument("--seed", type=int, default=20260908)
    pilot.add_argument("--decisions-root", type=Path, required=True)
    pilot.add_argument("--strategies", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "smoke":
        report = build_smoke(project_path(args.input), project_path(args.output))
    else:
        report = build_pilot(
            project_path(args.input), project_path(args.output), args.target, args.seed,
            project_path(args.decisions_root), project_path(args.strategies),
        )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

