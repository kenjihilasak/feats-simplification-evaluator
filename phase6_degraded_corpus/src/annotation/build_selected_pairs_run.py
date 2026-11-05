#!/usr/bin/env python3
"""Pool rows for chosen pairs on a chosen axis, so earlier selected items (Serge's English choice) get v2 degradations.

A normal pool gives each original one task and, in English, needs the single Phase 3a strategy; pairs chosen in an
earlier round can miss either condition. This writes `pools/structural_candidates.jsonl` for exactly the chosen
pairs, keeping only the rule sites or host of the chosen axis (MEANING and FLUENCY need none), and the allocation files once their clean texts are
scored (`allocate`). Pairs the v2 rules cannot degrade on that axis are reported and left out.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, write_jsonl
from phase6_degraded_corpus.src.common.languages import load_nlp
from phase6_degraded_corpus.src.selection.select_fose_pools import eligible_rule_sites, structural_features
from phase6_degraded_corpus.src.selection.select_mmi_pools import corpus_of
from phase6_degraded_corpus.src.selection.select_multilingual_pools import RULE_AXES, TASK_ORDER, illoc_host, mod_host, shape

GENERIC = ("MEANING", "FLUENCY")


def prepare(cfg: dict, chosen: dict[str, str]) -> tuple[list[dict], dict]:
    lang, nlp, rows, report = cfg["language"], load_nlp(cfg["language"], disable=("ner",)), [], {}
    for row in read_jsonl(Path(cfg["phase2b_file"])):
        axis = chosen.get(row["canonical_pair_id"])
        if not axis:
            continue
        original, simple = row["original"].strip(), row["simple"].strip()
        feats = structural_features(original, simple)
        sites = {axis: eligible_rule_sites(axis, feats, nlp, lang)} if axis in RULE_AXES else {}
        mod = mod_host(simple, lang) if axis == "MOD" else None
        illoc = illoc_host(simple, lang, nlp) if axis == "ILLOC" else None
        # MEANING and FLUENCY apply to any pair; their groups come from generate_meaning_fluency_ml.
        ok = axis in GENERIC or bool(sites.get(axis)) or bool(mod) or bool(illoc)
        report[row["canonical_pair_id"]] = axis if ok else f"{axis}: no v2 site"
        if ok:
            rows.append({"schema": "feats-phase6-s1-pool-candidate-v1", "language": lang,
                         "canonical_pair_id": row["canonical_pair_id"], "canonical_original_id": row["canonical_original_id"],
                         "original": original, "clean_simplification": simple, "source": row["corpora"][0].get("source"),
                         "corpus": corpus_of(row), "eligible_sites": {k: v for k, v in sites.items() if v}, "mod_host": mod,
                         "illoc_host": illoc, "phase3a_strategy": None, "chosen_axis": axis,
                         "selection_features": {k: feats[k] for k in ("overlap", "len_ratio", "edit_blocks")}})
    for pid in chosen.keys() - report.keys():
        report[pid] = "not in the Phase 2b file"
    return rows, report


def allocate(run: Path, seed: int) -> dict:
    scores = {r["canonical_pair_id"]: r for r in read_jsonl(run / "pools/clean_quality_scores.jsonl")}
    tasks: dict[str, list[dict]] = {}
    for row in read_jsonl(run / "pools/structural_candidates.jsonl"):
        s = scores[row["canonical_pair_id"]]
        row = {**row, "clean_acceptability": s["acceptability"], "clean_nli_probabilities": s["nli_probabilities"]}
        axis = row["chosen_axis"]
        if axis in GENERIC:
            continue
        kind = "graded" if axis == "MOD" or (axis in RULE_AXES and len(row["eligible_sites"][axis]) >= 2 and axis != "EXPL") else "pair"
        task = f"{axis}_{kind}"
        tasks.setdefault(task, []).append(shape(task, row, seed))
    (run / "allocation").mkdir(parents=True, exist_ok=True)
    for task in TASK_ORDER:  # every file, empty or not: the rule step reads them all
        write_jsonl(run / f"allocation/{task.lower()}.jsonl", tasks.get(task, []))
    return {t: len(v) for t, v in tasks.items()}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=("prepare", "allocate"))
    p.add_argument("--config", type=Path, required=True, help="the language's experiment config (output_dir is replaced)")
    p.add_argument("--chosen", type=Path, required=True, help='JSON {"canonical_pair_id": "AXIS"}')
    p.add_argument("--run-dir", type=Path, required=True)
    args = p.parse_args()
    cfg = json.loads(args.config.read_text())
    if args.stage == "prepare":
        rows, report = prepare(cfg, json.loads(args.chosen.read_text()))
        (args.run_dir / "pools").mkdir(parents=True, exist_ok=True)
        write_jsonl(args.run_dir / "pools/structural_candidates.jsonl", rows)
        (args.run_dir / "pools/report_chosen.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(allocate(args.run_dir, cfg["seed"]), indent=2))


if __name__ == "__main__":
    main()
