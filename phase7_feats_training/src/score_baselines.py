"""Score fixed lexical, NLI, acceptability, and random-head baselines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from contracts import read_jsonl, write_jsonl


def candidate_text(row: dict) -> str:
    for key in ("candidate", "candidate_simplification", "simple", "degraded"):
        if key in row:
            return str(row[key])
    raise ValueError("Input row has no candidate text")


def length_scores(rows: list[dict]) -> list[dict]:
    output = []
    for row in rows:
        candidate = candidate_text(row)
        original_words = max(1, len(row["original"].split()))
        ratio = len(candidate.split()) / original_words
        output.append({**row, "length_ratio": ratio, "inverse_length_ratio": 1.0 / max(ratio, 1e-12)})
    return output


def neural_scores(rows: list[dict], config: dict, nli: bool, cola: bool, batch_size: int) -> list[dict]:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    output = [dict(row) for row in rows]
    if nli:
        spec = config["nli"]
        snapshot = Path(spec["snapshot_path"])
        if not snapshot.is_absolute():
            snapshot = Path(__file__).resolve().parents[2] / snapshot
        if not snapshot.is_dir():
            raise FileNotFoundError(f"Pinned NLI snapshot is missing: {snapshot}")
        tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
        model = AutoModelForSequenceClassification.from_pretrained(snapshot, local_files_only=True).to(device).eval()
        entailment = int(model.config.label2id["entailment"])
        pairs = []
        for row in rows:
            candidate = candidate_text(row)
            pairs.extend(((row["original"], candidate), (candidate, row["original"])))
        probabilities = []
        with torch.inference_mode():
            for start in range(0, len(pairs), batch_size):
                part = pairs[start:start + batch_size]
                encoded = tokenizer([item[0] for item in part], [item[1] for item in part], padding=True,
                                    truncation=True, max_length=256, return_tensors="pt")
                probabilities.extend(model(**{k: v.to(device) for k, v in encoded.items()}).logits.softmax(-1)[:, entailment].cpu().tolist())
        for index, row in enumerate(output):
            row["nli_bidirectional_entailment"] = (probabilities[2 * index] + probabilities[2 * index + 1]) / 2
        del model
        torch.cuda.empty_cache()
    if cola:
        spec = config["acceptability"]
        snapshot = Path(spec["snapshot_path"])
        if not snapshot.is_absolute():
            snapshot = Path(__file__).resolve().parents[2] / snapshot
        if not snapshot.is_dir():
            raise FileNotFoundError(f"Pinned acceptability snapshot is missing: {snapshot}")
        tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
        model = AutoModelForSequenceClassification.from_pretrained(snapshot, local_files_only=True).to(device).eval()
        texts = [candidate_text(row) for row in rows]
        probabilities = []
        with torch.inference_mode():
            for start in range(0, len(texts), batch_size):
                encoded = tokenizer(texts[start:start + batch_size], padding=True, truncation=True,
                                    max_length=256, return_tensors="pt")
                probabilities.extend(model(**{k: v.to(device) for k, v in encoded.items()}).logits.softmax(-1)[:, 0].cpu().tolist())
        for row, score in zip(output, probabilities):
            row["acceptability"] = score
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--nli", action="store_true")
    parser.add_argument("--acceptability", action="store_true")
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()
    rows = length_scores(list(read_jsonl(args.input)))
    if args.nli or args.acceptability:
        if args.config is None:
            parser.error("--config is required for neural baselines")
        config = json.loads(args.config.read_text(encoding="utf-8"))
        rows = neural_scores(rows, config, args.nli, args.acceptability, args.batch_size)
    write_jsonl(args.output, rows)


if __name__ == "__main__":
    main()
