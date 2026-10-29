#!/usr/bin/env python3
"""Shortcut audit of exported Phase 6 corpora.

For every record and every two versions with different target scores, a cross-validated logistic model predicts
which version scores higher from shallow differences only (length, sentences, question mark, commas, overlap with
the Original). An ROC AUC above 0.70 means a scorer could rank that axis without reading it. Length is definitional
for OMIT and EXPL (the degraded version restores or removes words), so their gate leaves the length features out,
as in `shortcut_audit.py`; the full-feature AUC is still reported.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np

from phase6_degraded_corpus.src.common.contracts import read_jsonl
from phase6_degraded_corpus.src.evaluation.shortcut_audit import _fit_logistic, cv_auc
from phase6_degraded_corpus.src.planning.plan_mmi_operations import split_sentences

FEATURES = ("delta_tokens", "delta_characters", "delta_sentences", "delta_question", "delta_commas", "delta_overlap_original")
LENGTH = {0, 1, 5}
LENGTH_DEFINITIONAL = {"OMIT", "EXPL"}
GATE = 0.70


def features(text: str, original: str, lang: str) -> list[float]:
    words = re.findall(r"\w+", text.casefold())
    orig = set(re.findall(r"\w+", original.casefold()))
    return [len(words), len(text), len(split_sentences(text, lang)), float("?" in text or "؟" in text), text.count(","),
            len(set(words) & orig) / max(1, len(set(words) | orig))]


def examples(rows: list[dict], lang: str) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    by_axis = defaultdict(lambda: ([], []))
    for r in rows:
        f = {k: features(v, r["original"], lang) for k, v in r["versions"].items()}
        for a, b in combinations(r["versions"], 2):
            sa, sb = r["scores"][a], r["scores"][b]
            if sa == sb:
                continue
            diff = np.subtract(f[b], f[a])
            xs, ys = by_axis[r["axis"]]
            xs += [diff, -diff]; ys += [float(sb > sa), float(sa > sb)]
    return {axis: (np.asarray(xs), np.asarray(ys)) for axis, (xs, ys) in by_axis.items()}


def audit(rows: list[dict], lang: str) -> dict:
    out = {}
    for axis, (x, y) in sorted(examples(rows, lang).items()):
        gate_idx = [i for i in range(len(FEATURES)) if not (axis in LENGTH_DEFINITIONAL and i in LENGTH)]
        full, gate = cv_auc(x, y), cv_auc(x[:, gate_idx], y)
        weights = _fit_logistic(x[:, gate_idx], y)[0][1:]
        out[axis] = {"comparisons": int(len(y) // 2), "auc_all_features": full, "auc_gate": gate,
                     "largest_feature": FEATURES[gate_idx[int(np.argmax(np.abs(weights)))]],
                     "passed": gate is not None and gate <= GATE}
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-dir", type=Path, action="append", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    report = {}
    for run in args.run_dir:
        lang = run.name.split("_")[1]
        report[lang] = audit(read_jsonl(run / "final/phase6_corpus.jsonl"), lang)
    args.output.write_text(json.dumps({"gate_auc": GATE, "languages": report}, indent=2) + "\n", encoding="utf-8")
    for lang, axes in report.items():
        print(lang, {a: (round(v["auc_gate"], 2) if v["auc_gate"] is not None else None, v["largest_feature"]) for a, v in axes.items()})


if __name__ == "__main__":
    main()
