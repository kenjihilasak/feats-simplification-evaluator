"""Compute pairwise LaBSE cosine similarity for every corpus pair."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterator

import numpy as np
from sentence_transformers import SentenceTransformer

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


def scored_records(records, model, settings) -> Iterator[dict]:
    batch_size = int(settings["batch_size"])
    chunk_size = int(settings.get("chunk_size", 4096))
    for rows in chunks(records, chunk_size):
        originals = model.encode(
            [row["original"] for row in rows],
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        simples = model.encode(
            [row["simple"] for row in rows],
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        similarities = np.einsum("ij,ij->i", originals, simples)
        for row, similarity in zip(rows, similarities):
            yield {"id": row["id"], "labse_similarity": float(similarity)}


def run(config: dict) -> None:
    settings = config["labse"]
    cache = project_path(config["cache_root"])
    cache.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer(
        settings["model_id"],
        revision=settings.get("revision"),
        cache_folder=str(cache),
        device="cuda",
    )
    for corpus_file in input_files(config):
        expected = expected_count(corpus_file, config)
        target = output_path(config, "scores/labse", corpus_file)
        if reusable(target, expected):
            print(f"[labse] reuse {target} ({expected:,})", flush=True)
            continue
        print(f"[labse] {corpus_file.language}/{corpus_file.filename} ({expected:,})", flush=True)
        count = atomic_jsonl(
            target,
            scored_records(iter_jsonl(corpus_file.path, input_limit(config)), model, settings),
        )
        if count != expected:
            raise RuntimeError(f"Wrote {count} LaBSE scores; expected {expected}: {target}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    run(load_config(args.config))


if __name__ == "__main__":
    main()

