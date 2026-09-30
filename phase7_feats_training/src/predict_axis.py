"""Predict scalar axis scores for Phase 7 JSONL items."""

from __future__ import annotations

import argparse
from pathlib import Path

from contracts import read_jsonl, write_jsonl


def predict(checkpoint: Path, input_path: Path, output_path: Path, batch_size: int) -> None:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(checkpoint, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(checkpoint, local_files_only=True).to(device).eval()
    rows, output = list(read_jsonl(input_path)), []
    with torch.inference_mode():
        for start in range(0, len(rows), batch_size):
            batch = rows[start:start + batch_size]
            candidates = [row.get("candidate", row.get("candidate_simplification")) for row in batch]
            encoded = tokenizer([row["original"] for row in batch], candidates, padding=True,
                                truncation=True, max_length=256, return_tensors="pt")
            logits = model(**{key: value.to(device) for key, value in encoded.items()}).logits.squeeze(-1)
            scores = logits.sigmoid().float().cpu().tolist()
            output.extend({**row, "axis_score": float(score)} for row, score in zip(batch, scores))
    write_jsonl(output_path, output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()
    predict(args.checkpoint, args.input, args.output, args.batch_size)


if __name__ == "__main__":
    main()
