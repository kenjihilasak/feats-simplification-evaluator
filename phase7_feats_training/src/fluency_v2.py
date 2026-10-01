"""FLUENCY recipe v2 (graded): reuses meaning_v2 machinery with FLUENCY data and fluency ratings.

Arms: A = graded groups (clean / Original copy / also-trim = 1, minor 0.67, major 0.33,
severe 0); binary = the same pairs with only clean (1) and one single-error variant (0),
i.e. the FOSE v1 design. Human test: Simplicity-DA and Human-Likert *fluency* ratings;
heldout = FLUENCY cases judged Valid in the FOSE v1 blinded review.
Subcommands: build, features, diagnose, train, evaluate (as in meaning_v2).
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

import meaning_v2 as mv
from contracts import atomic_json, read_jsonl, write_jsonl
from evaluation_loaders import load_human_likert, load_simpeval_2022, load_simplicity_da

ROOT = mv.ROOT
mv.RUN = RUN = ROOT / "phase7_feats_training/runs/fluency_v2"
GROUPS = ROOT / "phase6_degraded_corpus/runs/fluency_graded_en_v1/groups.jsonl"
SOURCES = ROOT / "phase6_degraded_corpus/runs/mmi_en_v2/pools/evaluation_sources"
REVIEW = ROOT / "phase6_degraded_corpus/docs/reports/current/fose_v1_review.md"
REVIEW_KEY = ROOT / "phase6_degraded_corpus/runs/fose_en_v1/audit/review_key.json"
mv.ARMS = ARMS = {"A": ("graded", False), "binary": ("binary", False)}


def build() -> None:
    graded, binary = [], []
    for g in read_jsonl(GROUPS):
        base = {"group_id": g["canonical_pair_id"], "original_id": g["canonical_original_id"], "split": g["split"], "original": g["original"]}
        for m in g["members"]:
            graded.append({**base, "level": m["level"], "target": m["target_score"], "candidate": m["text"]})
        single = [m for m in g["members"] if m["level"] in {"minor", "major"} and len(m.get("edits", [])) == 1]
        if single:
            clean = next(m for m in g["members"] if m["level"] == "clean")
            binary += [{**base, "level": "clean", "target": 1.0, "candidate": clean["text"]},
                       {**base, "level": "contradiction", "target": 0.0, "candidate": single[0]["text"]}]
    write_jsonl(RUN / "data/graded.jsonl", graded)
    write_jsonl(RUN / "data/binary.jsonl", binary)
    ev = {"simplicity_da": load_simplicity_da(SOURCES / "simplicity_da/data/simplicity_DA.csv", aspect="fluency"),
          "human_likert": load_human_likert(SOURCES / "questeval_human_evaluations/simplification_human_evaluations/questeval_simplification_likert_ratings.csv", aspect="fluency"),
          "simpeval_2022": load_simpeval_2022(SOURCES / "lens_heineman/data/simpeval_2022.csv")}
    for name, rows in ev.items():
        write_jsonl(RUN / f"data/evaluation/{name}.jsonl", rows)
    write_jsonl(RUN / "data/evaluation/heldout_fose.jsonl", heldout_cases())
    print({"graded": len(graded), "binary_pairs": len(binary) // 2, **{k: len(v) for k, v in ev.items()},
           "heldout": len(heldout_cases())})


def heldout_cases() -> list[dict]:
    key = json.loads(REVIEW_KEY.read_text())
    cases = []
    for block in re.split(r"\n### Case ", REVIEW.read_text(encoding="utf-8"))[1:]:
        cid = block.split("\n", 1)[0].strip()
        ticked = re.findall(r"^\s*[-*] \[[xX]\] (Valid|Invalid|Unsure)", block, flags=re.M)
        field = lambda name: re.search(rf"\*\*{name}:\*\*\s*(.*)", block).group(1).strip()
        if key[cid]["target_axis"] == "FLUENCY" and len(ticked) == 1 and ticked[0] in {"Valid", "Unsure"}:
            cases.append({"case_id": cid, "original": field("Original"), "clean": field("Simplified"),
                          "degraded": field("Degraded"), "corpus": key[cid]["corpus"]})
    return cases


def evaluation_items() -> list[dict]:
    items = []
    for name in ("simplicity_da", "human_likert", "simpeval_2022"):
        items += [{"original": r["original"], "candidate": r["candidate"]} for r in read_jsonl(RUN / f"data/evaluation/{name}.jsonl")]
    for r in read_jsonl(RUN / "data/evaluation/heldout_fose.jsonl"):
        items += [{"original": r["original"], "candidate": r[v]} for v in ("clean", "degraded")]
    return items


def features() -> None:
    mv.evaluation_items = evaluation_items
    names = ("graded", "binary")
    sys_import = __import__("sys")
    sys_import.path.insert(0, str(ROOT))
    from phase6_degraded_corpus.src.evaluation.score_mmi_candidates import Checkers
    cfg = json.loads((ROOT / "phase6_degraded_corpus/configs/experiments/mmi_en_v2_pools.json").read_text())
    cfg["cache_dir"] = str(ROOT / cfg["cache_dir"])
    texts = {}
    for name in names:
        for r in read_jsonl(RUN / f"data/{name}.jsonl"):
            texts[mv.key(r["original"], r["candidate"])] = (r["original"], r["candidate"])
    for r in evaluation_items():
        texts[mv.key(r["original"], r["candidate"])] = (r["original"], r["candidate"])
    keys = sorted(texts)
    ck = Checkers(cfg, "cuda")
    acc = ck.acceptability([texts[k][1] for k in keys])
    nli = ck.nli_probs([texts[k][0] for k in keys], [texts[k][1] for k in keys])
    write_jsonl(RUN / "data/features.jsonl", [{"key": k, "acceptability": a, **n} for k, a, n in zip(keys, acc, nli)])
    print({"texts": len(keys)})


def evaluate(reps: int) -> None:
    import torch
    from transformers import AutoTokenizer
    from run_evaluation import BASELINES, bootstrap, load_baselines
    from scipy.stats import pearsonr
    device = torch.device("cuda")
    feats = mv.load_features()
    baselines = load_baselines(ROOT / "phase7_feats_training/runs/axis_validation_v1/baselines/predictions")
    results = {}
    arm_scores = {}
    for arm, (data_name, use_nli) in ARMS.items():
        runs = defaultdict(list)
        for path in (RUN / f"training/{arm}").glob("*/lr_*/seed_*/run.json"):
            run = json.loads(path.read_text())
            runs[(path.parts[-4], path.parts[-3])].append({**run, "dir": path.parent})
        sel = max(runs, key=lambda k: np.mean([r["best_validation_spearman"] for r in runs[k]]))
        models = []
        for run in runs[sel]:
            model = mv.make_model(run["snapshot"], use_nli).to(device)
            model.load_state_dict(torch.load(run["dir"] / "model.pt", map_location=device))
            models.append((model, AutoTokenizer.from_pretrained(run["dir"] / "tokenizer", local_files_only=True)))
        score = lambda rows: list(np.mean([mv.predict_rows(m, t, rows, feats, use_nli, device) for m, t in models], axis=0))
        out = {"selection": {"chosen": "/".join(sel), "table": {f"{m}/{lr}": float(np.mean([x["best_validation_spearman"] for x in r]))
                                                               for (m, lr), r in runs.items()}}}
        for name in ("simplicity_da", "human_likert", "simpeval_2022"):
            rows = [dict(r, human_score=float(r["human_score"])) for r in read_jsonl(RUN / f"data/evaluation/{name}.jsonl")]
            for r, s in zip(rows, score(rows)):
                r["model"] = s
                # Baselines were stored with the older Human-Likert id (no text hash) = aggregation_id.
                r.update(baselines.get(r["evaluation_id"]) or baselines.get(r.get("aggregation_id"), {}))
            arm_scores[(arm, name)] = rows
        held = list(read_jsonl(RUN / "data/evaluation/heldout_fose.jsonl"))
        c = score([{"original": r["original"], "candidate": r["clean"]} for r in held])
        d = score([{"original": r["original"], "candidate": r["degraded"]} for r in held])
        out["heldout_pairwise"] = {"n": len(held), "accuracy": float(np.mean([x > y for x, y in zip(c, d)]))}
        results[arm] = out
        del models
        torch.cuda.empty_cache()
    for name in ("simplicity_da", "human_likert", "simpeval_2022"):
        rows = arm_scores[("A", name)]
        for r, b in zip(rows, arm_scores[("binary", name)]):
            r["binary_model"] = b["model"]
        fields = ["model", "binary_model"] + [f for f in BASELINES if all(f in r for r in rows)]
        per = {f: bootstrap(rows, f, None, reps, 20260930) for f in fields}
        rival = max((f for f in fields if f not in {"model", "binary_model"}), key=lambda f: per[f]["estimate"])
        entry = {"spearman": per, "strongest_baseline": rival,
                 "A_minus_strongest": bootstrap(rows, "model", rival, reps, 20260930),
                 "A_minus_acceptability": bootstrap(rows, "model", "acceptability", reps, 20260930),
                 "A_minus_binary": bootstrap(rows, "model", "binary_model", reps, 20260930)}
        if name == "simplicity_da":
            systems = defaultdict(list)
            for r in rows:
                systems[r["system"]].append(r)
            entry["system_level_pearson"] = {f: float(pearsonr([np.mean([x[f] for x in v]) for v in systems.values()],
                                                               [np.mean([x["human_score"] for x in v]) for v in systems.values()]).statistic)
                                             for f in fields}
        results[name] = entry
    crit = {n: {"ci_excludes_0": results[n]["spearman"]["model"]["ci95"][0] > 0,
                "non_inferior_strongest": results[n]["A_minus_strongest"]["ci95"][0] > -0.05,
                "beats_acceptability": results[n]["A_minus_acceptability"]["ci95"][0] > 0,
                "beats_binary": results[n]["A_minus_binary"]["ci95"][0] > 0} for n in ("simplicity_da", "human_likert")}
    results["criteria"] = crit
    results["Q1_pass"] = all(v["ci_excludes_0"] and v["non_inferior_strongest"] for v in crit.values())
    results["Q2_pass"] = any(v["beats_acceptability"] for v in crit.values())
    atomic_json(RUN / "evaluation/results.json", results)
    print(json.dumps({"Q1_pass": results["Q1_pass"], "Q2_pass": results["Q2_pass"], "criteria": crit}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "features", "diagnose", "train", "evaluate"))
    parser.add_argument("--arm", choices=tuple(ARMS))
    parser.add_argument("--lr", type=float)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--reps", type=int, default=10000)
    args = parser.parse_args()
    if args.command == "build":
        build()
    elif args.command == "features":
        features()
    elif args.command == "diagnose":
        mv.diagnose()
    elif args.command == "train":
        mv.train(args.arm, args.lr, args.seed, ROOT / "phase7_feats_training/configs/models/deberta_v3_base.json", 3, 8)
    else:
        evaluate(args.reps)


if __name__ == "__main__":
    main()
