#!/usr/bin/env python3
"""Export one language's valid Phase 6 items as a scorer-ready corpus.

Each record is one original with its versions and a target score per version for its axis: pairs give the clean
simplification 1.0 and the degraded one 0.0; graded groups give clean 1.0, the mild version 0.5 and the strong one
(both edits) 0.0; MEANING and FLUENCY groups keep their own levels (1.0 / 0.67 / 0.33 / 0.0). Every text gets the
same spacing (pre-tokenized sources such as PaCCSS-IT and CLEAR would otherwise set the clean text apart from LLM
rewrites); a version that then repeats another is dropped, and so is a record left with a single score.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
from collections import Counter
from pathlib import Path

from phase6_degraded_corpus.src.annotation.build_s1_multilingual import uniform_spacing
from phase6_degraded_corpus.src.common.contracts import read_jsonl, write_jsonl
from phase6_degraded_corpus.src.common.languages import get as language

KEEP = ("canonical_pair_id", "canonical_original_id", "language", "corpus", "original")


def read(path: Path) -> list[dict]:
    return read_jsonl(path) if path.exists() else []


def drop_added_commas(clean: str, text: str) -> str:
    """MOD fronting adds a comma after the fronted phrase ("After many years of planning, the museum…"); the v2
    shortcut audit found that this comma alone predicts the lower score (AUC 0.71-0.87). The comma is optional
    after a fronted adverbial in every v2 language, so commas the edit added are removed."""
    pattern = re.compile(r"\w+(?:[-’']\w+)*|[^\w\s]")
    a, b = [m.group(0) for m in pattern.finditer(clean)], list(pattern.finditer(text))
    # Only the surplus: a comma that moved with the fronted phrase ("in Gateshead, England") stays.
    surplus = text.count(",") - clean.count(",")
    if surplus <= 0:
        return text
    drop = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, [m.group(0) for m in b], autojunk=False).get_opcodes():
        if tag in {"insert", "replace"}:
            extra = [m for m in b[j1:j2] if m.group(0) == ","][: max(0, [m.group(0) for m in b[j1:j2]].count(",") - a[i1:i2].count(","))]
            drop += extra
    for m in sorted(drop[-surplus:], key=lambda m: m.start(), reverse=True):  # the last one closes the fronted phrase
        text = text[:m.start()] + text[m.end():]
    return re.sub(r"\s{2,}", " ", text).strip()


def member_groups(path: Path, axis: str | None = None) -> list[dict]:
    """MEANING/FLUENCY groups ({members: [{level, text, target_score}]}) as export records."""
    out = []
    for g in read(path):
        name = axis or g.get("axis")
        out.append({**{k: g.get(k) for k in KEEP}, "axis": name, "format": "graded", "operation": f"{name.lower()}_graded",
                    "versions": {m["level"]: m["text"] for m in g["members"]},
                    "scores": {m["level"]: m["target_score"] for m in g["members"]}})
    return out


def records(run: Path) -> list[dict]:
    out = member_groups(run / "scored/meaning_groups.jsonl") + member_groups(run / "scored/fluency_groups.jsonl")
    for r in read(run / "scored/fose_pairs.jsonl"):
        if r["valid"]:
            out.append({**{k: r.get(k) for k in KEEP}, "axis": r["target_axis"], "format": "pair",
                        "operation": f'{r["target_axis"].lower()}_restore' if r["target_axis"] != "EXPL" else "expl_remove",
                        "versions": {"clean": r["clean_simplification"], "degraded": r["degraded_simplification"]},
                        "scores": {"clean": 1.0, "degraded": 0.0}})
    for g in read(run / "scored/fose_groups.jsonl"):
        if g["valid"]:
            mild = g["mild_version"]
            out.append({**{k: g.get(k) for k in KEEP}, "axis": g["target_axis"], "format": "graded",
                        "operation": f'{g["target_axis"].lower()}_graded',
                        "versions": {"clean": g["clean_simplification"], "mild": g["versions"][mild]["degraded"],
                                     "strong": g["versions"]["AB"]["degraded"]},
                        "scores": {"clean": 1.0, "mild": 0.5, "strong": 0.0}})
    relative = language(run.name.split("_")[1]).relative_pronouns
    for g in read(run / "scored/mod_groups.jsonl"):
        fronted = next((a for b, a in zip(g["clean_simplification"].split(". "), g["versions"]["A"]["degraded"].split(". ")) if b != a), "")
        if g["valid"] and not (re.findall(r"\w+", fronted.casefold())[:1] and re.findall(r"\w+", fronted.casefold())[0] in relative):
            # A fronted relative clause ("Который поддерживал бы…") is ungrammatical, not a mild degradation.
            clean = g["clean_simplification"]
            out.append({**{k: g.get(k) for k in KEEP}, "language": run.name.split("_")[1], "axis": "MOD", "format": "graded",
                        "operation": "mod_front_heavy+mod_sentence_reorder",
                        "versions": {"clean": clean, "mild": drop_added_commas(clean, g["versions"]["A"]["degraded"]),
                                     "strong": drop_added_commas(clean, g["versions"]["AB"]["degraded"])},
                        "scores": {"clean": 1.0, "mild": 0.5, "strong": 0.0}})
    controls = {r["canonical_pair_id"]: r["candidates"][r["selected_index"]]["degraded"]
                for r in read(run / "scored/illoc_paraphrase.jsonl") if r["yield"]}
    for r in read(run / "scored/illoc.jsonl"):
        if r["yield"]:
            versions = {"clean": r["clean_simplification"], "degraded": r["candidates"][r["selected_index"]]["degraded"]}
            scores = {"clean": 1.0, "degraded": 0.0}
            if r["canonical_pair_id"] in controls:  # a direct paraphrase, scored like the clean text
                versions["paraphrase"], scores["paraphrase"] = controls[r["canonical_pair_id"]], 1.0
            out.append({**{k: r.get(k) for k in KEEP}, "axis": "ILLOC", "format": "pair", "operation": r["operation"],
                        "versions": versions, "scores": scores})
    return out


def spaced(record: dict) -> dict | None:
    high = bool(re.search(r"\w [;:!?]", record["versions"]["clean"]))
    versions, seen = {}, set()
    for k, v in record["versions"].items():
        v = uniform_spacing(v, high)
        if v not in seen:
            versions[k] = v; seen.add(v)
    scores = {k: record["scores"][k] for k in versions}
    if len(set(scores.values())) < 2 or (record["format"] == "pair" and len(versions) < 2):
        return None
    return {**record, "original": uniform_spacing(record["original"], high), "versions": versions, "scores": scores,
            "schema": "feats-phase6-corpus-v2"}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-dir", type=Path, action="append", required=True)
    p.add_argument("--output-name", default="phase6_corpus.jsonl")
    p.add_argument("--extra-groups", nargs=3, action="append", default=[], metavar=("RUN_NAME", "AXIS", "PATH"),
                   help="add MEANING/FLUENCY groups built elsewhere (English) to one run's export")
    args = p.parse_args()
    summary = {}
    for run in args.run_dir:
        raw = records(run)
        for name, axis, path in args.extra_groups:
            if name == run.name:
                raw += [{**r, "language": r.get("language") or name.split("_")[1]} for r in member_groups(Path(path), axis)]
        kept = [s for s in map(spaced, raw) if s]
        write_jsonl(run / "final" / args.output_name, kept)
        summary[run.name] = {"records": len(kept), "dropped_after_spacing": len(raw) - len(kept),
                             "by_axis_format": dict(sorted(Counter(f'{r["axis"]}:{r["format"]}' for r in kept).items()))}
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
