#!/usr/bin/env python3
"""Reparse raw model responses with the current parser without rerunning inference."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, write_jsonl
from phase6_degraded_corpus.src.generation.generate_degradations import automatic_checks, parse_generation


def reparse(manifest: list[dict], generated: list[dict]) -> tuple[list[dict], dict]:
    plans = {row["canonical_pair_id"]: row for row in manifest}
    if len(plans) != len(manifest):
        raise ValueError("duplicate canonical_pair_id in manifest")
    output = []
    transitions = Counter()
    for record in generated:
        pair_id = record["canonical_pair_id"]
        if pair_id not in plans:
            raise ValueError(f"unknown canonical_pair_id: {pair_id}")
        if record.get("status") != "failed_parse":
            output.append(record)
            continue
        original_status = record["status"]
        try:
            parsed = parse_generation(record["raw_response"])
            checks = automatic_checks(plans[pair_id], parsed)
            required = [value for key, value in checks.items() if key != "length_ratio"]
            status = "generated_pending_audit" if all(required) else "failed_validation"
            updated = {
                **record,
                "generation": parsed,
                "automatic_checks": checks,
                "status": status,
                "error": None,
                "parser_repair": {"previous_status": original_status, "parser": "phase6-v2-whitespace-normalized"},
            }
        except Exception:
            updated = record
            status = original_status
        transitions[f"{original_status}->{status}"] += 1
        output.append(updated)
    return output, {
        "schema": "feats-phase6-reparse-report-v1",
        "records": len(output),
        "transitions": dict(sorted(transitions.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--generated", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    rows, report = reparse(read_jsonl(args.manifest), read_jsonl(args.generated))
    write_jsonl(args.output, rows)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
