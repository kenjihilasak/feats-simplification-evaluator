#!/usr/bin/env python3
"""Compose a round's examples file from reviewed examples files and chosen extra cases.

- `--base`: an examples file kept as it is (its case ids too).
- `--add AXIS FILE`: cases of that axis from another examples file whose pair is not already in the round; they get
  new case ids after the base ones.
- `--chosen RUN AXIS PAIR_ID LABEL`: one case taken from a run's corpus or MEANING/FLUENCY groups (e.g. pairs Serge
  chose in an earlier round), with case id `<LANG>-<LABEL>`; listed first in the output.
Writes the same columns as export_examples_csv.py, with a BOM.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from phase6_degraded_corpus.src.annotation.export_examples_csv import AXES, COLUMNS, corpus_case, group_case
from phase6_degraded_corpus.src.common.contracts import read_jsonl

GROUP_FILES = {"MEANING": ("scored/meaning_groups.jsonl", "groups.jsonl"), "FLUENCY": ("scored/fluency_groups.jsonl", "groups.jsonl")}


def rows_of(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def chosen_case(run: Path, axis: str, pair: str) -> dict:
    if axis in GROUP_FILES:
        for name in GROUP_FILES[axis]:
            if (run / name).exists():
                for g in read_jsonl(run / name):
                    if g["canonical_pair_id"] == pair:
                        return group_case(g, axis)
    for r in read_jsonl(run / "final/phase6_corpus.jsonl"):
        if r["canonical_pair_id"] == pair and r["axis"] == axis:
            return corpus_case(r)
    raise SystemExit(f"{axis} {pair} not found in {run}")


def case_rows(c: dict, case_id: str) -> list[dict]:
    return [{"case_id": case_id, "dataset": c["corpus"], "feats_axis": AXES[c["axis"]], "item_format": "rank3" if c["format"] == "graded" else "pair",
             "source": c["original"], "human_simplification": c["clean"], "automatic_degradation": text, "degradation_operation": op,
             "operation_description": desc, "target_score": score, "version": version, "canonical_pair_id": c["pair"]}
            for version, text, score, op, desc in c["versions"]]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--language", required=True)
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--add", nargs=2, action="append", default=[], metavar=("AXIS", "FILE"))
    p.add_argument("--chosen", nargs=4, action="append", default=[], metavar=("RUN", "AXIS", "PAIR_ID", "LABEL"))
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    lang = args.language.upper()
    chosen_pairs = {pair for _, _, pair, _ in args.chosen}
    out = []
    for run, axis, pair, label in args.chosen:
        out += case_rows(chosen_case(Path(run), axis, pair), f"{lang}-{label}")
    base = [r for r in rows_of(args.base) if r["canonical_pair_id"] not in chosen_pairs]
    out += base
    pairs = {r["canonical_pair_id"] for r in out}
    n = max(int(r["case_id"].rsplit("S", 1)[1]) for r in base if r["case_id"].rsplit("S", 1)[1].isdigit())
    for axis, path in args.add:
        new_ids = {}
        for r in rows_of(Path(path)):
            if r["feats_axis"] != AXES[axis] or (r["canonical_pair_id"] in pairs and r["case_id"] not in new_ids):
                continue
            if r["case_id"] not in new_ids:
                n += 1
                new_ids[r["case_id"]] = f"{lang}-S{n:03d}"
            out.append({**r, "case_id": new_ids[r["case_id"]]})
        pairs |= {r["canonical_pair_id"] for r in out}
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(out)
    print(args.output, len({r["case_id"] for r in out}), "cases")


if __name__ == "__main__":
    main()
