#!/usr/bin/env python3
"""Create and validate resumable model-homogeneous shards for mmi_en_v2_full."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, write_jsonl


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(plan: Path, output_dir: Path, shard_size: int) -> dict:
    rows = [row for row in read_jsonl(plan) if row.get("plan_status") == "ready"]
    groups = {
        "C1": [row for row in rows if row["target_axis"] in {"MEANING", "ILLOC"}],
        "C2": [row for row in rows if row["target_axis"] == "MOD"],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for config_id, values in groups.items():
        values.sort(key=lambda row: row["canonical_pair_id"])
        for index, start in enumerate(range(0, len(values), shard_size)):
            shard = values[start:start + shard_size]
            path = output_dir / f"{config_id.lower()}_{index:03d}.jsonl"
            write_jsonl(path, shard)
            manifest.append({
                "array_index": len(manifest),
                "config_id": config_id,
                "plan": str(path),
                "output": str(output_dir.parent / "generations" / f"{path.stem}.jsonl"),
                "rows": len(shard),
                "plan_sha256": sha256(path),
                "axes": dict(sorted(Counter(row["target_axis"] for row in shard).items())),
            })
    manifest_path = output_dir / "shard_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = {
        "plan": str(plan), "plan_sha256": sha256(plan), "ready_rows": len(rows),
        "shard_size": shard_size, "shards": len(manifest),
        "configs": dict(sorted(Counter(item["config_id"] for item in manifest).items())),
    }
    (output_dir / "shard_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def validate(plan: Path, output: Path) -> bool:
    expected = [row for row in read_jsonl(plan) if row.get("plan_status") == "ready"]
    if not output.exists():
        return False
    actual = read_jsonl(output)
    expected_ids = [row["canonical_pair_id"] for row in expected]
    actual_ids = [row["canonical_pair_id"] for row in actual]
    return len(actual_ids) == len(set(actual_ids)) and actual_ids == expected_ids


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("prepare")
    make.add_argument("--plan", type=Path, required=True)
    make.add_argument("--output-dir", type=Path, required=True)
    make.add_argument("--shard-size", type=int, default=2000)
    check = sub.add_parser("validate")
    check.add_argument("--plan", type=Path, required=True)
    check.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        print(json.dumps(prepare(args.plan, args.output_dir, args.shard_size), indent=2, sort_keys=True))
    elif not validate(args.plan, args.output):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
