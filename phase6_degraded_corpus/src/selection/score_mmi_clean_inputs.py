#!/usr/bin/env python3
"""Score MMI structural candidates with pinned acceptability and NLI checkers."""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from phase6_degraded_corpus.src.common.contracts import read_jsonl, write_jsonl


def batches(rows: list[dict], size: int):
    for start in range(0, len(rows), size):
        yield start, rows[start : start + size]


def load_pinned(model_id: str, revision: str, cache_dir: str):
    snapshot = (
        Path(cache_dir)
        / "hub"
        / f"models--{model_id.replace('/', '--')}"
        / "snapshots"
        / revision
    ).resolve()
    if not (snapshot / "config.json").is_file():
        raise FileNotFoundError(f"missing pinned snapshot: {snapshot}")
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(snapshot, local_files_only=True)
    return tokenizer, model


def score_acceptability(rows, config, device):
    tokenizer, model = load_pinned(
        config["acceptability_model"], config["acceptability_revision"], config["cache_dir"]
    )
    model.to(device).eval()
    output = [None] * len(rows)
    with torch.inference_mode():
        for start, batch in batches(rows, config["checker_batch_size"]):
            encoded = tokenizer(
                [row["clean_simplification"] for row in batch],
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(device)
            probabilities = model(**encoded).logits.softmax(-1)[:, 0].float().cpu().tolist()
            output[start : start + len(batch)] = probabilities
    del model, tokenizer
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return output


def score_nli(rows, config, device):
    tokenizer, model = load_pinned(
        config["nli_model"], config["nli_revision"], config["cache_dir"]
    )
    label_ids = {
        label: int(model.config.label2id[label])
        for label in ("entailment", "neutral", "contradiction")
    }
    model.to(device).eval()
    output = [None] * len(rows)
    with torch.inference_mode():
        for start, batch in batches(rows, config["checker_batch_size"]):
            encoded = tokenizer(
                [row["original"] for row in batch],
                [row["clean_simplification"] for row in batch],
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(device)
            probabilities = model(**encoded).logits.softmax(-1).float().cpu()
            values = [
                {label: float(vector[index]) for label, index in label_ids.items()}
                for vector in probabilities
            ]
            output[start : start + len(batch)] = values
    del model, tokenizer
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    rows = read_jsonl(Path(config["output_dir"]) / "structural_candidates.jsonl")
    device = torch.device(args.device)
    acceptability = score_acceptability(rows, config, device)
    nli = score_nli(rows, config, device)
    output = [
        {
            "schema": "feats-phase6-clean-quality-v2",
            "canonical_pair_id": row["canonical_pair_id"],
            "acceptability": round(acceptability[index], 8),
            "entailment": round(nli[index]["entailment"], 8),
            "nli_probabilities": {
                label: round(probability, 8) for label, probability in nli[index].items()
            },
            "acceptability_model": config["acceptability_model"],
            "acceptability_revision": config["acceptability_revision"],
            "nli_model": config["nli_model"],
            "nli_revision": config["nli_revision"],
        }
        for index, row in enumerate(rows)
    ]
    write_jsonl(Path(config["quality_scores_file"]), output)
    manifest = {
        "schema": "feats-phase6-clean-quality-manifest-v2",
        "records": len(output),
        "device": str(device),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "transformers": __import__("transformers").__version__,
        "acceptability_min_max": [min(acceptability), max(acceptability)],
        "nli_min_max": {
            label: [min(row[label] for row in nli), max(row[label] for row in nli)]
            for label in ("entailment", "neutral", "contradiction")
        },
    }
    path = Path(config["output_dir"]) / "clean_quality_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
