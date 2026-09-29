#!/usr/bin/env python3
"""Compare scored MMI configs on the shared split (plan §6.1, §6.3).

Per config × axis × source cell: parse / no-op / copy-original rates on the first sample,
check_pass@1, yield@n, single-edit rate. Per axis: macro (sources weigh equally; cells with
fewer than `--min-cell` rows are shown but excluded) and micro averages. MEANING also gets
an LLM-only table (rule-based number/date rows removed). Configs are compared pairwise on
the same pairs with an exact McNemar test and a bootstrap CI of the yield difference.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl

AXES = ("MEANING", "MOD", "ILLOC")
SOURCES = ("WikiAutoEN", "ASSET", "Wikipedia-Vikidia")
RANKED_ILLOC_OPS = {"assertion_to_question", "assertion_to_directive"}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (centre - half, centre + half)


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def bootstrap_diff(pairs: list[tuple[str, bool, bool]], seed: int = 20260930, reps: int = 10000) -> tuple[float, float, float]:
    clusters: dict[str, list[tuple[bool, bool]]] = defaultdict(list)
    for cluster, a, b in pairs:
        clusters[cluster].append((a, b))
    keys = sorted(clusters)
    rng = random.Random(seed)
    point = sum(a - b for _, a, b in pairs) / len(pairs)
    diffs = []
    for _ in range(reps):
        sample = [item for key in (rng.choice(keys) for _ in keys) for item in clusters[key]]
        diffs.append(sum(a - b for a, b in sample) / len(sample))
    diffs.sort()
    return point, diffs[int(0.025 * reps)], diffs[int(0.975 * reps) - 1]


def rows_for_ranking(rows: list[dict], axis: str, llm_only: bool = False) -> list[dict]:
    out = [r for r in rows if r["target_axis"] == axis]
    if axis == "ILLOC":
        out = [r for r in out if r.get("operation") in RANKED_ILLOC_OPS or r.get("config_id") == "C0"]
    if llm_only:
        out = [r for r in out if r.get("generator_kind") != "rule"]
    return out


def cell_metrics(rows: list[dict]) -> dict:
    n = len(rows)
    if not n:
        return {"n": 0}
    first = [r["candidates"][0] if r["candidates"] else {} for r in rows]
    checks0 = [c.get("checks") or {} for c in first]
    k = sum(r["yield"] for r in rows)
    lo, hi = wilson(k, n)
    return {
        "n": n,
        "parse_rate": sum(c.get("parsed", False) for c in checks0) / n,
        "noop_rate": sum(c.get("parsed", False) and not c.get("not_noop", True) for c in checks0) / n,
        "copy_original_rate": sum(c.get("parsed", False) and not c.get("not_copy_original", True) for c in checks0) / n,
        "check_pass_at_1": sum(r["check_pass_at_1"] for r in rows) / n,
        "yield": k / n, "yield_ci": [lo, hi],
        "single_edit_rate": sum(bool(r.get("single_edit")) for r in rows) / n,
    }


def summarize(scored: dict[str, list[dict]], min_cell: int) -> dict:
    result = {}
    for config, rows in scored.items():
        per_axis = {}
        for axis in AXES:
            for variant in ("end_to_end", "llm_only") if axis == "MEANING" else ("end_to_end",):
                axis_rows = rows_for_ranking(rows, axis, llm_only=variant == "llm_only")
                cells = {src: cell_metrics([r for r in axis_rows if r["corpus"] == src]) for src in SOURCES}
                eligible = [m for m in cells.values() if m["n"] >= min_cell]
                macro = {key: sum(m[key] for m in eligible) / len(eligible)
                         for key in ("yield", "check_pass_at_1", "single_edit_rate", "noop_rate", "copy_original_rate")} if eligible else {}
                per_axis[f"{axis}:{variant}"] = {"cells": cells, "macro": macro, "micro": cell_metrics(axis_rows),
                                                 "macro_sources": [s for s, m in cells.items() if m["n"] >= min_cell]}
        ops = defaultdict(list)
        for r in rows:
            if r["target_axis"] == "ILLOC":
                op = r.get("operation") if r.get("config_id") != "C0" else (
                    r["candidates"][r["selected_index"]].get("matched_operation") if r["selected_index"] is not None else "none")
                ops[op].append(r)
            if r["target_axis"] == "MEANING":
                ops[f'meaning:{r.get("meaning_type")}'].append(r)
        per_axis["by_operation"] = {op: cell_metrics(rs) for op, rs in sorted(ops.items())}
        result[config] = per_axis
    return result


def paired(scored: dict[str, list[dict]], axis: str) -> list[dict]:
    configs = sorted(scored)
    out = []
    for i, a in enumerate(configs):
        for b in configs[i + 1:]:
            ra = {r["canonical_pair_id"]: r for r in rows_for_ranking(scored[a], axis)}
            rb = {r["canonical_pair_id"]: r for r in rows_for_ranking(scored[b], axis)}
            common = sorted(set(ra) & set(rb))
            if not common:
                continue
            triples = [(ra[p]["canonical_original_id"], ra[p]["yield"], rb[p]["yield"]) for p in common]
            b_only = sum(x and not y for _, x, y in triples)
            c_only = sum(y and not x for _, x, y in triples)
            diff, lo, hi = bootstrap_diff(triples)
            out.append({"a": a, "b": b, "n": len(common), "a_only": b_only, "b_only": c_only,
                        "mcnemar_p": mcnemar_exact(b_only, c_only), "diff": diff, "ci": [lo, hi]})
    return out


def pct(x: float) -> str:
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.0f}%"


def render(summary: dict, pairs: dict, finalists: dict, examples: dict, args) -> str:
    configs = sorted(summary)
    lines = [
        "# MMI v2 model comparison (dev, automatic checks)",
        "",
        f"Split: `{args.split}`. Configs: {', '.join(f'`{c}`' for c in configs)}. "
        "These are **automatic** results used to pick finalists (plan §6.3); the winner is decided by the blinded human audit on `heldout` (§6.4).",
        "",
        f"`yield` = share of pairs with at least one candidate passing every axis check (n=4 samples; C0 and C1_greedy have n=1, so for them yield = pass@1). "
        f"Macro averages weigh sources equally and exclude cells with fewer than {args.min_cell} rows. ILLOC ranking uses question + directive only; hedged is reported separately.",
        "",
        "## Finalists per axis",
        "",
        "| Axis | Finalist 1 | Finalist 2 | Basis |",
        "|---|---|---|---|",
    ]
    for axis in AXES:
        f = finalists[axis]
        lines.append(f"| {axis} | `{f[0]}` | `{f[1]}` | macro end-to-end yield, then single-edit rate |")
    for axis in AXES:
        variants = ("end_to_end", "llm_only") if axis == "MEANING" else ("end_to_end",)
        for variant in variants:
            key = f"{axis}:{variant}"
            title = {"end_to_end": "end-to-end (ranking)", "llm_only": "LLM-only (rule number/date rows removed)"}[variant]
            lines += ["", f"## {axis} — {title}", "",
                      "| Config | Macro yield | Micro yield | pass@1 (macro) | single-edit (macro) | no-op (macro) | copy-Original (macro) | " +
                      " | ".join(f"{s} yield [95% CI] (n)" for s in SOURCES) + " |",
                      "|---|---|---|---|---|---|---|" + "---|" * len(SOURCES)]
            for c in configs:
                a = summary[c][key]
                m = a["macro"]
                cells = " | ".join(
                    f"{pct(a['cells'][s].get('yield'))} [{pct(a['cells'][s]['yield_ci'][0])}–{pct(a['cells'][s]['yield_ci'][1])}] ({a['cells'][s]['n']})"
                    if a["cells"][s]["n"] else "—" for s in SOURCES)
                lines.append(f"| `{c}` | **{pct(m.get('yield'))}** | {pct(a['micro'].get('yield'))} | {pct(m.get('check_pass_at_1'))} | "
                             f"{pct(m.get('single_edit_rate'))} | {pct(m.get('noop_rate'))} | {pct(m.get('copy_original_rate'))} | {cells} |")
        lines += ["", f"### {axis} — paired comparisons (yield, same pairs)", "",
                  "| A | B | n | only A valid | only B valid | McNemar p | A−B [95% bootstrap CI] |", "|---|---|---|---|---|---|---|"]
        for p in pairs[axis]:
            lines.append(f"| `{p['a']}` | `{p['b']}` | {p['n']} | {p['a_only']} | {p['b_only']} | {p['mcnemar_p']:.3g} | "
                         f"{100 * p['diff']:+.0f} pp [{100 * p['ci'][0]:+.0f}, {100 * p['ci'][1]:+.0f}] |")
    lines += ["", "## By operation (all sources)", "", "| Operation | " + " | ".join(f"`{c}` yield (n)" for c in configs) + " |",
              "|---|" + "---|" * len(configs)]
    ops = sorted({op for c in configs for op in summary[c]["by_operation"]})
    for op in ops:
        vals = [summary[c]["by_operation"].get(op, {"n": 0}) for c in configs]
        lines.append(f"| {op} | " + " | ".join(f"{pct(v.get('yield'))} ({v['n']})" if v["n"] else "—" for v in vals) + " |")
    lines += ["", "## Examples (selected candidate, or first candidate when none passed)", ""]
    for axis in AXES:
        lines += [f"### {axis}", ""]
        for c in configs:
            lines.append(f"**`{c}`**")
            lines.append("")
            for ex in examples[axis][c]:
                mark = "✅" if ex["valid"] else "❌"
                failed = "" if ex["valid"] else f" — failed: {', '.join(ex['failed']) or 'parse'}"
                lines.append(f"- {mark} *{ex['operation']}* ({ex['corpus']})  \n  Clean: {ex['clean']}  \n  Degraded: {ex['degraded']}{failed}")
            lines.append("")
    return "\n".join(lines) + "\n"


def pick_examples(scored: dict[str, list[dict]], per: int = 4) -> dict:
    out = {axis: {} for axis in AXES}
    for c, rows in scored.items():
        for axis in AXES:
            axis_rows = sorted([r for r in rows if r["target_axis"] == axis], key=lambda r: r["canonical_pair_id"])
            chosen = [r for r in axis_rows if r["yield"]][: per // 2] + [r for r in axis_rows if not r["yield"]][: per - per // 2]
            items = []
            for r in chosen:
                idx = r["selected_index"] if r["selected_index"] is not None else 0
                cand = r["candidates"][idx] if r["candidates"] else {"degraded": None, "checks": {}}
                items.append({"valid": r["yield"], "operation": r.get("operation") or r.get("meaning_type"), "corpus": r["corpus"],
                              "clean": r["clean_simplification"], "degraded": cand.get("degraded"),
                              "failed": [k for k, v in (cand.get("checks") or {}).items() if not v]})
            out[axis][c] = items
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scored-dir", type=Path, required=True)
    parser.add_argument("--split", default="dev")
    parser.add_argument("--min-cell", type=int, default=20)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    scored = {p.stem: read_jsonl(p) for p in sorted(args.scored_dir.glob("*.jsonl"))}
    for c, rows in scored.items():
        for r in rows:
            r.setdefault("config_id", c)
    summary = summarize(scored, args.min_cell)
    pairs = {axis: paired(scored, axis) for axis in AXES}
    finalists = {}
    for axis in AXES:
        key = f"{axis}:end_to_end"
        ranked = sorted(summary, key=lambda c: (-summary[c][key]["macro"].get("yield", 0),
                                                 -summary[c][key]["macro"].get("single_edit_rate", 0), c))
        finalists[axis] = ranked[:2]
    report = render(summary, pairs, finalists, pick_examples(scored), args)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps({"summary": summary, "paired": pairs, "finalists": finalists}, indent=2, sort_keys=True) + "\n")
    print(json.dumps(finalists, indent=2))


if __name__ == "__main__":
    main()
