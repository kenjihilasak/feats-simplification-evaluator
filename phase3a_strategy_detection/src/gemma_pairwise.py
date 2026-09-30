"""Gemma 3 pairwise QLoRA backend released with the E2R classifier."""

from __future__ import annotations

import gc
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from strategy_backend import (
    BackendPrediction,
    LABEL_CODES,
    LABELS,
    validate_thresholds,
)


RELEASE_FILES = (
    "adapter_config.json",
    "inference.py",
    "resolved_config.yaml",
    "runtime.json",
    "taxonomy_cards.json",
    "thresholds.json",
    "tokenizer/chat_template.jinja",
    "tokenizer/tokenizer.json",
    "tokenizer/tokenizer_config.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def import_release_module(snapshot: Path, revision: str) -> Any:
    """Import the checkpoint's pinned official inference implementation."""

    module_name = f"_feats_e2r_gemma_inference_{revision[:12]}"
    if module_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            module_name, snapshot / "inference.py"
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot import Gemma inference from {snapshot}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    return sys.modules[module_name]


class GemmaPairwiseBackend:
    """Six independent boolean next-token decisions for each sentence pair."""

    def __init__(self, config: Mapping[str, Any], cache_root: Path):
        self.config = dict(config)
        self.alias = str(self.config["alias"])
        self.model_id = str(self.config["model_id"])
        self.revision = str(self.config["revision"])
        self.base_model_id = str(self.config["base_model_id"])
        self.base_revision = str(self.config["base_revision"])
        self.cache_root = Path(cache_root)
        self.batch_size = int(self.config.get("batch_size", 1))
        self.verbose_predictions = bool(
            self.config.get("verbose_predictions", False)
        )
        self.snapshot: Path | None = None
        self.release: Any = None
        self.thresholds: dict[str, float] = {}
        self.taxonomy_cards: dict[str, str] = {}
        self.runtime: dict[str, Any] = {}
        self.resolved_config: dict[str, Any] = {}
        self.training_max_length = 0
        self.processor: Any = None
        self.tokenizer: Any = None
        self.model: Any = None
        if self.batch_size != 1:
            raise ValueError("The released Gemma backend requires batch_size=1.")

    def prepare(self) -> None:
        """Download and validate the small released inference artifacts."""

        if self.snapshot is not None:
            return
        import yaml
        from huggingface_hub import snapshot_download

        snapshot = Path(
            snapshot_download(
                repo_id=self.model_id,
                revision=self.revision,
                cache_dir=self.cache_root,
                allow_patterns=list(RELEASE_FILES),
            )
        )
        adapter_config = json.loads(
            (snapshot / "adapter_config.json").read_text(encoding="utf-8")
        )
        thresholds = validate_thresholds(
            json.loads(
                (snapshot / "thresholds.json").read_text(encoding="utf-8")
            )
        )
        taxonomy_cards = json.loads(
            (snapshot / "taxonomy_cards.json").read_text(encoding="utf-8")
        )
        if set(taxonomy_cards) != set(LABELS):
            raise ValueError("Released Gemma taxonomy labels differ from Phase 3a.")
        taxonomy_cards = {
            label: str(taxonomy_cards[label]) for label in LABELS
        }
        runtime = json.loads(
            (snapshot / "runtime.json").read_text(encoding="utf-8")
        )
        resolved_config = yaml.safe_load(
            (snapshot / "resolved_config.yaml").read_text(encoding="utf-8")
        )
        if not isinstance(resolved_config, dict):
            raise ValueError("Invalid released Gemma resolved_config.yaml.")
        release = import_release_module(snapshot, self.revision)

        released_model = str(adapter_config.get("base_model_name_or_path", ""))
        configured_model = str(
            resolved_config.get("model", {}).get("pretrained_model_name", "")
        )
        if (
            released_model != self.base_model_id
            or configured_model != self.base_model_id
        ):
            raise ValueError("Released Gemma base model differs from configuration.")
        if list(release.LABELS) != list(LABELS):
            raise ValueError("Released Gemma label order differs from Phase 3a.")
        if str(release.BASE_MODEL) != self.base_model_id:
            raise ValueError("Official Gemma inference uses a different base model.")
        model_settings = resolved_config.get("model", {})
        if model_settings.get("architecture") != "pairwise_causal_lm":
            raise ValueError("Unexpected Gemma classifier architecture.")
        if resolved_config.get("data", {}).get("input_mode") != "pair":
            raise ValueError("Unexpected Gemma classifier input mode.")
        if resolved_config.get("decision", {}).get("probability_source") != "token":
            raise ValueError("Unexpected Gemma probability source.")
        expected_quantization = {
            "load_in_4bit": True,
            "quant_type": "nf4",
            "compute_dtype": "bfloat16",
            "double_quant": True,
        }
        if self.config.get("quantization") != expected_quantization:
            raise ValueError("Gemma config must reproduce the released NF4 settings.")
        if resolved_config.get("quantization") != expected_quantization:
            raise ValueError("Released Gemma NF4 settings differ from configuration.")

        self.snapshot = snapshot
        self.release = release
        self.thresholds = thresholds
        self.taxonomy_cards = taxonomy_cards
        self.runtime = runtime
        self.resolved_config = resolved_config
        self.training_max_length = int(model_settings["max_length"])

    def load(self) -> None:
        """Load the pinned gated base model and released adapter on CUDA."""

        self.prepare()
        if self.model is not None:
            return

        import torch
        from peft import PeftModel, prepare_model_for_kbit_training
        from transformers import (
            AutoProcessor,
            BitsAndBytesConfig,
            Gemma3ForConditionalGeneration,
        )

        if not torch.cuda.is_available():
            raise RuntimeError("The Gemma pairwise backend requires a CUDA GPU.")
        if not torch.cuda.is_bf16_supported():
            raise RuntimeError(
                "The released Gemma inference uses bfloat16, but this GPU does "
                "not report bfloat16 support."
            )

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        processor = AutoProcessor.from_pretrained(
            self.base_model_id,
            revision=self.base_revision,
            cache_dir=self.cache_root,
            trust_remote_code=False,
        )
        tokenizer = processor.tokenizer
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"
        tokenizer.truncation_side = "left"

        base_model = Gemma3ForConditionalGeneration.from_pretrained(
            self.base_model_id,
            revision=self.base_revision,
            cache_dir=self.cache_root,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.bfloat16,
            attn_implementation="sdpa",
            trust_remote_code=False,
        )
        base_model = prepare_model_for_kbit_training(
            base_model,
            use_gradient_checkpointing=True,
        )
        model = PeftModel.from_pretrained(
            base_model,
            self.model_id,
            revision=self.revision,
            cache_dir=self.cache_root,
            is_trainable=False,
        )
        model.eval()
        model.config.use_cache = True

        self.processor = processor
        self.tokenizer = tokenizer
        self.model = model

    def predict_pair(self, original: str, simple: str) -> BackendPrediction:
        if self.model is None or self.processor is None or self.tokenizer is None:
            raise RuntimeError("Call load() before predict_pair().")
        scores: dict[str, float] = {}
        prompt_tokens: dict[str, int] = {}
        for label in LABELS:
            prompt = self.release._build_binary_prompt(
                self.processor,
                str(original),
                str(simple),
                label,
                self.taxonomy_cards[label],
            )
            token_count = len(
                self.tokenizer.encode(prompt, add_special_tokens=True)
            )
            prompt_tokens[LABEL_CODES[label]] = token_count
            probability = self.release._boolean_token_probability(
                self.model,
                self.tokenizer,
                prompt,
            )
            scores[label] = float(probability)
            if self.verbose_predictions:
                print(
                    f"Finished {LABEL_CODES[label]} ({label}): "
                    f"{probability:.6f}",
                    flush=True,
                )

        largest = max(prompt_tokens.values(), default=0)
        return BackendPrediction(
            scores=scores,
            diagnostics={
                "prompt_tokens": prompt_tokens,
                "max_prompt_tokens": largest,
                "training_max_length": self.training_max_length,
                "exceeds_training_max_length": largest > self.training_max_length,
            },
        )

    def predict_batch(
        self, pairs: Sequence[tuple[str, str]]
    ) -> list[BackendPrediction]:
        return [self.predict_pair(original, simple) for original, simple in pairs]

    def provenance(self) -> Mapping[str, Any]:
        self.prepare()
        assert self.snapshot is not None
        model_settings = self.resolved_config["model"]
        return {
            "backend": "gemma_pairwise",
            "alias": self.alias,
            "model_id": self.model_id,
            "revision": self.revision,
            "base_model_id": self.base_model_id,
            "base_revision": self.base_revision,
            "architecture": model_settings["architecture"],
            "decision_method": "boolean_next_token_probability",
            "input_mode": self.resolved_config["data"]["input_mode"],
            "training_max_length": self.training_max_length,
            "batch_size": self.batch_size,
            "label_order": list(LABELS),
            "label_codes": dict(LABEL_CODES),
            "thresholds": dict(self.thresholds),
            "taxonomy_fingerprint": self.runtime.get("taxonomy_fingerprint"),
            "taxonomy_cards_sha256": sha256(
                self.snapshot / "taxonomy_cards.json"
            ),
            "reference_files": {
                name: sha256(self.snapshot / name)
                for name in RELEASE_FILES
                if (self.snapshot / name).is_file()
            },
            "quantization": dict(self.config["quantization"]),
            "attn_implementation": model_settings["attn_implementation"],
        }

    def close(self) -> None:
        self.model = None
        self.processor = None
        self.tokenizer = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
