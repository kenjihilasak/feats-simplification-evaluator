"""Add hand-picked English Compression and Syntactic-change examples to S1 (requested by Serge, 23 Oct 2026).

Each pair has two edits; the degradation undoes only the compression or syntactic change by restoring the
original wording, so the degraded version differs from both the simplification and the original. The four
pairs were chosen by reading candidates whose single Phase 3a strategy is COMP or SYNT.
"""
from __future__ import annotations

import json
from pathlib import Path

from phase6_degraded_corpus.src.annotation.build_s1_round import item
from phase6_degraded_corpus.src.generation.generate_fose_rules import alignment, detokenize

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "phase6_degraded_corpus/runs/annotation_v1"
CANDIDATES = ROOT / ("phase3a_strategy_detection/gold_candidates/2026-09-30_single_strategy_gemma_anchored_strict_textrepair_v1"
                     "/data/en/single_strategy_candidates.jsonl")
# (case id, pair id fragment, axis, original wording restored, simplified wording replaced)
PICKS = [
    ("S301", "255535fa82d0", "COMP", "is used to refer", "refers"),
    ("S302", "cfc3d4b812b1", "COMP", "the west of", "western"),
    ("S303", "af56b2433734", "SYNT", "has symbolical significance", "is a symbol"),
    ("S304", "c991a1ce0559", "SYNT", "have received nominations", "were also nominated"),
]


def degrade(original: str, simple: str, restored: str, replaced: str) -> str:
    left, right, ops = alignment(original, simple)
    for tag, i1, i2, j1, j2 in ops:
        if tag == "replace" and " ".join(left[i1:i2]) == restored and " ".join(right[j1:j2]) == replaced:
            return detokenize(right[:j1] + left[i1:i2] + right[j2:])
    raise ValueError(f"edit not found: {replaced!r} <- {restored!r}")


def build() -> tuple[list[dict], list[dict], list[dict]]:
    rows = [json.loads(line) for line in CANDIDATES.read_text(encoding="utf-8").splitlines()]
    public, key, meta = [], [], []
    for case, fragment, axis, restored, replaced in PICKS:
        matches = [r for r in rows if fragment in r["canonical_pair_id"]]
        if len(matches) != 1:
            raise ValueError(f"{case}: {len(matches)} pairs match {fragment}")
        row = matches[0]
        if row["candidate_strategy_code"] != axis:
            raise ValueError(f"{case}: Phase 3a strategy is {row['candidate_strategy_code']}, not {axis}")
        corpus = row["corpora"][0]["corpus"]
        pair = {"canonical_pair_id": row["canonical_pair_id"], "canonical_original_id": row["canonical_original_id"],
                "corpus": corpus, "original": row["original"], "clean_simplification": row["simple"]}
        operation = "comp_restore" if axis == "COMP" else "synt_restore"
        p, k = item(axis, pair, [(1.0, "clean", row["simple"]), (0.0, operation, degrade(row["original"], row["simple"], restored, replaced))], "pair")
        public.append({"case_id": case, **p}); key.append({"case_id": case, **k})
        meta.append({"case_id": case, "dataset": f"MultiSim · {corpus}",
                     "human_versions": [label for label, level in k["levels"].items() if level == 1.0]})
    return public, key, meta


def main() -> None:
    public, key, meta = build()
    (RUN / "s1_items_comp_synt.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in public), encoding="utf-8")
    (RUN / "s1_key_comp_synt.json").write_text(json.dumps(key, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (RUN / "s1_meta_comp_synt.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in meta), encoding="utf-8")
    for x in public:
        print(x["case_id"], x["axis"], json.dumps(x["versions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
