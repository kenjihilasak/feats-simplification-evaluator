#!/usr/bin/env python3
"""Consolidate Phase 6 generation shards losslessly in manifest order."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from contracts import read_jsonl, write_jsonl


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def consolidate(manifest_rows: list[dict], shard_paths: list[Path]) -> tuple[list[dict], dict]:
    expected_ids = [row["canonical_pair_id"] for row in manifest_rows]
    if len(expected_ids) != len(set(expected_ids)):
        raise ValueError("duplicate canonical_pair_id in expected manifest")
    predictions = {}
    shard_info = []
    for path in sorted(shard_paths):
        if not path.exists():
            raise FileNotFoundError(f"missing shard: {path}")
        rows = read_jsonl(path)
        for row in rows:
            pair_id = row["canonical_pair_id"]
            if pair_id in predictions:
                raise ValueError(f"duplicate prediction across shards: {pair_id}")
            predictions[pair_id] = row
        shard_info.append({"path": str(path), "records": len(rows), "sha256": file_sha256(path)})
    unknown = set(predictions) - set(expected_ids)
    missing = set(expected_ids) - set(predictions)
    if unknown:
        raise ValueError(f"predictions not present in manifest: {sorted(unknown)[:3]}")
    if missing:
        raise ValueError(f"incomplete shards; missing {len(missing)} predictions")
    output = [predictions[pair_id] for pair_id in expected_ids]
    report = {
        "schema": "feats-phase6-consolidation-manifest-v1",
        "expected_records": len(expected_ids),
        "consolidated_records": len(output),
        "shards": shard_info,
    }
    return output, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--shards", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    rows, report = consolidate(read_jsonl(args.manifest), args.shards)
    write_jsonl(args.output, rows)
    report["output_sha256"] = file_sha256(args.output)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
