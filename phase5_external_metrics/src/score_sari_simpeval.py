#!/usr/bin/env python3
"""Sentence-level SARI for SimpEval 2022, as in the LENS meta-evaluation.

Uses the SARI implementation shipped with the LENS repository
(``experiments/meta_evaluation/metrics/sari.py``, commit ``72c3c33``): the
score is ``SARIsent(original, output, references)[3][0]``, exactly what its
``SARI.compute_metric`` returns. SimpEval 2022 has one human reference per
original (``data/simpeval_2022/references/test.{src,dst}``).

Environment: ``.venv-phase5-lens`` (``nltk`` pinned in requirements-lens.txt)
with ``NLTK_DATA`` pointing to a folder that holds ``punkt_tab``.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

LENS_COMMIT = "72c3c337f6f77c94a5d512b50306bf9da5d4c741"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--lens-repo", type=Path, required=True, help="clone of the LENS repository")
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    commit = subprocess.run(["git", "-C", str(a.lens_repo), "rev-parse", "HEAD"], capture_output=True,
                            text=True, check=True).stdout.strip()
    if commit != LENS_COMMIT:
        raise SystemExit(f"LENS repository at {commit}, expected {LENS_COMMIT}")
    meta = a.lens_repo / "experiments/meta_evaluation"
    sys.path.insert(0, str(meta))
    from metrics.sari import SARIsent  # noqa: E402  (LENS implementation)

    refs_dir = meta / "data/simpeval_2022/references"
    src = (refs_dir / "test.src").read_text(encoding="utf-8").splitlines()
    dst = (refs_dir / "test.dst").read_text(encoding="utf-8").splitlines()
    reference = {s.strip(): d.strip() for s, d in zip(src, dst) if s.strip()}
    rows = list(csv.DictReader((a.lens_repo / "data/simpeval_2022.csv").open(encoding="utf-8")))
    out = []
    for r in rows:
        original = r["original"].strip()
        if original not in reference:
            raise SystemExit(f"no reference for original {r['original_id']}")
        score = SARIsent(original, r["generation"], [reference[original]])[3][0]
        # Same id format as the other SimpEval 2022 baselines: simpeval_2022:<original_id>:<system>.
        out.append({"evaluation_id": f"simpeval_2022:{r['original_id']}:{r['system']}", "sari": score})
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("w", encoding="utf-8") as handle:
        for row in out:
            handle.write(json.dumps(row) + "\n")
    print(json.dumps({"items": len(out), "lens_commit": commit, "output": str(a.output)}))


if __name__ == "__main__":
    main()
