#!/usr/bin/env python3
"""Plan the ILLOC control: a direct paraphrase of the host sentence, scored like the clean text (1.0).

Without it every ILLOC degradation is the only reworded version, so "reworded and longer" predicts the lower
score (v2 shortcut audit, 29 Oct 2026). The control rewords the sentence while keeping the act direct, so wording
alone no longer separates the versions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, write_jsonl


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--allocation", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    rows = [{**r, "host_operation": r["operation"], "operation": "illoc_direct_paraphrase"} for r in read_jsonl(args.allocation)]
    write_jsonl(args.output, rows)
    print(json.dumps({"planned": len(rows)}))


if __name__ == "__main__":
    main()
