#!/usr/bin/env python3
"""Extend the frozen evaluation-original list with every S1, SimpEval and iDEM original.

Inputs (read only):
- the existing frozen manifest (``runs/mmi_en_v2/pools/reserved_original_membership.jsonl``);
- annotation items shown to annotators (``runs/annotation_*/s1_items*.jsonl``);
- S1 candidate corpora (``runs/s1_*/final/*.jsonl``), so unused candidates are reserved too;
- SimpEval S1 items (``runs/simpeval2022_s1_v1/items.jsonl``);
- iDEM S1 items and reservation (``runs/idem_s1_v1/*/items.jsonl``, ``reserved_original_membership.jsonl``).

Output: ``runs/evaluation_originals_v3/`` with a membership file (one row per strong key,
with language and sources), a plain text list and a manifest with SHA-256 of every input.
Near-duplicate matching (word Jaccard >= 0.8) is applied at selection time, as before.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from freeze_evaluation_originals import sha256, strong_key


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def collect(runs: Path) -> tuple[dict[str, dict], dict[str, str]]:
    entries: dict[str, dict] = {}
    inputs: dict[str, str] = {}

    def add(text: str | None, language: str | None, source: str) -> None:
        if not text or not text.strip():
            return
        key = strong_key(text)
        if not key:
            return
        entry = entries.setdefault(key, {"strong_key": key, "original": text.strip(), "languages": set(), "sources": set()})
        if language:
            entry["languages"].add(language)
        entry["sources"].add(source)

    groups = [
        ("frozen_v2", sorted(runs.glob("mmi_en_v2/pools/reserved_original_membership.jsonl"))),
        ("idem_reserved", sorted(runs.glob("idem_s1_v1/reserved_original_membership.jsonl"))),
        ("s1_annotation_items", sorted(runs.glob("annotation_*/s1_items*.jsonl"))),
        ("s1_candidates", sorted(p for p in runs.glob("s1_*/final/*.jsonl") if "before_" not in p.name)),
        ("simpeval_s1_items", sorted(runs.glob("simpeval2022_s1_v1/items.jsonl"))),
        ("idem_s1_items", sorted(runs.glob("idem_s1_v1/*/items.jsonl"))),
    ]
    for group, paths in groups:
        if not paths:
            raise FileNotFoundError(f"No input files for {group} under {runs}")
        for path in paths:
            inputs[str(path.relative_to(runs))] = sha256(path)
            for row in iter_jsonl(path):
                language = row.get("language")
                if group == "frozen_v2" and not language:
                    language = "en"
                add(row.get("original"), language, group)
    return entries, inputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parents[2]
    parser.add_argument("--runs", type=Path, default=here / "runs")
    parser.add_argument("--output", type=Path, default=here / "runs" / "evaluation_originals_v3")
    args = parser.parse_args()

    entries, inputs = collect(args.runs)
    args.output.mkdir(parents=True, exist_ok=True)

    rows = []
    for key in sorted(entries):
        entry = entries[key]
        rows.append({
            "strong_key": key,
            "original": entry["original"],
            "languages": sorted(entry["languages"]),
            "sources": sorted(entry["sources"]),
        })

    membership = args.output / "reserved_original_membership.jsonl"
    with membership.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    texts = args.output / "reserved_original_texts.txt"
    texts.write_text("".join(row["original"].replace("\n", " ") + "\n" for row in rows), encoding="utf-8")

    by_language = Counter(lang for row in rows for lang in row["languages"] or ["unknown"])
    by_source = Counter(src for row in rows for src in row["sources"])
    manifest = {
        "schema": "feats-phase6-evaluation-originals-v3",
        "extends": "runs/mmi_en_v2/pools/evaluation_sources_manifest.json (schema v2, 419 EN sentences)",
        "normalization": {"strong_key": "same as v2 (freeze_evaluation_originals.strong_key)",
                          "near_duplicates": "word Jaccard >= 0.8, applied at selection time"},
        "counts": {"distinct_strong_keys": len(rows), "by_language": dict(sorted(by_language.items())),
                   "by_source": dict(sorted(by_source.items()))},
        "inputs_sha256": inputs,
        "outputs": {
            "membership": {"relative_path": membership.name, "count": len(rows), "sha256": sha256(membership)},
            "reserved_original_texts": {"relative_path": texts.name, "count": len(rows), "sha256": sha256(texts)},
        },
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["counts"], indent=2))


if __name__ == "__main__":
    main()
