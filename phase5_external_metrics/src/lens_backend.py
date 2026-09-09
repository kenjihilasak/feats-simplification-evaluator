"""LENS-SALSA adapter with a pinned Hugging Face snapshot."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from metric_backend import MetricPrediction


class LensSalsaBackend:
    def __init__(self, config: Mapping[str, Any], cache_root: Path):
        self.config = dict(config)
        self.alias = str(config["alias"])
        self.batch_size = int(config.get("batch_size", 8))
        self.repo_id = str(config["repo_id"])
        self.revision = str(config["revision"])
        self.cache_root = cache_root
        self.devices = list(config.get("devices", [0]))
        self.keep_tagged_output = bool(config.get("keep_tagged_output", False))
        self.model = None
        self.snapshot_path: Path | None = None

    def prepare(self) -> None:
        try:
            from huggingface_hub import snapshot_download
            from lens import LENS_SALSA
        except ImportError as error:
            raise RuntimeError(
                "LENS dependencies are missing; use .venv-phase5-lens."
            ) from error
        snapshot = snapshot_download(
            repo_id=self.repo_id,
            revision=self.revision,
            cache_dir=str(self.cache_root),
            allow_patterns=["checkpoints/model.ckpt", "hparams.yaml"],
        )
        self.snapshot_path = Path(snapshot)
        checkpoint = self.snapshot_path / "checkpoints" / "model.ckpt"
        if not checkpoint.is_file():
            raise FileNotFoundError(f"Pinned LENS checkpoint is missing: {checkpoint}")
        self.model = LENS_SALSA(str(checkpoint))

    def _truncate_pair(self, source: str, target: str) -> tuple[str, str, dict[str, Any]]:
        if self.model is None:
            raise RuntimeError("prepare() must be called before prediction.")
        encoder = self.model.model.encoder
        tokenizer = encoder.tokenizer
        source_ids = tokenizer.encode(source.lower(), add_special_tokens=False)
        target_ids = tokenizer.encode(target.lower(), add_special_tokens=False)
        special_tokens = tokenizer.num_special_tokens_to_add(pair=True)
        budget = int(encoder.max_positions) - special_tokens
        total = len(source_ids) + len(target_ids)
        truncated = total > budget
        if truncated:
            target_budget = min(len(target_ids), budget // 2)
            source_budget = min(len(source_ids), budget - target_budget)
            target_budget = min(len(target_ids), budget - source_budget)
            source_ids = source_ids[:source_budget]
            target_ids = target_ids[:target_budget]
            source = tokenizer.decode(source_ids, skip_special_tokens=True)
            target = tokenizer.decode(target_ids, skip_special_tokens=True)
        return source, target, {
            "source_subwords": len(tokenizer.encode(source.lower(), add_special_tokens=False)) if not truncated else len(source_ids),
            "target_subwords": len(tokenizer.encode(target.lower(), add_special_tokens=False)) if not truncated else len(target_ids),
            "combined_subwords_before_truncation": total,
            "combined_subword_budget": budget,
            "truncated": truncated,
        }

    def predict_batch(self, pairs: Sequence[tuple[str, str]]) -> list[MetricPrediction]:
        if self.model is None:
            raise RuntimeError("prepare() must be called before prediction.")
        prepared = [self._truncate_pair(pair[0], pair[1]) for pair in pairs]
        originals = [item[0] for item in prepared]
        simples = [item[1] for item in prepared]
        scores, word_scores = self.model.score(
            originals, simples, batch_size=self.batch_size, devices=self.devices
        )
        if len(scores) != len(pairs):
            raise RuntimeError("LENS returned a different number of scores than inputs.")
        tagged = None
        if self.keep_tagged_output:
            tagged = self.model.recover_output(word_scores, threshold=0.5)
        predictions = []
        for index, value in enumerate(scores):
            score = float(value)
            if not math.isfinite(score):
                raise ValueError(f"LENS returned a non-finite score at batch row {index}.")
            diagnostics = dict(prepared[index][2])
            if tagged is not None:
                diagnostics["tagged_output"] = tagged[index]
            predictions.append(MetricPrediction(score=score, diagnostics=diagnostics))
        return predictions

    def provenance(self) -> Mapping[str, Any]:
        return {
            "backend": "lens_salsa",
            "repo_id": self.repo_id,
            "revision": self.revision,
            "snapshot_path": str(self.snapshot_path) if self.snapshot_path else None,
            "native_scale": True,
            "tagged_output": self.keep_tagged_output,
        }

    def close(self) -> None:
        self.model = None

