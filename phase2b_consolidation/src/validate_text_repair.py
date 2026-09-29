#!/usr/bin/env python3
"""Validate a Phase 2b text-repair variant against its immutable input."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from repair_text import BLOCKED_LANGUAGES, REPAIR_VERSION, iter_jsonl, repair_record, repaired_key, text_sha256


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate(input_root: Path, output_root: Path) -> dict:
    errors: list[str] = []
    files = []
    input_paths = sorted(input_root.glob("*/feats_consolidated.jsonl"))
    expected_layout = {path.relative_to(input_root) for path in input_paths}
    actual_layout = {path.relative_to(output_root) for path in output_root.glob("*/feats_consolidated.jsonl")}
    if expected_layout != actual_layout:
        errors.append(f"layout mismatch missing={sorted(expected_layout-actual_layout)} extra={sorted(actual_layout-expected_layout)}")
    for input_path in input_paths:
        relative = input_path.relative_to(input_root); output_path = output_root / relative
        if not output_path.exists():
            continue
        language = input_path.parent.name
        input_rows = iter_jsonl(input_path); output_rows = iter_jsonl(output_path)
        count = repaired_count = 0; pair_ids = set(); original_ids = set()
        duplicate_rows = []; key_min: dict[bytes, str] = {}
        while True:
            try: raw = next(input_rows)
            except StopIteration: raw = None
            try: out = next(output_rows)
            except StopIteration: out = None
            if raw is None or out is None:
                if raw is not None or out is not None:
                    errors.append(f"row count mismatch for {language}")
                break
            count += 1; label = f"{language}:{count}"
            for key in ("canonical_pair_id", "canonical_original_id"):
                if raw.get(key) != out.get(key): errors.append(f"{key} changed at {label}")
            pair_ids.add(raw["canonical_pair_id"]); original_ids.add(raw["canonical_original_id"])
            if out.get("original_raw") != raw.get("original") or out.get("simple_raw") != raw.get("simple"):
                errors.append(f"raw text mismatch at {label}")
            if out.get("original_raw_sha256") != text_sha256(raw["original"]) or out.get("simple_raw_sha256") != text_sha256(raw["simple"]):
                errors.append(f"raw hash mismatch at {label}")
            expected = repair_record(raw)
            for key in ("original", "simple", "text_repairs", "text_repaired", "text_repair_version"):
                if out.get(key) != expected.get(key): errors.append(f"deterministic repair mismatch for {key} at {label}")
            if language in BLOCKED_LANGUAGES and out.get("text_repaired"):
                errors.append(f"repair in blocked language at {label}")
            if out.get("text_repaired"): repaired_count += 1
            key = repaired_key(language, out["original"], out["simple"])
            key_min[key] = min(key_min.get(key, out["canonical_pair_id"]), out["canonical_pair_id"])
            duplicate_rows.append((out["canonical_pair_id"], key, out.get("repaired_duplicate_of")))
            if len(errors) >= 100: break
        for pair_id, key, marker in duplicate_rows:
            expected_marker = None if pair_id == key_min[key] else key_min[key]
            if marker != expected_marker:
                errors.append(f"duplicate marker mismatch for {pair_id}: {marker} != {expected_marker}")
        files.append({"language": language, "rows": count, "repaired_rows": repaired_count,
                      "pair_ids": len(pair_ids), "original_ids": len(original_ids),
                      "bytes": output_path.stat().st_size, "sha256": file_sha256(output_path)})
    return {"schema": "feats-text-repair-validation-v1", "valid": not errors,
            "validated_at_utc": datetime.now(timezone.utc).isoformat(),
            "repair_version": REPAIR_VERSION, "input_root": str(input_root),
            "output_root": str(output_root), "files": files, "errors": errors[:100]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.input_root, args.output_root)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
