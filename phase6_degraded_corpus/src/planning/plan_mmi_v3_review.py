#!/usr/bin/env python3
"""Build the MMI v3 MOD/ILLOC review plans from the v2 allocation, on originals no review has seen."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl
from phase6_degraded_corpus.src.planning.plan_mmi_operations import IMPERATIVE_CUE, plan_illoc, plan_mod

CORPORA = {"WikiAutoEN", "ASSET"}


def reviewed_originals(paths: list[Path], id_files: list[Path]) -> set[str]:
    seen = {line.strip() for path in id_files for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}
    for path in paths:
        rows = json.loads(path.read_text(encoding="utf-8")) if path.suffix == ".json" else read_jsonl(path)
        seen |= {r["canonical_original_id"] for r in rows if r.get("canonical_original_id")}
    return seen


def pick(rows: list[dict], count: int, seed: int, tag: str) -> list[dict]:
    return sorted(rows, key=lambda r: stable_key(seed, f"{tag}:{r['canonical_pair_id']}"))[:count]


def build(allocation: list[dict], excluded: set[str], seed: int, size: int = 360) -> tuple[list[dict], list[dict]]:
    usable = [r for r in allocation if r["corpus"] in CORPORA and r["canonical_original_id"] not in excluded]
    mod = pick([r for r in usable if r["target_axis"] == "MOD"], size, seed, "mod")
    illoc = [r for r in usable if r["target_axis"] == "ILLOC" and not r["clean_simplification"].rstrip().endswith("?")]
    # Any clean pair can host an injection; deontic modals are rare, so draw them from every axis.
    hosts = {r["canonical_pair_id"]: r for r in usable if not r["clean_simplification"].rstrip().endswith("?")}
    mod_ids = {r["canonical_pair_id"] for r in mod}
    modal = pick([{**r, "target_axis": "ILLOC"} for r in hosts.values() if r["canonical_pair_id"] not in mod_ids and IMPERATIVE_CUE.search(r["clean_simplification"])], size // 3, seed, "modal")
    taken = {r["canonical_pair_id"] for r in modal}
    plain = pick([r for r in illoc if r["canonical_pair_id"] not in taken and not IMPERATIVE_CUE.search(r["clean_simplification"])], size - len(modal), seed, "plain")
    planned_mod, planned_illoc = plan_mod(mod, seed), plan_illoc(modal + plain, seed)
    for row in planned_illoc:  # every modal-bearing row is spent on the scarce imperative operation
        if row["canonical_pair_id"] in taken:
            row["operation"] = "illoc_imperative_swap"
    for row in planned_mod + planned_illoc:
        row["plan_schema"] = "feats-phase6-mmi-plan-v3"
    return planned_mod, planned_illoc


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--allocation", type=Path, required=True)
    p.add_argument("--exclude", type=Path, action="append", default=[], help="JSONL/JSON with canonical_original_id")
    p.add_argument("--exclude-ids", type=Path, action="append", default=[], help="text file, one original id per line")
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--seed", type=int, default=20261002)
    args = p.parse_args()
    mod, illoc = build(read_jsonl(args.allocation), reviewed_originals(args.exclude, args.exclude_ids), args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "mod_review_plan.jsonl", mod)
    write_jsonl(args.output_dir / "illoc_review_plan.jsonl", illoc)
    from collections import Counter
    print(json.dumps({"MOD": Counter(r["operation"] for r in mod), "ILLOC": Counter(r["operation"] for r in illoc)}, indent=2))


if __name__ == "__main__":
    main()
