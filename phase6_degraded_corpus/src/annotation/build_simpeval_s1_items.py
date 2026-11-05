#!/usr/bin/env python3
"""S1 rank-3 items from SimpEval-2022 (English): real system outputs, judged per FEATS axis.

Two steps (both CPU):

`prepare` writes the 180 pairs (60 originals x 3 versions) in the Phase 2b consolidated schema, as input for the
four Phase 3a strategy classifiers (experiment `simpeval2022_s1_v1`). Versions per original: the better human
simplification (higher mean of rating_1..3 between Human 1 and Human 2; tie -> Human 1), GPT-3-few-shot and Muss.

`build` reads the four models' predictions after the GPU job and writes `items.jsonl`, `key.json`, `report.json`:
- a strategy is confirmed for a pair when >= 2 of the 4 models predict it (labels are non-exclusive);
- the human version (the best rated) is the reference, the two system outputs are judged against it: the item axis
  is a FEATS axis (SYN, MOD, EXPL, OMIT; COMP and SYNT have none) confirmed in the human version, the one most models
  predict; ties go to the axis the system versions share least, then to the axis with fewer items so far
  (originals in id order), then to the order OMIT, SYN, MOD, EXPL;
- otherwise ILLOC when the human simplification hosts a direct act (`illoc_host`, lang en), else MEANING and
  FLUENCY alternately, in the order of a stable hash of the original id.
Public items show only neutral labels X/Y/Z; systems, ratings and the source dataset live only in the key.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable

from phase6_degraded_corpus.src.annotation.build_s1_multilingual import displayed
from phase6_degraded_corpus.src.annotation.build_s1_round import item
from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl

SEED = 20261105
SOURCE = "simpeval_2022"
CSV_PATH = Path("phase6_degraded_corpus/runs/mmi_en_v2/pools/evaluation_sources/lens_heineman/data/simpeval_2022.csv")
RUN = Path("phase6_degraded_corpus/runs/simpeval2022_s1_v1")
INPUT_FILE = RUN / "phase3a_input/en/feats_consolidated.jsonl"
PHASE3A_RUN = Path("phase3a_strategy_detection/runs/2026-11-05_simpeval2022_s1_v1")
HUMANS = ("Human 1 Writing", "Human 2 Writing")
MACHINES = ("GPT-3-few-shot", "Muss")
MODELS = ("gemma3_12b_pairwise_qlora", "qwen2p5_7b_pairwise_qlora", "xlmr_large_focal", "multilingual_e5_large_bce")
STRATEGY_AXIS = {"SYN": "SYN", "MOD": "MOD", "EXPL": "EXPL", "OMIT": "OMIT"}  # COMP, SYNT: no axis
AXIS_ORDER = ("OMIT", "SYN", "MOD", "EXPL")
MIN_MODELS = 2


def slug(system: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", system.casefold()).strip("-")


def pair_id(original_id: str, system: str) -> str:
    return f"pair:en:simpeval2022:{original_id}:{slug(system)}"


def mean_rating(row: dict) -> float:
    return sum(float(row[f"rating_{i}"]) for i in (1, 2, 3)) / 3


def select_versions(rows: list[dict]) -> dict[str, list[dict]]:
    """original_id -> [human, GPT-3-few-shot, Muss], each {system, text, mean_rating, role, pair_id, original}."""
    by: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in rows:
        if r["system"] in by[r["original_id"]]:
            raise ValueError(f"duplicate row: {r['original_id']} {r['system']}")
        by[r["original_id"]][r["system"]] = r
    out = {}
    for oid in sorted(by, key=lambda v: (int(v) if v.isdigit() else 10**9, v)):
        systems = by[oid]
        missing = [s for s in HUMANS + MACHINES if s not in systems]
        if missing:
            raise ValueError(f"original {oid} lacks {missing}")
        h1, h2 = (systems[s] for s in HUMANS)
        human = h1 if mean_rating(h1) >= mean_rating(h2) else h2
        chosen = [(human, "human")] + [(systems[s], "machine") for s in MACHINES]
        out[oid] = [{"system": r["system"], "role": role, "text": r["generation"].strip(), "original": r["original"].strip(),
                     "mean_rating": round(mean_rating(r), 4), "pair_id": pair_id(oid, r["system"])} for r, role in chosen]
    return out


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def phase3a_records(selected: dict[str, list[dict]]) -> list[dict]:
    """Phase 2b consolidated rows (id == canonical_pair_id, so the runner's canonical check passes)."""
    out = []
    for oid, versions in selected.items():
        for v in versions:
            orig_sha = hashlib.sha256(v["original"].encode()).hexdigest()
            out.append({
                "id": v["pair_id"], "canonical_pair_id": v["pair_id"], "language": "en",
                "original_id": f"original:en:simpeval2022:{oid}", "canonical_original_id": f"original:en:simpeval2022:{oid}",
                "original": v["original"], "original_raw": v["original"], "original_raw_sha256": orig_sha,
                "simple": v["text"], "simple_raw": v["text"], "simple_raw_sha256": hashlib.sha256(v["text"].encode()).hexdigest(),
                "corpora": [{"corpus": "SimpEval_2022", "source": "SimpEval"}], "sources": ["SimpEval"],
                "provenance": [{"source": "SimpEval", "corpus": "SimpEval_2022", "original_id": oid, "system": v["system"]}],
                "upstream_splits": ["test"], "partially_retained": False, "repaired_duplicate_of": None,
                "text_repaired": False, "text_repairs": [],
            })
    return out


def confirmed(pred_paths: dict[str, Path], min_models: int = MIN_MODELS) -> dict[str, dict[str, list[str]]]:
    """pair_id -> {strategy code: supporting models}, only codes with >= min_models votes (as build_strategy_consensus)."""
    votes: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    seen: dict[str, set[str]] = defaultdict(set)
    for model, path in pred_paths.items():
        for r in read_jsonl(path):
            seen[model].add(r["canonical_pair_id"])
            votes[r["canonical_pair_id"]]  # pairs without any predicted code still count as covered
            for code in r["predicted_codes"]:
                votes[r["canonical_pair_id"]][code].append(model)
    sizes = {m: len(s) for m, s in seen.items()}
    if len(set(sizes.values())) > 1:
        raise ValueError(f"models cover different pair counts: {sizes}")
    return {p: {c: sorted(ms) for c, ms in sorted(by.items()) if len(ms) >= min_models} for p, by in votes.items()}


def hash_order(oid: str) -> str:
    return stable_key(SEED, f"fallback:{oid}")


def choose_axes(selected: dict[str, list[dict]], strategies: dict[str, dict[str, list[str]]],
                hosts_act: Callable[[str], bool]) -> dict[str, tuple[str, str]]:
    """original_id -> (axis, reason). The human version (the best rated) is the reference: the axis is a strategy
    confirmed in it, so the item asks how well each version did what the sentence needed."""
    out: dict[str, tuple[str, str]] = {}
    assigned: Counter = Counter()
    fallback = []
    for oid, versions in selected.items():
        human = strategies.get(versions[0]["pair_id"], {})
        votes = {STRATEGY_AXIS[c]: len(ms) for c, ms in human.items() if c in STRATEGY_AXIS}
        if votes:
            others = [{STRATEGY_AXIS[c] for c in strategies.get(v["pair_id"], {}) if c in STRATEGY_AXIS} for v in versions[1:]]
            shared = {a: sum(a in s for s in others) for a in votes}
            # most models first; then the strategy the machine versions share least (it separates them from the
            # reference); then the axis with fewer items so far; then the order OMIT, SYN, MOD, EXPL
            axis = min(votes, key=lambda a: (-votes[a], shared[a], assigned[a], AXIS_ORDER.index(a)))
            out[oid] = (axis, f"human version: {votes[axis]}/4 models; in {shared[axis]}/2 machine versions")
            assigned[axis] += 1
        elif hosts_act(versions[0]["text"]):
            out[oid] = ("ILLOC", "no strategy axis in the human version; it hosts a direct act")
        else:
            fallback.append(oid)
    for i, oid in enumerate(sorted(fallback, key=hash_order)):
        out[oid] = (("MEANING", "FLUENCY")[i % 2], "no strategy axis in the human version and no direct act; "
                    "MEANING/FLUENCY alternate by stable hash of original_id")
    return out


def build(selected: dict[str, list[dict]], strategies: dict[str, dict[str, list[str]]],
          hosts_act: Callable[[str], bool]) -> tuple[list[dict], list[dict], dict]:
    axes = choose_axes(selected, strategies, hosts_act)
    built = []
    for n, (oid, versions) in enumerate(selected.items(), 1):
        case_id = f"EN-SE{n:03d}"
        axis, reason = axes[oid]
        human = versions[0]
        row = {"clean_simplification": human["text"], "original": human["original"], "canonical_pair_id": human["pair_id"],
               "canonical_original_id": f"original:en:simpeval2022:{oid}", "corpus": SOURCE}
        # Levels are the mean human ratings scaled to [0, 1]; the human version is flagged highest so `displayed`
        # picks its spacing (ratings stay unchanged in the key).
        vs = [(2.0 if v["role"] == "human" else v["mean_rating"] / 100, v["system"], v["text"]) for v in versions]
        public, key = displayed(item(axis, row, vs, "rank3"))
        by_system = {v["system"]: v for v in versions}
        labels = key["operations"]
        key = {**key, "case_id": case_id, "language": "en", "source": SOURCE, "original_id": oid,
               "systems": labels, "levels": {lab: round(by_system[s]["mean_rating"] / 100, 4) for lab, s in labels.items()},
               "mean_human_rating": {lab: by_system[s]["mean_rating"] for lab, s in labels.items()},
               "pair_ids": {lab: by_system[s]["pair_id"] for lab, s in labels.items()},
               "confirmed_strategies": {lab: strategies.get(by_system[s]["pair_id"], {}) for lab, s in labels.items()},
               "human_label": next(lab for lab, s in labels.items() if s == human["system"]),
               "axis_reason": reason}
        built.append(({"case_id": case_id, "language": "en", **public}, key))
    built.sort(key=lambda pk: stable_key(SEED, f"shuffle:{pk[1]['case_id']}"))
    public, key = [p for p, _ in built], [k for _, k in built]
    report = {"source": SOURCE, "items": len(public), "by_axis": dict(sorted(Counter(k["axis"] for k in key).items())),
              "human_choice": dict(Counter(v[0]["system"] for v in selected.values())),
              "pairs_with_confirmed_strategy": sum(1 for v in selected.values() for x in v if strategies.get(x["pair_id"])),
              "by_strategy": dict(sorted(Counter(c for v in selected.values() for x in v
                                                 for c in strategies.get(x["pair_id"], {})).items())),
              "by_reason": dict(Counter(k["axis_reason"].split(";")[0] for k in key)),
              "min_models": MIN_MODELS, "seed": SEED}
    return public, key, report


def illoc_checker() -> Callable[[str], bool]:
    from phase6_degraded_corpus.src.common.languages import load_nlp
    from phase6_degraded_corpus.src.selection.select_multilingual_pools import illoc_host
    nlp = load_nlp("en", disable=("ner",))
    return lambda text: illoc_host(text, "en", nlp) is not None


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("step", choices=("prepare", "build"))
    p.add_argument("--csv", type=Path, default=CSV_PATH)
    p.add_argument("--phase3a-run", type=Path, default=PHASE3A_RUN)
    p.add_argument("--out", type=Path, default=RUN)
    args = p.parse_args()
    selected = select_versions(read_csv(args.csv))
    if args.step == "prepare":
        records = phase3a_records(selected)
        path = args.out / "phase3a_input/en/feats_consolidated.jsonl"
        write_jsonl(path, records)
        summary = {"pairs": len(records), "originals": len(selected),
                   "human_choice": dict(Counter(v[0]["system"] for v in selected.values())),
                   "human_choice_by_original": {oid: v[0]["system"] for oid, v in selected.items()}}
        (args.out / "selection_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps({k: v for k, v in summary.items() if k != "human_choice_by_original"}, indent=2))
        return
    paths = {m: args.phase3a_run / f"models/{m}/predictions/en/feats_consolidated.jsonl" for m in MODELS}
    strategies = confirmed(paths)
    expected = {v["pair_id"] for vs in selected.values() for v in vs}
    if missing := expected - set(strategies):
        raise ValueError(f"{len(missing)} pairs lack predictions, e.g. {sorted(missing)[:3]}")
    public, key, report = build(selected, strategies, illoc_checker())
    args.out.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out / "items.jsonl", public)
    (args.out / "key.json").write_text(json.dumps(key, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (args.out / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
