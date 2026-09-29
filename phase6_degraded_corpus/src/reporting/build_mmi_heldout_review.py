#!/usr/bin/env python3
"""Build the blinded heldout audit file for the finalists (plan §6.3) and score it (§6.4).

`build`: for each axis, take the finalists' scored heldout rows, show the selected candidate
(or the first one when none passed the automatic checks), shuffle all cases of the axis
together, and hide the config. The key (case → config) goes to a private file under runs/.
`score`: read the ticked checkboxes, compute valid rates per config × axis × source, run the
paired tests and apply the decision rule.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import defaultdict
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key
from phase6_degraded_corpus.src.evaluation.analyze_mmi_comparison import SOURCES, bootstrap_diff, mcnemar_exact, wilson

TASK = {
    "MEANING": "exactly one factual change that contradicts the Original; everything else unchanged and fluent",
    "MOD": "two adjacent sentences merged into one; no fact or wording change beyond joining words; grammatical",
    "recombine_split": "two adjacent sentences merged into one; no fact or wording change beyond joining words; grammatical",
    "assertion_to_question": "statement turned into a yes/no question about the same proposition; nothing else changed",
    "assertion_to_directive": "statement turned into an instruction to the reader ('Note that …'); nothing else changed",
    "assertion_to_hedged": "statement made uncertain with one hedge ('might', 'probably'); nothing else changed",
}


def build(args) -> None:
    finalists = json.loads(args.finalists.read_text())["finalists"]
    cases, key = [], {}
    for axis, configs in finalists.items():
        axis_cases = []
        for config in configs:
            for row in read_jsonl(args.scored_dir / f"{config}.jsonl"):
                if row["target_axis"] != axis or row.get("operation") == "assertion_to_hedged":
                    continue
                idx = row["selected_index"] if row.get("selected_index") is not None else 0
                cand = row["candidates"][idx] if row["candidates"] else {}
                axis_cases.append({"axis": axis, "config": config, "row": row, "degraded": cand.get("degraded") or "(no output)"})
        # Identical outputs for the same pair are shown once; the decision counts for every config that produced it.
        merged: dict[tuple[str, str], dict] = {}
        for case in axis_cases:
            slot = (case["row"]["canonical_pair_id"], case["degraded"])
            if slot in merged:
                merged[slot]["configs"].append(case["config"])
            else:
                merged[slot] = {**case, "configs": [case["config"]]}
        axis_cases = sorted(merged.values(), key=lambda c: stable_key(args.seed, f'{c["row"]["canonical_pair_id"]}:{c["degraded"]}'))
        cases += axis_cases
    lines = [
        "# MMI v2 heldout review (blinded)",
        "",
        "Mark exactly one box per case. **Valid** = the Degraded text makes exactly the requested change and nothing else "
        "(facts, fluency and wording otherwise preserved). The generating configuration is hidden and cases are shuffled.",
        "",
    ]
    for number, case in enumerate(cases, 1):
        row = case["row"]
        case_id = f"H{number:03d}"
        key[case_id] = {"configs": case["configs"], "axis": case["axis"], "canonical_pair_id": row["canonical_pair_id"],
                        "canonical_original_id": row["canonical_original_id"], "corpus": row["corpus"],
                        "operation": row.get("operation"), "automatic_valid": row["yield"]}
        operation = row.get("operation") if case["axis"] != "MEANING" else "MEANING"
        lines += [
            f"### Case {case_id}", "",
            f"- **Axis:** `{case['axis']}` — required change: {TASK.get(operation) or TASK.get(case['axis'], '')}",
            f"- **Source:** {row['corpus']}",
            f"- **Original:** {row['original']}",
            f"- **Simplified:** {row['clean_simplification']}",
            f"- **Degraded:** {case['degraded']}",
            "",
            "- [ ] Valid", "- [ ] Invalid", "- [ ] Unsure", "- **Note:**", "",
        ]
    args.review.write_text("\n".join(lines), encoding="utf-8")
    args.key.parent.mkdir(parents=True, exist_ok=True)
    args.key.write_text(json.dumps(key, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"cases": len(cases), "review": str(args.review)}, indent=2))


def parse_review(text: str) -> dict[str, str]:
    decisions = {}
    for block in re.split(r"\n### Case ", text)[1:]:
        case_id = block.split("\n", 1)[0].strip()
        ticked = re.findall(r"- \[[xX]\] (Valid|Invalid|Unsure)", block)
        decisions[case_id] = ticked[0] if len(ticked) == 1 else ("MULTIPLE" if ticked else "UNMARKED")
    return decisions


def score(args) -> None:
    key = json.loads(args.key.read_text())
    decisions = parse_review(args.review.read_text(encoding="utf-8"))
    by = defaultdict(list)
    for case_id, meta in key.items():
        for config in meta["configs"]:
            by[(meta["axis"], config)].append({**meta, "decision": decisions.get(case_id, "UNMARKED")})
    unmarked = sum(d in {"UNMARKED", "MULTIPLE"} for d in decisions.values())
    out = {"unmarked_or_multiple": unmarked, "axes": {}}
    lines = ["", "## Heldout human audit results", "",
             f"Cases: {len(key)}; unmarked or multiple marks: {unmarked}. Unsure counts as not valid.", ""]
    for axis in sorted({a for a, _ in by}):
        configs = sorted(c for a, c in by if a == axis)
        stats = {}
        for config in configs:
            items = by[(axis, config)]
            cells = {}
            for src in SOURCES:
                s = [i for i in items if i["corpus"] == src]
                k = sum(i["decision"] == "Valid" for i in s)
                cells[src] = {"n": len(s), "valid": k, "rate": k / len(s) if s else None, "ci": wilson(k, len(s)) if s else None}
            rates = [c["rate"] for c in cells.values() if c["rate"] is not None]
            stats[config] = {"cells": cells, "macro": sum(rates) / len(rates) if rates else 0.0,
                             "unsure": sum(i["decision"] == "Unsure" for i in items),
                             "auto_vs_human_agreement": sum((i["decision"] == "Valid") == i["automatic_valid"] for i in items) / len(items)}
        eligible = [c for c in configs if stats[c]["macro"] >= 0.85]
        decision = {"eligible": eligible}
        if len(configs) == 2:
            a, b = configs
            ia = {i["canonical_pair_id"]: i for i in by[(axis, a)]}
            ib = {i["canonical_pair_id"]: i for i in by[(axis, b)]}
            common = sorted(set(ia) & set(ib))
            triples = [(ia[p]["canonical_original_id"], ia[p]["decision"] == "Valid", ib[p]["decision"] == "Valid") for p in common]
            if triples:
                only_a = sum(x and not y for _, x, y in triples)
                only_b = sum(y and not x for _, x, y in triples)
                diff, lo, hi = bootstrap_diff(triples)
                decision["paired"] = {"a": a, "b": b, "n": len(triples), "only_a": only_a, "only_b": only_b,
                                      "mcnemar_p": mcnemar_exact(only_a, only_b), "diff": diff, "ci": [lo, hi]}
        if not eligible:
            decision["winner"], decision["rule"] = None, "no finalist reaches 85%: revise and repeat (§6.4.1)"
        elif len(eligible) == 1:
            decision["winner"], decision["rule"] = eligible[0], "only eligible finalist (§6.4.2)"
        else:
            p = decision.get("paired", {})
            significant = p and p["mcnemar_p"] < 0.05 and (p["ci"][0] > 0 or p["ci"][1] < 0)
            if significant:
                decision["winner"] = p["a"] if p["diff"] > 0 else p["b"]
                decision["rule"] = "significant paired difference (§6.4.3)"
            else:
                decision["winner"], decision["rule"] = None, "equivalent: apply the cost / local / per-source tie-break (§6.4.3)"
        out["axes"][axis] = {"stats": stats, "decision": decision}
        lines += [f"### {axis}", "", "| Config | Macro valid | " + " | ".join(f"{s} (n)" for s in SOURCES) + " | Unsure | Auto–human agreement |",
                  "|---|---|" + "---|" * len(SOURCES) + "---|---|"]
        for c in configs:
            st = stats[c]
            cells = " | ".join(f"{100 * v['rate']:.0f}% ({v['n']})" if v["rate"] is not None else "—" for v in st["cells"].values())
            lines.append(f"| `{c}` | **{100 * st['macro']:.0f}%** | {cells} | {st['unsure']} | {100 * st['auto_vs_human_agreement']:.0f}% |")
        lines += ["", f"Decision: **{decision['winner'] or 'no automatic winner'}** — {decision['rule']}.", ""]
    args.results_json.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    if args.append_to:
        with args.append_to.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
    print(json.dumps({a: v["decision"] for a, v in out["axes"].items()}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "score"))
    parser.add_argument("--finalists", type=Path)
    parser.add_argument("--scored-dir", type=Path)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--results-json", type=Path)
    parser.add_argument("--append-to", type=Path)
    parser.add_argument("--seed", type=int, default=20260930)
    args = parser.parse_args()
    build(args) if args.command == "build" else score(args)


if __name__ == "__main__":
    main()
