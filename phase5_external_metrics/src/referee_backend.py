"""Checkpoint-compatible adapter for the official REFEREE implementation."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from common import sha256
from metric_backend import MetricPrediction


class RefereeBackend:
    def __init__(self, config: Mapping[str, Any], cache_root: Path):
        self.config = dict(config)
        self.alias = str(config["alias"])
        self.batch_size = int(config.get("batch_size", 16))
        self.backbone = str(config.get("backbone", "microsoft/deberta-v3-base"))
        self.backbone_revision = str(config["backbone_revision"])
        self.checkpoint = Path(str(config["checkpoint"])).expanduser()
        self.expected_checkpoint_sha256 = str(config.get("checkpoint_sha256", ""))
        self.max_length = int(config.get("max_length", 512))
        self.cache_root = cache_root
        self.device = None
        self.model = None
        self.tokenizer = None
        self.checkpoint_sha256 = None

    def prepare(self) -> None:
        if not self.checkpoint.is_file():
            raise FileNotFoundError(
                f"REFEREE checkpoint not found: {self.checkpoint}. "
                "Provision pretrained.bin locally; it must not be redistributed."
            )
        self.checkpoint_sha256 = sha256(self.checkpoint)
        if (
            self.expected_checkpoint_sha256
            and self.checkpoint_sha256 != self.expected_checkpoint_sha256
        ):
            raise ValueError("REFEREE checkpoint SHA-256 does not match the config.")
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer
        except ImportError as error:
            raise RuntimeError(
                "REFEREE dependencies are missing; use .venv-phase5-referee."
            ) from error

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.backbone,
            revision=self.backbone_revision,
            cache_dir=str(self.cache_root),
        )
        encoder = AutoModel.from_pretrained(
            self.backbone,
            revision=self.backbone_revision,
            cache_dir=str(self.cache_root),
        )

        class OfficialLinearHead(torch.nn.Module):
            def __init__(inner_self):
                super().__init__()
                inner_self.deberta = encoder
                inner_self.linear_out = torch.nn.ModuleList(
                    [torch.nn.Linear(768, 1) for _ in range(13)]
                )

            def forward(inner_self, encoded):
                hidden = inner_self.deberta(**encoded).last_hidden_state[:, 0, :]
                return torch.cat([head(hidden) for head in inner_self.linear_out], dim=1)

        model = OfficialLinearHead().to(self.device).float()
        payload = torch.load(self.checkpoint, map_location=self.device)
        state = payload.get("model_state_dict") if isinstance(payload, dict) else None
        if not isinstance(state, dict):
            raise ValueError("REFEREE checkpoint lacks model_state_dict.")
        model.load_state_dict(state, strict=False)
        model.eval()
        self.model = model

    def predict_batch(self, pairs: Sequence[tuple[str, str]]) -> list[MetricPrediction]:
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("prepare() must be called before prediction.")
        import torch

        texts = [f"{source} {self.tokenizer.sep_token} {target}" for source, target in pairs]
        raw_lengths = [
            len(self.tokenizer(text, add_special_tokens=True, truncation=False)["input_ids"])
            for text in texts
        ]
        encoded = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.max_length,
        )
        encoded = {key: value.to(self.device) for key, value in encoded.items()}
        with torch.no_grad():
            scores = self.model(encoded)[:, -1].detach().cpu().tolist()
        predictions = []
        for index, (value, tokens) in enumerate(zip(scores, raw_lengths)):
            score = float(value)
            if not math.isfinite(score):
                raise ValueError(f"REFEREE returned a non-finite score at batch row {index}.")
            predictions.append(
                MetricPrediction(
                    score=score,
                    diagnostics={
                        "input_subwords": tokens,
                        "max_length": self.max_length,
                        "truncated": tokens > self.max_length,
                    },
                )
            )
        return predictions

    def provenance(self) -> Mapping[str, Any]:
        return {
            "backend": "referee",
            "upstream_repository": "i-need-sleep/referee",
            "backbone": self.backbone,
            "backbone_revision": self.backbone_revision,
            "checkpoint_sha256": self.checkpoint_sha256,
            "head_type": "linear",
            "head_count": 13,
            "selected_head": 12,
            "max_length": self.max_length,
            "native_scale": True,
        }

    def close(self) -> None:
        self.model = None

