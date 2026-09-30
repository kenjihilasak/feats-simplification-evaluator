"""Train a paired cross-encoder with BCE plus margin-ranking loss."""

from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path
from typing import Any

from contracts import atomic_json, read_jsonl, sha256


def seed_everything(seed: int) -> None:
    random.seed(seed)
    import numpy as np
    import torch
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def paired(rows: list[dict], axis: str, split: str) -> list[tuple[dict, dict]]:
    by_pair: dict[str, dict[str, dict]] = {}
    for row in rows:
        if row["axis"] == axis and row["split"] == split:
            by_pair.setdefault(row["canonical_pair_id"], {})[row["provenance"]["variant"]] = row
    result = []
    for pair_id, variants in by_pair.items():
        if set(variants) != {"simplified", "degraded"}:
            raise ValueError(f"Incomplete pair {pair_id}: {set(variants)}")
        result.append((variants["simplified"], variants["degraded"]))
    return sorted(result, key=lambda pair: pair[0]["canonical_pair_id"])


class PairDataset:
    def __init__(self, pairs: list[tuple[dict, dict]], tokenizer: Any, max_length: int):
        self.pairs, self.tokenizer, self.max_length = pairs, tokenizer, max_length

    def __len__(self) -> int:
        return len(self.pairs)

    def __getitem__(self, index: int) -> dict:
        clean, degraded = self.pairs[index]
        encoded = self.tokenizer(
            [clean["original"], degraded["original"]],
            [clean["candidate_simplification"], degraded["candidate_simplification"]],
            truncation=True, max_length=self.max_length, padding=False,
        )
        return {**encoded, "labels": [1.0, 0.0], "pair_id": clean["canonical_pair_id"]}


def collate(features: list[dict], tokenizer: Any) -> dict:
    import torch
    flattened = []
    for feature in features:
        for index in range(2):
            flattened.append({key: value[index] for key, value in feature.items()
                              if key not in {"labels", "pair_id"}})
    batch = tokenizer.pad(flattened, padding=True, return_tensors="pt")
    batch["labels"] = torch.tensor([label for feature in features for label in feature["labels"]])
    return batch


def pairwise_accuracy(model: Any, loader: Any, device: Any) -> float:
    import torch
    model.eval()
    correct = total = 0
    with torch.inference_mode():
        for batch in loader:
            labels = batch.pop("labels")
            logits = model(**{key: value.to(device) for key, value in batch.items()}).logits.squeeze(-1).cpu()
            correct += int((logits[0::2] > logits[1::2]).sum())
            total += len(labels) // 2
    return correct / total


def train(config_path: Path, dataset_path: Path, output_dir: Path, axis: str,
          learning_rate: float, seed: int) -> None:
    import torch
    from torch.nn import functional as F
    from torch.optim import AdamW
    from torch.utils.data import DataLoader
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    config = json.loads(config_path.read_text(encoding="utf-8"))
    seed_everything(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rows = list(read_jsonl(dataset_path))
    train_pairs, validation_pairs = paired(rows, axis, "train"), paired(rows, axis, "validation")
    snapshot = Path(config["snapshot_path"])
    if not snapshot.is_absolute():
        snapshot = Path(__file__).resolve().parents[2] / snapshot
    if not snapshot.is_dir():
        raise FileNotFoundError(f"Pinned model snapshot is missing: {snapshot}")
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        snapshot, num_labels=1, local_files_only=True, ignore_mismatched_sizes=True,
    ).to(device)
    if config.get("gradient_checkpointing", False):
        model.gradient_checkpointing_enable()
    train_loader = DataLoader(PairDataset(train_pairs, tokenizer, config["max_length"]),
                              batch_size=config["pair_batch_size"], shuffle=True,
                              collate_fn=lambda rows: collate(rows, tokenizer))
    validation_loader = DataLoader(PairDataset(validation_pairs, tokenizer, config["max_length"]),
                                   batch_size=config["eval_pair_batch_size"], shuffle=False,
                                   collate_fn=lambda rows: collate(rows, tokenizer))
    optimizer = AdamW(model.parameters(), lr=learning_rate, weight_decay=config["weight_decay"])
    accumulation = int(config["gradient_accumulation_steps"])
    # bf16 autocast: fp16 overflows on DeBERTa-v3; no loss scaling needed with bf16.
    scaler = torch.amp.GradScaler("cuda", enabled=False)
    output_dir.mkdir(parents=True, exist_ok=True)
    history, best = [], -1.0
    for epoch in range(1, int(config["epochs"]) + 1):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        running = 0.0
        for step, batch in enumerate(train_loader, 1):
            labels = batch.pop("labels").to(device)
            inputs = {key: value.to(device) for key, value in batch.items()}
            with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
                logits = model(**inputs).logits.squeeze(-1)
                bce = F.binary_cross_entropy_with_logits(logits, labels)
                ranking = F.margin_ranking_loss(logits[0::2], logits[1::2],
                                                torch.ones_like(logits[0::2]),
                                                margin=float(config["margin"]))
                loss = (bce + float(config["pairwise_weight"]) * ranking) / accumulation
            scaler.scale(loss).backward()
            if step % accumulation == 0 or step == len(train_loader):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), float(config["max_grad_norm"]))
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
            running += float(loss) * accumulation
        accuracy = pairwise_accuracy(model, validation_loader, device)
        history.append({"epoch": epoch, "train_loss": running / len(train_loader),
                        "validation_pairwise_accuracy": accuracy})
        if accuracy > best:
            best = accuracy
            model.save_pretrained(output_dir / "checkpoint")
            tokenizer.save_pretrained(output_dir / "checkpoint")
        else:
            break
    atomic_json(output_dir / "run.json", {
        "schema": "feats-phase7-training-run-v1", "status": "complete", "axis": axis,
        "model_name": config["model_name"], "revision": config["revision"],
        "learning_rate": learning_rate, "seed": seed, "dataset_sha256": sha256(dataset_path),
        "config_sha256": sha256(config_path), "train_pairs": len(train_pairs),
        "validation_pairs": len(validation_pairs), "best_validation_pairwise_accuracy": best,
        "history": history, "torch_version": torch.__version__, "transformers_offline": os.getenv("TRANSFORMERS_OFFLINE"),
    })


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-config", required=True, type=Path)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--axis", required=True, choices=("MEANING", "MOD", "ILLOC"))
    parser.add_argument("--learning-rate", required=True, type=float)
    parser.add_argument("--seed", required=True, type=int)
    args = parser.parse_args()
    train(args.model_config, args.dataset, args.output_dir, args.axis, args.learning_rate, args.seed)


if __name__ == "__main__":
    main()
