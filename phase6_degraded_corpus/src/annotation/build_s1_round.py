#!/usr/bin/env python3
"""Build the single blinded S1 round: 60 items per axis, graded groups where levels exist, pairs elsewhere.

| Axis  | Items                                   |
|-------|-----------------------------------------|
| OMIT  | 60 rank-3 groups (1.0 / 0.5 / 0.0)       |
| MOD   | 60 rank-3 groups, half with each mild op |
| SYN   | 30 rank-3 groups + 30 pairs              |
| EXPL  | 60 pairs (two glosses per sentence are too rare for levels) |
| ILLOC | 60 pairs (speech act changes or not)     |

Annotators see the Original and the versions under neutral labels (X, Y, Z) in random order; which one is the
clean simplification is hidden. Levels, operations and pair ids live only in the key.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl
from phase6_degraded_corpus.src.generation.generate_fose_rules import generate_expl, generate_omit, generate_syn

LABELS = "XYZ"
SEED = 20261002
GENERATORS = {"OMIT": generate_omit, "SYN": generate_syn, "EXPL": generate_expl}


def restore_quotes(clean: str, text: str) -> str:
    """LLMs turned "x" into 'x'; put the clean text's double quotes back so style is not a cue."""
    if '"' in clean and '"' not in text:
        return re.sub(r"(?<!\w)'([^']+)'(?!\w)", r'"\1"', text)
    return text


def order(seed: int, key: str, n: int) -> list[int]:
    return sorted(range(n), key=lambda i: stable_key(seed, f"{key}:{i}"))


def pick(rows: list[dict], count: int, tag: str) -> list[dict]:
    rows = sorted(rows, key=lambda r: stable_key(SEED, f"{tag}:{r['canonical_pair_id']}"))
    if len(rows) < count:
        raise RuntimeError(f"{tag}: {len(rows)} available, need {count}")
    return rows[:count]


def item(axis: str, row: dict, versions: list[tuple[float, str, str]], fmt: str) -> tuple[dict, dict]:
    """versions: (level, operation, text). Returns the public item and its key entry."""
    clean = row["clean_simplification"]
    versions = [(lvl, op, restore_quotes(clean, text)) for lvl, op, text in versions]
    perm = order(SEED, f"labels:{axis}:{row['canonical_pair_id']}", len(versions))
    public = {"axis": axis, "format": fmt, "original": row["original"],
              "versions": {LABELS[i]: versions[j][2] for i, j in enumerate(perm)}}
    key = {"axis": axis, "format": fmt, "canonical_pair_id": row["canonical_pair_id"],
           "canonical_original_id": row["canonical_original_id"], "corpus": row.get("corpus"),
           "levels": {LABELS[i]: versions[j][0] for i, j in enumerate(perm)},
           "operations": {LABELS[i]: versions[j][1] for i, j in enumerate(perm)}}
    return public, key


def graded(groups: list[dict], axis: str, count: int, ops: dict[str, str]) -> list[tuple[dict, dict]]:
    valid = [g for g in groups if g["target_axis"] == axis and g["valid"]]
    if axis == "MOD":  # half the groups use each operation as the mild version
        by = defaultdict(list)
        for g in valid:
            by[g["mild_version"]].append(g)
        chosen = pick(by["A"], count // 2, "MOD:A") + pick(by["B"], count - count // 2, "MOD:B")
    else:
        chosen = pick(valid, count, f"{axis}:graded")
    out = []
    for g in chosen:
        m = g["mild_version"]
        out.append(item(axis, g, [(1.0, "clean", g["clean_simplification"]),
                                  (0.5, g["versions"][m].get("operation", ops[m]), g["versions"][m]["degraded"]),
                                  (0.0, g["versions"]["AB"].get("operation", "both"), g["versions"]["AB"]["degraded"])], "rank3"))
    return out


def fose_pairs(axis: str, count: int, sample: list[dict], key: list[dict], pools: dict[str, dict], seed: int) -> list[tuple[dict, dict]]:
    """Re-derive the FOSE v2 review texts from their pool rows, so the quote fix in `detokenize` applies."""
    keys = {k["case_id"]: k for k in key}
    rows = [r for r in sample if r["axis"] == axis]
    out = []
    for r in pick([{**r, "canonical_pair_id": keys[r["case_id"]]["canonical_pair_id"]} for r in rows], count, f"{axis}:pairs"):
        k, pool = keys[r["case_id"]], pools[keys[r["case_id"]]["canonical_pair_id"]]
        result = GENERATORS[axis](pool["original"], pool["clean_simplification"], pool["canonical_pair_id"], seed, pool["eligible_sites"][axis])
        if result is None or re.sub(r"\s", "", result["degraded"]) != re.sub(r"\s", "", r["degraded"]):
            raise RuntimeError(f"{r['case_id']}: rule output changed beyond whitespace")
        op = result.get("expl_pattern", k.get("operation", axis.casefold()))
        out.append(item(axis, pool, [(1.0, "clean", pool["clean_simplification"]), (0.0, op, result["degraded"])], "pair"))
    return out


def mmi_pairs(axis: str, count: int, sample: list[dict], key: list[dict]) -> list[tuple[dict, dict]]:
    keys = {k["case_id"]: k for k in key}
    rows = [{**r, **{f: keys[r["case_id"]][f] for f in ("canonical_pair_id", "canonical_original_id", "corpus")},
             "clean_simplification": r["simplified"]} for r in sample if r["axis"] == axis]
    return [item(axis, r, [(1.0, "clean", r["clean_simplification"]), (0.0, keys[r["case_id"]]["operation"], r["degraded"])], "pair")
            for r in pick(rows, count, f"{axis}:pairs")]


def build(args) -> tuple[list[dict], list[dict]]:
    fose = read_jsonl(args.graded_dir / "fose_groups.jsonl")
    mod = read_jsonl(args.graded_dir / "mod_groups.jsonl")
    fose_sample, fose_key = read_jsonl(args.fose_dir / "review_sample.jsonl"), json.loads((args.fose_dir / "review_key.json").read_text())
    mmi_sample, mmi_key = read_jsonl(args.mmi_dir / "review_sample.jsonl"), json.loads((args.mmi_dir / "review_key.json").read_text())
    pools = {r["canonical_pair_id"]: r for a in ("omit", "syn", "expl") for r in read_jsonl(args.fose_dir / f"pools/{a}.jsonl")}
    seed = json.loads(args.fose_config.read_text())["seed"]
    rule_ops = {"A": "site_a", "B": "site_b"}
    items = (graded(fose, "OMIT", 60, rule_ops) + graded(mod, "MOD", 60, rule_ops) + graded(fose, "SYN", 30, rule_ops)
             + fose_pairs("SYN", 30, fose_sample, fose_key, pools, seed) + fose_pairs("EXPL", 60, fose_sample, fose_key, pools, seed)
             + mmi_pairs("ILLOC", 60, mmi_sample, mmi_key))
    originals = Counter(k["canonical_original_id"] for _, k in items)
    if max(originals.values()) > 1:
        raise RuntimeError("an original appears in more than one item")
    items.sort(key=lambda pk: stable_key(SEED, f"shuffle:{pk[1]['axis']}:{pk[1]['canonical_pair_id']}"))
    public, key = [], []
    for i, (p, k) in enumerate(items, 1):
        case = f"S{i:03d}"
        public.append({"case_id": case, **p}); key.append({"case_id": case, **k})
    return public, key


def main() -> None:
    root = Path("phase6_degraded_corpus/runs")
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--graded-dir", type=Path, default=root / "graded_en_v1")
    p.add_argument("--fose-dir", type=Path, default=root / "fose_en_v2")
    p.add_argument("--mmi-dir", type=Path, default=root / "mmi_en_v3")
    p.add_argument("--fose-config", type=Path, default=Path("phase6_degraded_corpus/configs/experiments/fose_en_v2.json"))
    p.add_argument("--output-dir", type=Path, default=root / "annotation_v1")
    args = p.parse_args()
    public, key = build(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "s1_items.jsonl", public)
    (args.output_dir / "s1_key.json").write_text(json.dumps(key, indent=2, sort_keys=True) + "\n")
    print(json.dumps(dict(Counter(f"{k['axis']}:{k['format']}" for k in key)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
