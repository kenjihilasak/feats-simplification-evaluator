#!/usr/bin/env python3
"""Materialize a deterministic language-stratified unrepaired control sample."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

FILES = ["ar", "ca", "de", "en", "es", "fr", "it", "ja", "pt-BR", "ru", "sl", "ur"]

def key(row: dict) -> tuple[str, str]:
    pair_id = str(row["canonical_pair_id"])
    return hashlib.sha256(pair_id.encode()).hexdigest(), pair_id

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-root", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--size", type=int, default=1000)
    args = ap.parse_args()
    base, extra = divmod(args.size, len(FILES))
    manifest = []
    total = 0
    for index, language in enumerate(FILES):
        wanted = base + (index < extra)
        source = args.input_root / language / "feats_consolidated.jsonl"
        rows = []
        with source.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("text_repaired") is False:
                    rows.append(row)
        rows = sorted(rows, key=key)[:wanted]
        if len(rows) != wanted:
            raise ValueError(f"{language}: requested {wanted}, found {len(rows)}")
        rows.sort(key=lambda row: str(row["canonical_pair_id"]))
        target = args.output_root / language / "feats_consolidated.jsonl"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")
        manifest.append({"language": language, "pairs": wanted, "source": str(source)})
        total += wanted
    (args.output_root / "CONTROL_MANIFEST.json").write_text(json.dumps({"schema": "feats-phase3a-textrepair-control-v1", "method": "sha256(canonical_pair_id), stratified equally by language", "pairs": total, "languages": manifest}, indent=2) + "\n")

if __name__ == "__main__": main()
