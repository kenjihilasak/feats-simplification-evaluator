"""Answer Q1–Q3 of axis_validation_v1 (plan §1, §6): select, predict once, compare.

Selection uses only synthetic validation (mean best pairwise accuracy over seeds per
model × learning rate). The chosen configuration's three seed checkpoints score every
evaluation item; the headline score is the seed-averaged sigmoid. Baselines are joined by
`pair_id`. Test sets are read once here, after selection.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr, spearmanr

from contracts import atomic_json, read_jsonl

BASELINES = ("nli_bidirectional_entailment", "length_ratio", "inverse_length_ratio", "acceptability",
             "lens_salsa_score", "referee_score")
SHORTCUTS = ("length_ratio", "inverse_length_ratio", "acceptability")
RATING_SETS = ("simplicity_da", "human_likert", "simpeval_2022")
MARGIN = -0.05


def select_config(training_root: Path, axis: str) -> dict:
    runs = defaultdict(list)
    for path in (training_root / axis).glob("*/lr_*/seed_*/run.json"):
        run = json.loads(path.read_text())
        runs[(path.parts[-4], path.parts[-3])].append({**run, "dir": str(path.parent)})
    if not runs:
        raise FileNotFoundError(f"no completed runs for {axis}")
    table = {f"{m}/{lr}": {"seeds": len(r), "mean_val_acc": float(np.mean([x["best_validation_pairwise_accuracy"] for x in r])),
                           "std_val_acc": float(np.std([x["best_validation_pairwise_accuracy"] for x in r]))}
             for (m, lr), r in runs.items()}
    best = max(runs, key=lambda k: (np.mean([x["best_validation_pairwise_accuracy"] for x in runs[k]]), -len(runs[k])))
    return {"chosen": f"{best[0]}/{best[1]}", "checkpoints": [x["dir"] + "/checkpoint" for x in runs[best]], "table": table}


def predict(checkpoints: list[str], items: list[dict], batch_size: int = 32) -> list[float]:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    all_scores = []
    for checkpoint in checkpoints:
        tokenizer = AutoTokenizer.from_pretrained(checkpoint, local_files_only=True)
        model = AutoModelForSequenceClassification.from_pretrained(checkpoint, local_files_only=True).to(device).eval()
        scores = []
        with torch.inference_mode():
            for start in range(0, len(items), batch_size):
                batch = items[start:start + batch_size]
                enc = tokenizer([x["original"] for x in batch], [x["candidate"] for x in batch], padding=True,
                                truncation=True, max_length=256, return_tensors="pt").to(device)
                scores += model(**enc).logits.squeeze(-1).float().sigmoid().cpu().tolist()
        all_scores.append(scores)
        del model
    return list(np.mean(all_scores, axis=0))


def load_baselines(baseline_dir: Path) -> dict[str, dict]:
    joined: dict[str, dict] = defaultdict(dict)
    for path in baseline_dir.glob("*.jsonl"):
        for row in read_jsonl(path):
            key = row.get("pair_id")
            if row.get("variant") and not str(key).endswith(row["variant"]):
                key = f'{row["evaluation_id"]}:{row["variant"]}'
            for field in BASELINES:
                if field in row and row[field] not in (None, ""):
                    joined[key][field] = float(row[field])
    return joined


def bootstrap(rows: list[dict], a: str, b: str | None, reps: int, seed: int) -> dict:
    groups = defaultdict(list)
    for row in rows:
        groups[row["original_id"]].append(row)
    keys = sorted(groups)
    rho = lambda rs, f: spearmanr([r[f] for r in rs], [r["human_score"] for r in rs]).statistic
    point = rho(rows, a) - (rho(rows, b) if b else 0.0)
    rng, values = np.random.default_rng(seed), []
    for _ in range(reps):
        sample = [r for k in rng.choice(keys, len(keys)) for r in groups[k]]
        v = rho(sample, a) - (rho(sample, b) if b else 0.0)
        if np.isfinite(v):
            values.append(v)
    lo, hi = np.quantile(values, [0.025, 0.975])
    return {"estimate": float(point), "ci95": [float(lo), float(hi)], "n": len(rows), "originals": len(keys)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, default=Path("phase7_feats_training/runs/axis_validation_v1"))
    parser.add_argument("--axes", nargs="+", default=["MEANING"])
    parser.add_argument("--reps", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260930)
    args = parser.parse_args()
    root = args.run_root
    baselines = load_baselines(root / "baselines/predictions")
    evaluation = {name: list(read_jsonl(root / f"data/evaluation/{name}.jsonl")) for name in RATING_SETS}
    heldout = [r for name in ("heldout_v2", "heldout_meaning_v21") for r in read_jsonl(root / f"data/evaluation/{name}.jsonl")]
    dataset = [r for r in read_jsonl(root / "data/dataset.jsonl") if r["split"] == "validation"]
    results = {}
    for axis in args.axes:
        selection = select_config(root / "training", axis)
        out = {"selection": selection}
        # --- rating sets (MEANING is the construct; others reported as context) ---
        for name, rows in evaluation.items():
            rows = [dict(r, human_score=float(r["human_score"])) for r in rows]
            scores = predict(selection["checkpoints"], rows)
            for r, s in zip(rows, scores):
                r["model"] = s
                r.update(baselines.get(r["evaluation_id"], {}))
            atomic_json(root / f"evaluation/{axis}/{name}_scored.json", rows)
            fields = ["model"] + [f for f in BASELINES if all(f in r for r in rows)]
            per = {f: bootstrap(rows, f, None, args.reps, args.seed) for f in fields}
            rival = max((f for f in fields if f != "model"), key=lambda f: per[f]["estimate"])
            entry = {"spearman": per, "strongest_baseline": rival,
                     "model_minus_strongest": bootstrap(rows, "model", rival, args.reps, args.seed)}
            if "nli_bidirectional_entailment" in fields:
                entry["model_minus_nli"] = bootstrap(rows, "model", "nli_bidirectional_entailment", args.reps, args.seed)
            if name == "simplicity_da":
                systems = defaultdict(list)
                for r in rows:
                    systems[r["system"]].append(r)
                entry["system_level_pearson"] = {f: float(pearsonr([np.mean([x[f] for x in v]) for v in systems.values()],
                                                                   [np.mean([x["human_score"] for x in v]) for v in systems.values()]).statistic)
                                                 for f in fields}
            out[name] = entry
        # --- human-audited heldout pairs of this axis (Valid/Unsure only) ---
        cases = [r for r in heldout if r["axis"] == axis and str(r.get("included")) == "True"]
        items = [{"original": c["original"], "candidate": c[v], "key": f'{c["evaluation_id"]}:{v}'} for c in cases for v in ("clean", "degraded")]
        scores = dict(zip([i["key"] for i in items], predict(selection["checkpoints"], items))) if items else {}
        fields = ["model"] + list(SHORTCUTS) + ["nli_bidirectional_entailment"]
        wins = defaultdict(list)
        by_op = defaultdict(list)
        for c in cases:
            vals = {}
            for v in ("clean", "degraded"):
                key = f'{c["evaluation_id"]}:{v}'
                vals[v] = {"model": scores[key], **baselines.get(key, {})}
            for f in fields:
                if f in vals["clean"] and f in vals["degraded"]:
                    wins[f].append(vals["clean"][f] > vals["degraded"][f])
            by_op[c["operation"]].append(vals["clean"]["model"] > vals["degraded"]["model"])
        pair = {f: float(np.mean(w)) for f, w in wins.items()}
        best_shortcut = max((f for f in SHORTCUTS if f in pair), key=lambda f: pair[f], default=None)
        out["heldout_pairwise"] = {"n": len(cases), "accuracy": pair, "by_operation": {k: float(np.mean(v)) for k, v in by_op.items()},
                                   "best_shortcut": best_shortcut}
        # --- synthetic validation pairwise, model vs shortcuts ---
        synth = [r for r in dataset if r["axis"] == axis]
        s_items = [{"original": r["original"], "candidate": r["candidate_simplification"], "key": r["example_id"]} for r in synth]
        s_scores = predict(selection["checkpoints"], s_items)
        by_pair = defaultdict(dict)
        for r, s in zip(synth, s_scores):
            by_pair[r["canonical_pair_id"]][r["provenance"]["variant"]] = {"model": s, **baselines.get(r["canonical_pair_id"], {})}
        out["synthetic_validation_pairwise"] = {"n": len(by_pair), "model": float(np.mean([p["simplified"]["model"] > p["degraded"]["model"] for p in by_pair.values()]))}
        # --- pre-registered verdicts ---
        if axis == "MEANING":
            verdict = {}
            for name in ("simplicity_da", "human_likert"):
                e = out[name]
                verdict[name] = {"model_ci_excludes_0": e["spearman"]["model"]["ci95"][0] > 0,
                                 "non_inferior_to_strongest": e["model_minus_strongest"]["ci95"][0] > MARGIN}
            out["Q1_pass"] = all(v["model_ci_excludes_0"] and v["non_inferior_to_strongest"] for v in verdict.values())
            out["Q1_detail"] = verdict
            out["Q2"] = {n: out[n].get("model_minus_nli") for n in ("simplicity_da", "human_likert")}
        else:
            acc = pair.get("model", 0.0)
            out["Q3_pass"] = acc >= 0.85 and best_shortcut is not None and acc - pair[best_shortcut] >= 0.10
        results[axis] = out
        atomic_json(root / f"evaluation/{axis}/results.json", out)
    print(json.dumps({a: {k: v for k, v in r.items() if k in ("Q1_pass", "Q3_pass")} | {"chosen": r["selection"]["chosen"]}
                      for a, r in results.items()}, indent=2))


if __name__ == "__main__":
    main()
