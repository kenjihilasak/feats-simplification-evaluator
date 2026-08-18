"""Score original/simple text with the sentence-complexity classifier."""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Iterator

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from common import (
    atomic_jsonl,
    chunks,
    expected_count,
    input_files,
    input_limit,
    iter_jsonl,
    load_config,
    output_path,
    project_path,
    reusable,
)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def set_mc_dropout(model, enabled: bool, probability: float) -> None:
    model.eval()
    for module in model.modules():
        if isinstance(module, torch.nn.Dropout):
            module.p = probability
            module.train(enabled)


def probabilities(model, encoded, device, batch_size: int, fp16: bool) -> np.ndarray:
    output: list[np.ndarray] = []
    total = next(iter(encoded.values())).shape[0]
    with torch.inference_mode():
        for start in range(0, total, batch_size):
            batch = {
                key: value[start : start + batch_size].to(device, non_blocking=True)
                for key, value in encoded.items()
            }
            with torch.autocast(
                device_type=device.type,
                dtype=torch.float16,
                enabled=fp16 and device.type == "cuda",
            ):
                logits = model(**batch).logits
            output.append(torch.softmax(logits.float(), dim=-1).cpu().numpy())
    return np.concatenate(output)


def score_texts(texts, tokenizer, model, device, settings, seed: int) -> dict[str, np.ndarray]:
    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=int(settings["max_length"]),
        return_tensors="pt",
    )
    batch_size = int(settings["batch_size"])
    dropout_p = float(settings["dropout_p"])
    fp16 = bool(settings.get("fp16", False))

    set_seed(seed)
    set_mc_dropout(model, False, dropout_p)
    base = probabilities(model, encoded, device, batch_size, fp16)

    samples = []
    for sample_index in range(int(settings["committee_size"])):
        set_seed(seed + sample_index + 1)
        set_mc_dropout(model, True, dropout_p)
        samples.append(probabilities(model, encoded, device, batch_size, fp16))
    set_mc_dropout(model, False, dropout_p)

    mean = np.stack(samples, axis=1).mean(axis=1)
    return {
        "base": base,
        "base_label": base.argmax(axis=1),
        "mc_mean": mean,
        "mc_label": mean.argmax(axis=1),
        "smp": 1.0 - mean.max(axis=1),
    }


def scored_records(records, tokenizer, model, device, settings, file_seed: int) -> Iterator[dict]:
    simple_idx = int(settings["simple_label_id"])
    complex_idx = int(settings["complex_label_id"])
    labels = {simple_idx: "simple", complex_idx: "complex"}
    chunk_size = int(settings.get("chunk_size", 2048))

    for chunk_index, rows in enumerate(chunks(records, chunk_size)):
        side_scores = {}
        for side_index, side in enumerate(("original", "simple")):
            seed = file_seed + chunk_index * 100 + side_index * 10
            side_scores[side] = score_texts(
                [row[side] for row in rows], tokenizer, model, device, settings, seed
            )
        for index, row in enumerate(rows):
            result = {"id": row["id"]}
            for side in ("original", "simple"):
                scores = side_scores[side]
                base_label = int(scores["base_label"][index])
                mc_label = int(scores["mc_label"][index])
                result[side] = {
                    "predicted_label_id": base_label,
                    "predicted_label": labels[base_label],
                    "prob_simple": float(scores["base"][index, simple_idx]),
                    "prob_complex": float(scores["base"][index, complex_idx]),
                    "mc_mean_predicted_label_id": mc_label,
                    "mc_mean_predicted_label": labels[mc_label],
                    "mc_mean_prob_simple": float(scores["mc_mean"][index, simple_idx]),
                    "mc_mean_prob_complex": float(scores["mc_mean"][index, complex_idx]),
                    "smp_max_mean_uncertainty": float(scores["smp"][index]),
                }
            yield result
        print(f"  scored {min((chunk_index + 1) * chunk_size, file_count_hint):,}", flush=True)


# Updated for progress before each input file.
file_count_hint = 0


def corpus_seed(settings: dict, corpus_file, file_index: int) -> int:
    configured = settings.get("file_seeds")
    if configured is None:
        return int(settings["seed"]) + file_index * 1_000_000
    key = f"{corpus_file.language}/{corpus_file.filename}"
    if key not in configured:
        raise KeyError(f"Missing complexity.file_seeds entry for {key}")
    return int(configured[key])


def run(config: dict) -> None:
    settings = config["complexity"]
    cache = project_path(config["cache_root"])
    cache.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_id = settings["model_id"]
    revision = settings.get("revision")
    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, cache_dir=cache)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_id, revision=revision, cache_dir=cache
    ).to(device)

    global file_count_hint
    for file_index, corpus_file in enumerate(input_files(config)):
        expected = expected_count(corpus_file, config)
        target = output_path(config, "scores/complexity", corpus_file)
        if reusable(target, expected):
            print(f"[complexity] reuse {target} ({expected:,})", flush=True)
            continue
        file_count_hint = expected
        print(f"[complexity] {corpus_file.language}/{corpus_file.filename} ({expected:,})", flush=True)
        records = iter_jsonl(corpus_file.path, input_limit(config))
        count = atomic_jsonl(
            target,
            scored_records(records, tokenizer, model, device, settings, corpus_seed(settings, corpus_file, file_index)),
        )
        if count != expected:
            raise RuntimeError(f"Wrote {count} complexity scores; expected {expected}: {target}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    run(load_config(args.config))


if __name__ == "__main__":
    main()
