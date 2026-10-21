#!/usr/bin/env python3
"""Turn scored fronting candidates into graded MOD groups.

`prepare` writes rule candidates for B (reorder of the clean text) and AB (reorder of the fronted text) in the
generation format, so `score_mmi_candidates` checks them like any other MOD candidate. `finalize` keeps groups
where A, B and AB are all valid."""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path
from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl
from phase6_degraded_corpus.src.planning.plan_mmi_operations import split_sentences


def swap(sentences: list[str], index: int) -> str:
    changed = list(sentences)
    changed[index:index + 2] = reversed(changed[index:index + 2])
    return " ".join(changed)


def prepare(scored: list[dict], plan: list[dict]) -> tuple[list[dict], list[dict]]:
    """`plan` supplies the planning fields (sentences, reorder_index) the generator does not copy."""
    planned = {r["canonical_pair_id"]: r for r in plan}
    plans, generations = [], []
    for row in scored:
        plan_row = planned[row["canonical_pair_id"]]
        row = {**row, **{k: plan_row[k] for k in ("sentences", "reorder_index")}, "language": plan_row.get("language", "en")}
        if row["selected_index"] is None:
            continue
        fronted = row["candidates"][row["selected_index"]]["degraded"]
        fronted_sentences = split_sentences(fronted, row.get("language", "en"))
        if len(fronted_sentences) != len(row["sentences"]):
            continue
        for version, text in (("B", swap(row["sentences"], row["reorder_index"])), ("AB", swap(fronted_sentences, row["reorder_index"]))):
            item = {**{k: v for k, v in row.items() if k not in {"candidates", "selected_index", "check_pass_at_1", "yield", "single_edit"}},
                    "canonical_pair_id": f'{row["canonical_pair_id"]}#{version}', "operation": "mod_sentence_reorder",
                    "generator_kind": "rule", "rule_output": {"degraded": text}, "target_sentence_index": None}
            plans.append(item)
            generations.append({**item, "candidates": [{"raw": None, "parsed": item["rule_output"], "degraded": text, "generator": "rule"}]})
    return plans, generations


def finalize(fronting: list[dict], reorders: list[dict], seed: int) -> list[dict]:
    by_id = {r["canonical_pair_id"]: r for r in reorders}
    groups = []
    for row in fronting:
        pid = row["canonical_pair_id"]
        b, ab = by_id.get(f"{pid}#B"), by_id.get(f"{pid}#AB")
        if row["selected_index"] is None or not b or not ab:
            continue
        cand = row["candidates"][row["selected_index"]]
        versions = {"A": {"degraded": cand["degraded"], "operation": "mod_front_heavy", "features": cand["features"], "valid": True},
                    "B": {"degraded": b["candidates"][0]["degraded"], "operation": "mod_sentence_reorder", "features": b["candidates"][0].get("features"), "valid": b["yield"]},
                    "AB": {"degraded": ab["candidates"][0]["degraded"], "operation": "both", "features": ab["candidates"][0].get("features"), "valid": ab["yield"]}}
        groups.append({k: row[k] for k in ("canonical_pair_id", "canonical_original_id", "corpus", "original", "clean_simplification",
                                            "clean_acceptability", "clean_nli_probabilities")} | {
            "target_axis": "MOD", "versions": versions, "valid": all(v["valid"] for v in versions.values()),
            "mild_version": "A" if int(stable_key(seed, f"mild:{pid}"), 16) % 2 == 0 else "B"})
    return groups


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("prepare"); a.add_argument("--scored", type=Path, required=True); a.add_argument("--plan", type=Path, required=True); a.add_argument("--plan-out", type=Path, required=True); a.add_argument("--generations-out", type=Path, required=True)
    b = sub.add_parser("finalize"); b.add_argument("--fronting", type=Path, required=True); b.add_argument("--reorders", type=Path, required=True); b.add_argument("--output", type=Path, required=True); b.add_argument("--seed", type=int, default=20261002)
    args = p.parse_args()
    if args.cmd == "prepare":
        plans, generations = prepare(read_jsonl(args.scored), read_jsonl(args.plan))
        write_jsonl(args.plan_out, plans); write_jsonl(args.generations_out, generations)
        print(json.dumps({"rule_rows": len(plans)}))
    else:
        groups = finalize(read_jsonl(args.fronting), read_jsonl(args.reorders), args.seed)
        write_jsonl(args.output, groups)
        print(json.dumps({"groups": len(groups), "valid": sum(g["valid"] for g in groups)}))


if __name__ == "__main__":
    main()
