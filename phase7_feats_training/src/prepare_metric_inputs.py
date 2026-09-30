"""Freeze Phase 7 evaluation rows into the reference-free Phase 5 metric schema."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

from contracts import read_jsonl, write_jsonl


def adapt_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map rated outputs to Phase 5 pairs; deliberately never copy references."""
    output = []
    for row in rows:
        candidate = row.get("candidate", row.get("candidate_simplification"))
        if candidate is None:
            raise ValueError("Input row has no rated candidate")
        output.append({
            "pair_id": row.get("evaluation_id", row.get("example_id")),
            "original": row["original"],
            "simple": candidate,
            "language": "en",
            "source": row.get("dataset", "phase7"),
        })
    return output


def heldout_variants(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        if not row.get("included", True):
            continue
        for variant in ("clean", "degraded"):
            output.append({
                "pair_id": f"{row['evaluation_id']}:{variant}", "original": row["original"],
                "simple": row[variant], "language": "en", "source": row["dataset"],
                "evaluation_id": row["evaluation_id"], "variant": variant,
            })
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--heldout", action="store_true")
    args = parser.parse_args()
    rows = list(read_jsonl(args.input))
    write_jsonl(args.output, heldout_variants(rows) if args.heldout else adapt_rows(rows))


if __name__ == "__main__":
    main()
