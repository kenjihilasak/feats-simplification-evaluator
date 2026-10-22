"""Write the per-item metadata the S1 server shows: the dataset always, the human version after submission.

Reads the hidden keys locally. Controls get a dataset too, so its absence cannot mark them.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "phase6_degraded_corpus/runs"
ROUNDS = {"en": RUNS / "annotation_v1", "es": RUNS / "annotation_es_v1", "fr": RUNS / "annotation_fr_v1"}
PHASE2B = ROOT / "phase2b_consolidation/runs"
VARIANTS = ("2026-09-29_base_textrepair_v1", "2026-09-29_target_simple_textrepair_v1")


def dataset(source: str | None, corpus: str | None) -> str:
    if not corpus:
        raise ValueError("missing corpus")
    return corpus if not source or source == corpus else f"{source} · {corpus}"


def corpus_index(lang: str) -> tuple[dict[str, tuple], dict[str, tuple]]:
    """canonical_original_id and original text -> (source, corpus), from the Phase 2b files."""
    by_id, by_text = {}, {}
    for variant in VARIANTS:
        path = PHASE2B / variant / f"data/{lang}/feats_consolidated.jsonl"
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                first = (row.get("corpora") or row.get("provenance") or [{}])[0]
                value = (first.get("source"), first.get("corpus"))
                by_id.setdefault(row["canonical_original_id"], value)
                by_text.setdefault(row["original"].strip(), value)
    return by_id, by_text


def build(lang: str) -> list[dict]:
    run = ROUNDS[lang]
    key = json.loads((run / "s1_key.json").read_text(encoding="utf-8"))
    controls = json.loads((run / "s1_controls_key.json").read_text(encoding="utf-8"))
    public = {json.loads(l)["case_id"]: json.loads(l) for name in ("s1_items.jsonl", "s1_controls.jsonl")
              for l in (run / name).read_text(encoding="utf-8").splitlines() if l.strip()}
    by_id, by_text = corpus_index(lang)
    rows = []
    for k in key:
        source, _ = by_id.get(k["canonical_original_id"], (None, None))
        best = max(k["levels"].values())
        rows.append({"case_id": k["case_id"], "dataset": dataset(source, k["corpus"]),
                     "human_versions": [label for label, level in k["levels"].items() if level == best]})
    for c in controls:
        item = public[c["case_id"]]
        found = by_id.get(c.get("source_id")) or by_text.get(item["original"].strip())
        if found is None:
            raise ValueError(f"no dataset for control {c['case_id']}")
        humans = (list(item["versions"]) if c["control_kind"] == "identical"
                  else [label for label, level in c["levels"].items() if level == 1.0])
        rows.append({"case_id": c["case_id"], "dataset": dataset(*found), "human_versions": humans})
    return rows


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", choices=tuple(ROUNDS), required=True)
    args = parser.parse_args(argv)
    rows = build(args.language)
    out = ROUNDS[args.language] / "s1_meta.jsonl"
    out.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    print(json.dumps({"language": args.language, "rows": len(rows), "output": str(out)}))


if __name__ == "__main__":
    main()
