#!/usr/bin/env python3
"""Build a Spanish or French S1 round from the checked candidates of `runs/s1_<lang>_v1`.

The design follows the English round (`build_s1_round.py`): per axis up to 60 items, graded rank-3 groups where
two edits exist, pairs elsewhere, neutral X/Y/Z labels in random order and a hidden key. Fewer checker-valid
candidates exist outside English, so each axis takes what is available:

| Axis  | Items                                                                              |
|-------|------------------------------------------------------------------------------------|
| OMIT  | graded groups first, then pairs                                                     |
| SYN   | graded groups up to half, then pairs                                                |
| EXPL  | pairs                                                                               |
| MOD   | graded groups first, then fronting-only pairs from groups whose reorder failed      |
| ILLOC | pairs, imperative and hedge operations interleaved                                  |

All displayed texts get the same spacing (`uniform_spacing`), so typography cannot reveal the degraded version.
Controls are identical pairs (the expected answer is Same). No previously validated degradation exists in these
languages, so there are no known-valid controls.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.annotation.build_s1_round import item
from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl
from phase6_degraded_corpus.src.reporting.build_mmi_v3_review import selected_text

SEED = 20261021
AXES = ("OMIT", "SYN", "EXPL", "MOD", "ILLOC")


def uniform_spacing(text: str, spaced_high: bool = False) -> str:
    """Pre-tokenized sources (CLEAR: "en cours , et", "d' évaluation") would set clean texts apart from LLM
    rewrites, so every displayed text gets the same spacing; French high punctuation follows the clean text."""
    text = re.sub(r"\s+([,.)\]])", r"\1", text)
    text = re.sub(r"([(\[])\s+", r"\1", text)
    text = re.sub(r"(\w['’])\s+(?=\w)", r"\1", text)
    text = re.sub(r"\s+([;:!?])", r"\1", text)
    if spaced_high:
        text = re.sub(r"(?<=\S)([;:!?])", r" \1", text)
    return re.sub(r"\s+", " ", text).strip()


def displayed(pair: tuple[dict, dict]) -> tuple[dict, dict]:
    public, key = pair
    clean = public["versions"][max(key["levels"], key=key["levels"].get)]
    spaced = bool(re.search(r"\w [;:!?]", clean))
    public = {**public, "original": uniform_spacing(public["original"], spaced),
              "versions": {k: uniform_spacing(v, spaced) for k, v in public["versions"].items()}}
    if len(set(public["versions"].values())) < len(public["versions"]):
        raise RuntimeError(f"versions differ only in spacing: {key['canonical_pair_id']}")
    return public, key


def ordered(rows: list[dict], tag: str) -> list[dict]:
    return sorted(rows, key=lambda r: stable_key(SEED, f"{tag}:{r['canonical_pair_id']}"))


def graded_items(groups: list[dict], axis: str, limit: int) -> list[tuple[dict, dict]]:
    out = []
    for g in ordered([g for g in groups if g["target_axis"] == axis and g["valid"]], f"{axis}:graded")[:limit]:
        m = g["mild_version"]
        mild_op = g["versions"][m].get("operation", {"A": "site_a", "B": "site_b"}[m])
        out.append(item(axis, g, [(1.0, "clean", g["clean_simplification"]),
                                  (0.5, mild_op, g["versions"][m]["degraded"]),
                                  (0.0, g["versions"]["AB"].get("operation", "both"), g["versions"]["AB"]["degraded"])], "rank3"))
    return out


def rule_pairs(pairs: list[dict], axis: str, limit: int) -> list[tuple[dict, dict]]:
    out = []
    for r in ordered([r for r in pairs if r["target_axis"] == axis and r["valid"]], f"{axis}:pairs")[:limit]:
        op = (r.get("rule_output") or {}).get("expl_pattern", axis.casefold())
        out.append(item(axis, r, [(1.0, "clean", r["clean_simplification"]), (0.0, op, r["degraded_simplification"])], "pair"))
    return out


def mod_pairs(fronting: list[dict], used: set[str], limit: int) -> list[tuple[dict, dict]]:
    rows = [r for r in fronting if r["canonical_pair_id"] not in used and selected_text(r)]
    return [item("MOD", r, [(1.0, "clean", r["clean_simplification"]), (0.0, r["operation"], selected_text(r))], "pair")
            for r in ordered(rows, "MOD:pairs")[:limit]]


def illoc_pairs(rows: list[dict], limit: int) -> list[tuple[dict, dict]]:
    by_op = defaultdict(list)
    for r in rows:
        if selected_text(r):
            by_op[r["operation"]].append(r)
    queues = {op: ordered(v, f"ILLOC:{op}") for op, v in by_op.items()}
    chosen, ops = [], sorted(queues)
    while len(chosen) < limit and any(queues.values()):
        for op in ops:
            if queues[op] and len(chosen) < limit:
                chosen.append(queues[op].pop(0))
    return [item("ILLOC", r, [(1.0, "clean", r["clean_simplification"]), (0.0, r["operation"], selected_text(r))], "pair")
            for r in chosen]


def read(path: Path) -> list[dict]:
    return read_jsonl(path) if path.exists() else []


def build(run: Path, cfg: dict) -> tuple[list[dict], list[dict], dict]:
    lang, counts, share = cfg["language"], cfg["round_counts"], cfg["graded_share"]
    fose_pairs, fose_groups = read(run / "scored/fose_pairs.jsonl"), read(run / "scored/fose_groups.jsonl")
    mod_groups, fronting, illoc = read(run / "scored/mod_groups.jsonl"), read(run / "scored/mod_fronting.jsonl"), read(run / "scored/illoc.jsonl")
    items = []
    for axis in ("OMIT", "SYN"):
        graded = graded_items(fose_groups, axis, int(counts[axis] * share[axis]))
        items += graded + rule_pairs(fose_pairs, axis, counts[axis] - len(graded))
    items += rule_pairs(fose_pairs, "EXPL", counts["EXPL"])
    mod = graded_items(mod_groups, "MOD", counts["MOD"])
    used = {k["canonical_pair_id"] for _, k in mod}
    items += mod + mod_pairs(fronting, used, counts["MOD"] - len(mod))
    items += illoc_pairs(illoc, counts["ILLOC"])
    items = [displayed(pair) for pair in items]
    originals = Counter(k["canonical_original_id"] for _, k in items)
    if items and max(originals.values()) > 1:
        raise RuntimeError("an original appears in more than one item")
    items.sort(key=lambda pk: stable_key(SEED, f"shuffle:{pk[1]['axis']}:{pk[1]['canonical_pair_id']}"))
    prefix = lang.upper()
    public, key = [], []
    for i, (p, k) in enumerate(items, 1):
        case = f"{prefix}-S{i:03d}"
        public.append({"case_id": case, "language": lang, **p}); key.append({"case_id": case, "language": lang, **k})
    summary = {"items": dict(Counter(f"{k['axis']}/{k['format']}" for k in key)), "target_per_axis": counts,
               "available": {"fose_pairs_valid": dict(Counter(r["target_axis"] for r in fose_pairs if r["valid"])),
                             "fose_groups_valid": dict(Counter(g["target_axis"] for g in fose_groups if g["valid"])),
                             "mod_groups_valid": sum(g["valid"] for g in mod_groups),
                             "mod_fronting_valid": sum(bool(selected_text(r)) for r in fronting),
                             "illoc_valid": dict(Counter(r["operation"] for r in illoc if selected_text(r)))}}
    return public, key, summary


def controls(run: Path, key: list[dict], lang: str, count: int) -> tuple[list[dict], list[dict]]:
    """Identical pairs from clean simplifications no item uses, on the axes the round contains."""
    used = {k["canonical_original_id"] for k in key}
    scores = {r["canonical_pair_id"]: r for r in read(run / "pools/clean_quality_scores.jsonl")}
    tau = json.loads((run / "checker_config.json").read_text())["tau_accept"]
    pool = [r for r in read(run / "pools/structural_candidates.jsonl")
            if r["canonical_original_id"] not in used and scores.get(r["canonical_pair_id"], {}).get("acceptability", -1e9) >= tau]
    axes = sorted({k["axis"] for k in key}) or list(AXES)
    public, hidden = [], []
    for i, r in enumerate(ordered(pool, "controls")[:count], 1):
        case = f"{lang.upper()}-C{i:03d}"
        spaced = bool(re.search(r"\w [;:!?]", r["clean_simplification"]))
        text = uniform_spacing(r["clean_simplification"], spaced)
        public.append({"case_id": case, "language": lang, "axis": axes[(i - 1) % len(axes)], "format": "pair",
                       "original": uniform_spacing(r["original"], spaced), "versions": {"X": text, "Y": text}})
        hidden.append({"case_id": case, "control_kind": "identical", "expected": "Same", "source_id": r["canonical_original_id"]})
    return public, hidden


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--language", choices=("es", "fr"), required=True)
    args = p.parse_args()
    root = Path("phase6_degraded_corpus/runs")
    run, out = root / f"s1_{args.language}_v1", root / f"annotation_{args.language}_v1"
    cfg = json.loads((run / "checker_config.json").read_text(encoding="utf-8"))
    public, key, summary = build(run, cfg)
    ctrl, ctrl_key = controls(run, key, args.language, max(6, round(len(public) * 0.1)))
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "s1_items.jsonl", public)
    (out / "s1_key.json").write_text(json.dumps(key, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    write_jsonl(out / "s1_controls.jsonl", ctrl)
    (out / "s1_controls_key.json").write_text(json.dumps(ctrl_key, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    summary["controls"] = len(ctrl)
    (out / "build_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
