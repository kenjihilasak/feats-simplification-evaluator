"""MEANING recipe v2 (graded loss): data, features, shortcut diagnostic, training, evaluation.

Subcommands
  build     member-level datasets for the arms (graded, graded_all, v1pairs)
  features  acceptability + NLI(original -> candidate) for every training and evaluation text (GPU)
  diagnose  within-group pairwise accuracy of length / acceptability shortcuts on validation
  train     one arm x lr x seed (GPU)
  evaluate  select per arm on synthetic validation, score the frozen human sets once (GPU)
Arms: A = graded; A_all = graded without the entailment filter; B = graded + NLI head;
C = v1 contradiction pairs + NLI head.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import atomic_json, read_jsonl, write_jsonl  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "phase7_feats_training/runs/meaning_v2"
GRADED = ROOT / "phase6_degraded_corpus/runs/meaning_graded_en_v1"
V1_DATASET = ROOT / "phase7_feats_training/runs/axis_validation_v1/data/dataset.jsonl"
V1_EVAL = ROOT / "phase7_feats_training/runs/axis_validation_v1/data/evaluation"
ARMS = {"A": ("graded", False), "A_all": ("graded_all", False), "B": ("graded", True), "C": ("v1pairs", True)}
NLI_KEYS = ("entailment", "neutral", "contradiction")


def key(original: str, candidate: str) -> str:
    return hashlib.sha256(f"{original}\0{candidate}".encode()).hexdigest()


# ---------------------------------------------------------------- build
def build() -> None:
    for name, path in (("graded", GRADED / "groups.jsonl"), ("graded_all", GRADED / "groups_all.jsonl")):
        rows = []
        for g in read_jsonl(path):
            for m in g["members"]:
                rows.append({"group_id": g["canonical_pair_id"], "original_id": g["canonical_original_id"], "split": g["split"],
                             "level": m["level"], "target": m["target_score"], "original": g["original"], "candidate": m["text"]})
        write_jsonl(RUN / f"data/{name}.jsonl", rows)
    rows = []
    for r in read_jsonl(V1_DATASET):
        if r["axis"] != "MEANING":
            continue
        rows.append({"group_id": r["canonical_pair_id"], "original_id": r["canonical_original_id"], "split": r["split"],
                     "level": "clean" if r["provenance"]["variant"] == "simplified" else "contradiction",
                     "target": float(r["target_score"]), "original": r["original"], "candidate": r["candidate_simplification"]})
    write_jsonl(RUN / "data/v1pairs.jsonl", rows)
    print({n: sum(1 for _ in read_jsonl(RUN / f"data/{n}.jsonl")) for n in ("graded", "graded_all", "v1pairs")})


def evaluation_items() -> list[dict]:
    items = []
    for name in ("simplicity_da", "human_likert", "simpeval_2022"):
        items += [{"original": r["original"], "candidate": r["candidate"]} for r in read_jsonl(V1_EVAL / f"{name}.jsonl")]
    for name in ("heldout_v2", "heldout_meaning_v21"):
        for r in read_jsonl(V1_EVAL / f"{name}.jsonl"):
            items += [{"original": r["original"], "candidate": r[v]} for v in ("clean", "degraded")]
    return items


# ---------------------------------------------------------------- features
def features() -> None:
    sys.path.insert(0, str(ROOT))
    from phase6_degraded_corpus.src.evaluation.score_mmi_candidates import Checkers
    cfg = json.loads((ROOT / "phase6_degraded_corpus/configs/experiments/mmi_en_v2_pools.json").read_text())
    cfg["cache_dir"] = str(ROOT / cfg["cache_dir"])
    texts = {}
    for name in ("graded", "graded_all", "v1pairs"):
        for r in read_jsonl(RUN / f"data/{name}.jsonl"):
            texts[key(r["original"], r["candidate"])] = (r["original"], r["candidate"])
    for r in evaluation_items():
        texts[key(r["original"], r["candidate"])] = (r["original"], r["candidate"])
    keys = sorted(texts)
    ck = Checkers(cfg, "cuda")
    acc = ck.acceptability([texts[k][1] for k in keys])
    nli = ck.nli_probs([texts[k][0] for k in keys], [texts[k][1] for k in keys])
    write_jsonl(RUN / "data/features.jsonl", [{"key": k, "acceptability": a, **n} for k, a, n in zip(keys, acc, nli)])
    print({"texts": len(keys)})


def load_features() -> dict[str, dict]:
    return {r["key"]: r for r in read_jsonl(RUN / "data/features.jsonl")}


# ---------------------------------------------------------------- diagnose
def diagnose() -> None:
    feats = load_features()
    groups = defaultdict(list)
    for r in read_jsonl(RUN / "data/graded.jsonl"):
        if r["split"] == "validation":
            groups[r["group_id"]].append(r)
    signals = {
        "length_ratio": lambda r: len(r["candidate"].split()) / max(1, len(r["original"].split())),
        "acceptability": lambda r: feats[key(r["original"], r["candidate"])]["acceptability"],
        "nli_entailment": lambda r: feats[key(r["original"], r["candidate"])]["entailment"],
    }
    result = {}
    for name, f in signals.items():
        wins, total = 0, 0
        for members in groups.values():
            for a, b in combinations(members, 2):
                if a["target"] == b["target"]:
                    continue
                hi, lo = (a, b) if a["target"] > b["target"] else (b, a)
                d = f(hi) - f(lo)
                if d != 0:
                    wins += d > 0
                    total += 1
        result[name] = {"pairwise_accuracy": wins / total, "pairs": total}
    result["length_ratio_either_direction"] = max(result["length_ratio"]["pairwise_accuracy"], 1 - result["length_ratio"]["pairwise_accuracy"])
    result["stop"] = result["length_ratio_either_direction"] >= 0.80 or result["acceptability"]["pairwise_accuracy"] >= 0.80
    atomic_json(RUN / "diagnostics/shortcut.json", result)
    print(json.dumps(result, indent=2))


# ---------------------------------------------------------------- model
def make_model(snapshot: str, use_nli: bool):
    import torch
    from transformers import AutoModel

    class Scorer(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = AutoModel.from_pretrained(snapshot, local_files_only=True)
            hidden = self.encoder.config.hidden_size
            self.use_nli = use_nli
            self.head = torch.nn.Sequential(torch.nn.Dropout(0.1), torch.nn.Linear(hidden + (3 if use_nli else 0), 1))

        def forward(self, input_ids, attention_mask, nli=None, token_type_ids=None):
            pooled = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state[:, 0]
            if self.use_nli:
                pooled = torch.cat([pooled, nli.to(pooled.dtype)], dim=-1)
            return self.head(pooled).squeeze(-1)

    return Scorer()


def encode(tokenizer, rows, feats, use_nli, device):
    import torch
    enc = tokenizer([r["original"] for r in rows], [r["candidate"] for r in rows], padding=True, truncation=True,
                    max_length=256, return_tensors="pt")
    batch = {"input_ids": enc["input_ids"].to(device), "attention_mask": enc["attention_mask"].to(device)}
    if use_nli:
        batch["nli"] = torch.tensor([[feats[key(r["original"], r["candidate"])][k] for k in NLI_KEYS] for r in rows], device=device)
    return batch


def predict_rows(model, tokenizer, rows, feats, use_nli, device, batch_size=64) -> list[float]:
    import torch
    model.eval()
    out = []
    with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.bfloat16):
        for i in range(0, len(rows), batch_size):
            out += model(**encode(tokenizer, rows[i:i + batch_size], feats, use_nli, device)).float().sigmoid().cpu().tolist()
    return out


def validation_score(rows, preds) -> dict:
    from scipy.stats import spearmanr
    rho = float(spearmanr(preds, [r["target"] for r in rows]).statistic)
    order = {"clean": 3, "original_copy": 3, "neutral_trim": 3, "mild_loss": 2, "major_loss": 1, "contradiction": 0}
    groups = defaultdict(list)
    for r, p in zip(rows, preds):
        groups[r["group_id"]].append((order[r["level"]], p))
    wins = total = 0
    for members in groups.values():
        for (la, pa), (lb, pb) in combinations(members, 2):
            if abs(la - lb) == 1:
                wins += (pa > pb) == (la > lb)
                total += 1
    return {"spearman": rho, "adjacent_pairwise": wins / total if total else float("nan")}


# ---------------------------------------------------------------- train
def train(arm: str, lr: float, seed: int, model_config: Path, epochs: int, groups_per_batch: int) -> None:
    import torch
    from torch.nn import functional as F
    from transformers import AutoTokenizer
    data_name, use_nli = ARMS[arm]
    cfg = json.loads(model_config.read_text())
    snapshot = str(ROOT / cfg["snapshot_path"]) if not Path(cfg["snapshot_path"]).is_absolute() else cfg["snapshot_path"]
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    device = torch.device("cuda")
    feats = load_features()
    rows = list(read_jsonl(RUN / f"data/{data_name}.jsonl"))
    train_groups = defaultdict(list)
    for r in rows:
        if r["split"] == "train":
            train_groups[r["group_id"]].append(r)
    val_rows = [r for r in rows if r["split"] == "validation"]
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
    model = make_model(snapshot, use_nli).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    out_dir = RUN / f"training/{arm}/{cfg['model_name'].split('/')[-1]}/lr_{lr}/seed_{seed}"
    out_dir.mkdir(parents=True, exist_ok=True)
    ids = sorted(train_groups)
    history, best = [], None
    for epoch in range(1, epochs + 1):
        model.train()
        random.Random(seed + epoch).shuffle(ids)
        losses = []
        for i in range(0, len(ids), groups_per_batch):
            batch_rows, spans = [], []
            for gid in ids[i:i + groups_per_batch]:
                spans.append((len(batch_rows), len(batch_rows) + len(train_groups[gid])))
                batch_rows += train_groups[gid]
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                scores = model(**encode(tokenizer, batch_rows, feats, use_nli, device)).float().sigmoid()
            targets = torch.tensor([r["target"] for r in batch_rows], device=device)
            loss = F.mse_loss(scores, targets)
            rank_terms = []
            for s, e in spans:
                for a, b in combinations(range(s, e), 2):
                    diff = targets[a] - targets[b]
                    if diff != 0:
                        hi, lo = (a, b) if diff > 0 else (b, a)
                        rank_terms.append(F.relu(0.2 * diff.abs() - (scores[hi] - scores[lo])))
            if rank_terms:
                loss = loss + torch.stack(rank_terms).mean()
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            losses.append(float(loss))
        val = validation_score(val_rows, predict_rows(model, tokenizer, val_rows, feats, use_nli, device))
        history.append({"epoch": epoch, "train_loss": float(np.mean(losses)), **val})
        score = (val["spearman"], val["adjacent_pairwise"])
        if best is None or score > best:
            best = score
            torch.save(model.state_dict(), out_dir / "model.pt")
            tokenizer.save_pretrained(out_dir / "tokenizer")
    atomic_json(out_dir / "run.json", {"arm": arm, "data": data_name, "use_nli": use_nli, "model_name": cfg["model_name"],
                                       "snapshot": snapshot, "lr": lr, "seed": seed, "best_validation_spearman": best[0],
                                       "best_validation_adjacent_pairwise": best[1], "history": history})


# ---------------------------------------------------------------- evaluate
def evaluate(reps: int) -> None:
    import torch
    from transformers import AutoTokenizer
    from run_evaluation import BASELINES, bootstrap, load_baselines
    device = torch.device("cuda")
    feats = load_features()
    baselines = load_baselines(ROOT / "phase7_feats_training/runs/axis_validation_v1/baselines/predictions")
    v1 = json.loads((ROOT / "phase7_feats_training/runs/axis_validation_v1/evaluation/MEANING/results.json").read_text())
    v1_scores = {}
    for name in ("simplicity_da", "human_likert", "simpeval_2022"):
        for r in json.loads((ROOT / f"phase7_feats_training/runs/axis_validation_v1/evaluation/MEANING/{name}_scored.json").read_text()):
            v1_scores[r["evaluation_id"]] = r["model"]
    results = {"v1_selection": v1["selection"]["chosen"]}
    for arm, (data_name, use_nli) in ARMS.items():
        runs = defaultdict(list)
        for path in (RUN / f"training/{arm}").glob("*/lr_*/seed_*/run.json"):
            run = json.loads(path.read_text())
            runs[(path.parts[-4], path.parts[-3])].append({**run, "dir": path.parent})
        if not runs:
            continue
        sel_key = max(runs, key=lambda k: (np.mean([r["best_validation_spearman"] for r in runs[k]]),
                                           np.mean([r["best_validation_adjacent_pairwise"] for r in runs[k]])))
        chosen = runs[sel_key]
        table = {f"{m}/{lr}": {"seeds": len(r), "val_spearman": float(np.mean([x["best_validation_spearman"] for x in r])),
                               "val_adjacent": float(np.mean([x["best_validation_adjacent_pairwise"] for x in r]))}
                 for (m, lr), r in runs.items()}
        out = {"selection": {"chosen": "/".join(sel_key), "table": table}}
        models = []
        for run in chosen:
            model = make_model(run["snapshot"], use_nli).to(device)
            model.load_state_dict(torch.load(run["dir"] / "model.pt", map_location=device))
            models.append((model, AutoTokenizer.from_pretrained(run["dir"] / "tokenizer", local_files_only=True)))
        score_rows = lambda rows: list(np.mean([predict_rows(m, t, rows, feats, use_nli, device) for m, t in models], axis=0))
        for name in ("simplicity_da", "human_likert", "simpeval_2022"):
            rows = [dict(r, human_score=float(r["human_score"])) for r in read_jsonl(V1_EVAL / f"{name}.jsonl")]
            for r, s in zip(rows, score_rows(rows)):
                r["model"] = s
                r["v1_model"] = v1_scores[r["evaluation_id"]]
                r.update(baselines.get(r["evaluation_id"], {}))
            fields = ["model", "v1_model"] + [f for f in BASELINES if all(f in r for r in rows)]
            per = {f: bootstrap(rows, f, None, reps, 20260930) for f in fields}
            entry = {"spearman": per,
                     "model_minus_nli": bootstrap(rows, "model", "nli_bidirectional_entailment", reps, 20260930),
                     "model_minus_v1": bootstrap(rows, "model", "v1_model", reps, 20260930)}
            if name == "simplicity_da":
                from scipy.stats import pearsonr
                systems = defaultdict(list)
                for r in rows:
                    systems[r["system"]].append(r)
                entry["system_level_pearson"] = {f: float(pearsonr([np.mean([x[f] for x in v]) for v in systems.values()],
                                                                   [np.mean([x["human_score"] for x in v]) for v in systems.values()]).statistic)
                                                 for f in fields}
            out[name] = entry
        heldout = [r for n in ("heldout_v2", "heldout_meaning_v21") for r in read_jsonl(V1_EVAL / f"{n}.jsonl")
                   if r["axis"] == "MEANING" and str(r.get("included")) == "True"]
        clean = score_rows([{"original": r["original"], "candidate": r["clean"]} for r in heldout])
        degraded = score_rows([{"original": r["original"], "candidate": r["degraded"]} for r in heldout])
        out["heldout_pairwise"] = {"n": len(heldout), "accuracy": float(np.mean([c > d for c, d in zip(clean, degraded)]))}
        q = {n: {"ci_excludes_0": out[n]["spearman"]["model"]["ci95"][0] > 0,
                 "non_inferior_nli": out[n]["model_minus_nli"]["ci95"][0] > -0.05,
                 "beats_nli": out[n]["model_minus_nli"]["ci95"][0] > 0,
                 "beats_v1": out[n]["model_minus_v1"]["ci95"][0] > 0,
                 "worse_than_v1": out[n]["model_minus_v1"]["ci95"][1] < 0} for n in ("simplicity_da", "human_likert")}
        out["Q1_pass"] = all(v["ci_excludes_0"] and v["non_inferior_nli"] for v in q.values())
        out["Q2_pass"] = any(v["beats_nli"] for v in q.values())
        out["Q4_pass"] = any(v["beats_v1"] for v in q.values()) and not any(v["worse_than_v1"] for v in q.values())
        out["criteria"] = q
        results[arm] = out
        del models
        torch.cuda.empty_cache()
    atomic_json(RUN / "evaluation/results.json", results)
    print(json.dumps({a: {k: r[k] for k in ("Q1_pass", "Q2_pass", "Q4_pass")} | {"chosen": r["selection"]["chosen"]}
                      for a, r in results.items() if isinstance(r, dict) and "Q1_pass" in r}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "features", "diagnose", "train", "evaluate"))
    parser.add_argument("--arm", choices=tuple(ARMS))
    parser.add_argument("--lr", type=float)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--model-config", type=Path, default=ROOT / "phase7_feats_training/configs/models/deberta_v3_base.json")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--groups-per-batch", type=int, default=8)
    parser.add_argument("--reps", type=int, default=10000)
    args = parser.parse_args()
    if args.command == "build":
        build()
    elif args.command == "features":
        features()
    elif args.command == "diagnose":
        diagnose()
    elif args.command == "train":
        train(args.arm, args.lr, args.seed, args.model_config, args.epochs, args.groups_per_batch)
    else:
        evaluate(args.reps)


if __name__ == "__main__":
    main()
