#!/usr/bin/env python3
"""Graded FLUENCY groups (FOSE plan §9): the FOSE v1 error rules applied 1, 2 or 3+ times.

Levels: original_copy / clean / also_trim = 1.0; minor (one determiner drop or preposition
swap) = 0.67; major (one agreement or word-order error, or two minor) = 0.33; severe
(three or more errors) = 0.0. Negatives are NOT selected with the acceptability model,
which is the baseline FLUENCY must beat (MEANING lesson: do not train on the baseline's own
decisions). The only check is that meaning is kept (NLI entailment both ways >= 0.5).

Stages: `candidates` (CPU) -> `score` (GPU, NLI) -> `select` (CPU).
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl
from phase6_degraded_corpus.src.evaluation.materialize_mmi_full import split_for
from phase6_degraded_corpus.src.generation.generate_fose_rules import AGREEMENT, PREPOSITIONS, fluency_sites
from phase6_degraded_corpus.src.planning.plan_mmi_operations import fix_articles
from phase6_degraded_corpus.src.generation.generate_meaning_graded import neutral_trims

TARGETS = {"original_copy": 1.0, "clean": 1.0, "also_trim": 1.0, "minor": 0.67, "major": 0.33, "severe": 0.0}
MINOR, MAJOR = ("determiner_drop", "preposition_swap"), ("agreement", "word_order")
LEVEL_PLANS = {"minor": [("minor", 1)], "major": [("major", 1)], "major_two_minor": [("minor", 2)],
               "severe": [("any", 3)]}


def positions(kind: str, site) -> set[int]:
    return set(site) if isinstance(site, tuple) else {site}


def rebuild(values: list[str], spaces: list[str]) -> str:
    """Join tokens with their ORIGINAL whitespace (no detokenizer artifacts such as 'singer - songwriter')."""
    import re
    text = "".join(v + s for v, s in zip(values, spaces) if v is not None)
    return fix_articles(re.sub(r"\s{2,}", " ", text).strip())


def apply_errors(values: list[str], edits: list[tuple[str, object]]) -> list[str | None]:
    values = list(values)
    deletions = []
    for kind, site in edits:
        if kind == "agreement":
            new = AGREEMENT[values[site].casefold()]
            values[site] = new.capitalize() if values[site][0].isupper() else new
        elif kind == "preposition_swap":
            new = PREPOSITIONS[values[site].casefold()]
            values[site] = new.capitalize() if values[site][0].isupper() else new
        elif kind == "word_order":
            a, b = site
            values[a], values[b] = values[b], values[a]
        else:
            deletions.append(site)
    for site in deletions:
        values[site] = None  # keep positions aligned with the whitespace list
    return values


def pick_edits(sites: dict, plan: list[tuple[str, int]], seed: int, pid: str, tag: str) -> list | None:
    """Choose non-overlapping edits deterministically; None if the plan cannot be met."""
    pools = {"minor": [(k, s) for k in MINOR for s in sites[k]], "major": [(k, s) for k in MAJOR for s in sites[k]],
             "any": [(k, s) for k in (*MINOR, *MAJOR) for s in sites[k]]}
    chosen, used = [], set()
    for group, n in plan:
        cands = sorted(pools[group], key=lambda e: stable_key(seed, f"{pid}:{tag}:{e}"))
        kinds_used = Counter()
        for kind, site in cands:
            if len([c for c in chosen if c in pools[group]]) >= n:
                break
            pos = positions(kind, site)
            if pos & used or any(abs(p - q) <= 1 for p in pos for q in used):
                continue
            if group == "any" and kinds_used[kind] >= 2:  # severe: mix error types
                continue
            chosen.append((kind, site)); used |= pos; kinds_used[kind] += 1
        if len([c for c in chosen if c in pools[group]]) < n:
            return None
    return chosen


def candidates(pool: Path, exclude: set[str], seed: int) -> list[dict]:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    rows = [r for r in read_jsonl(pool) if r["canonical_original_id"] not in exclude]
    out = []
    for r in rows:
        clean, pid = r["clean_simplification"], r["canonical_pair_id"]
        doc = nlp(clean)
        values = [t.text for t in doc]
        spaces = [t.whitespace_ for t in doc]
        sites = fluency_sites(clean, nlp)
        members = [{"level": "original_copy", "text": r["original"]}, {"level": "clean", "text": clean}]
        trims = [t for t in neutral_trims(clean) if t["rule"] == "adverb_also"]
        if trims:
            members.append({"level": "also_trim", "text": trims[0]["text"]})
        for name, plan in LEVEL_PLANS.items():
            edits = pick_edits(sites, plan, seed, pid, name)
            if edits:
                level = "major" if name == "major_two_minor" else name
                members.append({"level": level, "rule": name, "edits": [k for k, _ in edits],
                                "text": rebuild(apply_errors(values, edits), spaces)})
        out.append({"canonical_pair_id": pid, "canonical_original_id": r["canonical_original_id"], "corpus": r["corpus"],
                    "split": split_for(r["canonical_original_id"], 20260930, 0.1), "original": r["original"],
                    "clean": clean, "clean_acceptability": float(r["clean_acceptability"]), "members": members})
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("candidates", "score", "select"))
    parser.add_argument("--pool", type=Path, default=Path("phase6_degraded_corpus/runs/fose_en_v1/pools/fluency.jsonl"))
    parser.add_argument("--review-key", type=Path, default=Path("phase6_degraded_corpus/runs/fose_en_v1/audit/review_key.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("phase6_degraded_corpus/runs/fluency_graded_en_v1"))
    parser.add_argument("--pools-config", type=Path, default=Path("phase6_degraded_corpus/configs/experiments/mmi_en_v2_pools.json"))
    parser.add_argument("--seed", type=int, default=20261002)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.stage == "candidates":
        # Pairs already shown to the human reviewer (FOSE v1 audit) are kept out of training.
        exclude = {v["canonical_original_id"] for v in json.loads(args.review_key.read_text()).values()}
        rows = candidates(args.pool, exclude, args.seed)
        write_jsonl(args.out_dir / "candidates.jsonl", rows)
        print(json.dumps({"pairs": len(rows), "excluded_reviewed": len(exclude),
                          "members": dict(Counter(m.get("rule", m["level"]) for r in rows for m in r["members"]))}))
    elif args.stage == "score":
        from phase6_degraded_corpus.src.evaluation.score_mmi_candidates import Checkers
        rows = read_jsonl(args.out_dir / "candidates.jsonl")
        ck = Checkers(json.loads(args.pools_config.read_text()), "cuda")
        flat = [(r, m) for r in rows for m in r["members"] if m["level"] not in {"clean", "original_copy"}]
        fwd = ck.nli_probs([r["clean"] for r, _ in flat], [m["text"] for _, m in flat])
        bwd = ck.nli_probs([m["text"] for _, m in flat], [r["clean"] for r, _ in flat])
        for (r, m), f, b in zip(flat, fwd, bwd):
            m["meaning_kept"] = min(f["entailment"], b["entailment"]) >= 0.5
        write_jsonl(args.out_dir / "scored.jsonl", rows)
    else:
        groups, stats = [], Counter()
        for r in read_jsonl(args.out_dir / "scored.jsonl"):
            members = [dict(m, target_score=TARGETS[m["level"]]) for m in r["members"]
                       if m["level"] in {"clean", "original_copy"} or m.get("meaning_kept")]
            for m in r["members"]:
                stats[f'{m.get("rule", m["level"])}:{"kept" if m["level"] in {"clean", "original_copy"} or m.get("meaning_kept") else "dropped_meaning"}'] += 1
            if len({m["target_score"] for m in members}) >= 2 and len(members) >= 3:
                groups.append({k: r[k] for k in ("canonical_pair_id", "canonical_original_id", "corpus", "split", "original")} | {"members": members})
        stats["groups"] = len(groups)
        write_jsonl(args.out_dir / "groups.jsonl", groups)
        (args.out_dir / "groups_report.json").write_text(json.dumps(dict(sorted(stats.items())), indent=2) + "\n")
        print(json.dumps(dict(sorted(stats.items())), indent=2))


if __name__ == "__main__":
    main()
