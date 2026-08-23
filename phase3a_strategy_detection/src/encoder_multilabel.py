"""Shared batched backend for the released XLM-R and multilingual-E5 models."""

from __future__ import annotations

import gc
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from strategy_backend import BackendPrediction, LABELS, validate_thresholds


METADATA_PATTERNS = (
    "config.json",
    "label_order.json",
    "thresholds.json",
    "preprocessing.json",
    "modeling_*.py",
    "tokenizer.json",
    "tokenizer_config.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class EncoderMultilabelBackend:
    """Six-label sigmoid classifier over a standard/rewrite sentence pair."""

    def __init__(self, config: Mapping[str, Any], cache_root: Path):
        self.config = dict(config)
        self.alias = str(self.config["alias"])
        self.model_id = str(self.config["model_id"])
        self.revision = str(self.config["revision"])
        self.cache_root = Path(cache_root)
        self.batch_size = int(self.config.get("batch_size", 16))
        self.max_length = int(self.config.get("max_length", 512))
        self.standard_prefix = str(self.config.get("standard_prefix", ""))
        self.rewrite_prefix = str(self.config.get("rewrite_prefix", ""))
        self.thresholds = validate_thresholds(self.config["thresholds"])
        self.snapshot: Path | None = None
        self.model: Any = None
        self.tokenizer: Any = None
        self.device: Any = None

        if self.batch_size < 1:
            raise ValueError("Encoder batch_size must be positive.")
        if self.max_length < 2:
            raise ValueError("Encoder max_length must be at least 2.")

    def prepare(self) -> None:
        if self.snapshot is not None:
            return
        from huggingface_hub import snapshot_download

        snapshot = Path(
            snapshot_download(
                repo_id=self.model_id,
                revision=self.revision,
                cache_dir=self.cache_root,
                allow_patterns=list(METADATA_PATTERNS),
            )
        )
        labels = json.loads(
            (snapshot / "label_order.json").read_text(encoding="utf-8")
        )
        if labels != list(LABELS):
            raise ValueError(
                f"Released label order differs from Phase 3a: {labels}"
            )
        released_thresholds = validate_thresholds(
            json.loads((snapshot / "thresholds.json").read_text(encoding="utf-8"))
        )
        if released_thresholds != self.thresholds:
            raise ValueError("Configured thresholds differ from the released model.")

        model_config = json.loads(
            (snapshot / "config.json").read_text(encoding="utf-8")
        )
        released = model_config.get("e2r_classifier", {})
        if released.get("labels") != list(LABELS):
            raise ValueError("Checkpoint config has an unexpected label inventory.")
        if int(released.get("max_length", -1)) != self.max_length:
            raise ValueError("Configured max_length differs from the checkpoint.")
        config_thresholds = validate_thresholds(released.get("thresholds", {}))
        if config_thresholds != self.thresholds:
            raise ValueError("Checkpoint config and thresholds.json disagree.")

        preprocessing_path = snapshot / "preprocessing.json"
        if preprocessing_path.is_file():
            preprocessing = json.loads(preprocessing_path.read_text(encoding="utf-8"))
            if preprocessing.get("standard_prefix", "") != self.standard_prefix:
                raise ValueError("Configured standard prefix differs from release.")
            if preprocessing.get("rewrite_prefix", "") != self.rewrite_prefix:
                raise ValueError("Configured rewrite prefix differs from release.")
        elif self.standard_prefix or self.rewrite_prefix:
            raise ValueError("Configured prefixes but checkpoint has no preprocessing.json.")

        self.snapshot = snapshot

    def load(self) -> None:
        self.prepare()
        if self.model is not None:
            return

        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        if not torch.cuda.is_available():
            raise RuntimeError("The encoder backend requires a CUDA GPU.")
        self.device = torch.device("cuda")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            revision=self.revision,
            cache_dir=self.cache_root,
            trust_remote_code=True,
        )
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_id,
            revision=self.revision,
            cache_dir=self.cache_root,
            trust_remote_code=True,
            dtype=torch.float16,
            low_cpu_mem_usage=True,
        ).to(self.device)
        self.model.eval()

    def predict_batch(
        self,
        pairs: Sequence[tuple[str, str]],
    ) -> list[BackendPrediction]:
        if self.model is None or self.tokenizer is None or self.device is None:
            raise RuntimeError("Call load() before predict_batch().")
        if not pairs:
            return []

        import torch

        originals = [self.standard_prefix + str(original) for original, _ in pairs]
        rewrites = [self.rewrite_prefix + str(simple) for _, simple in pairs]
        encoded = self.tokenizer(
            originals,
            rewrites,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        token_counts = encoded["attention_mask"].sum(dim=1).tolist()
        encoded = {key: value.to(self.device) for key, value in encoded.items()}
        with torch.inference_mode():
            logits = self.model(**encoded).logits
            probabilities = torch.sigmoid(logits).float().cpu().tolist()

        predictions = []
        for values, token_count in zip(probabilities, token_counts):
            scores = {
                label: float(values[index])
                for index, label in enumerate(LABELS)
            }
            predictions.append(
                BackendPrediction(
                    scores=scores,
                    diagnostics={
                        "input_tokens": int(token_count),
                        "max_length": self.max_length,
                        "at_max_length": int(token_count) >= self.max_length,
                    },
                )
            )
        return predictions

    def provenance(self) -> Mapping[str, Any]:
        self.prepare()
        assert self.snapshot is not None
        metadata_files = {
            path.name: sha256(path)
            for path in sorted(self.snapshot.iterdir())
            if path.is_file()
        }
        return {
            "backend": "encoder_multilabel",
            "alias": self.alias,
            "model_id": self.model_id,
            "revision": self.revision,
            "architecture": self.config["architecture"],
            "training_loss": self.config["training_loss"],
            "input_mode": "pair",
            "standard_prefix": self.standard_prefix,
            "rewrite_prefix": self.rewrite_prefix,
            "max_length": self.max_length,
            "batch_size": self.batch_size,
            "label_order": list(LABELS),
            "thresholds": dict(self.thresholds),
            "metadata_files": metadata_files,
        }

    def close(self) -> None:
        self.model = None
        self.tokenizer = None
        self.device = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
