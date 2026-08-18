"""Qwen2.5 pairwise QLoRA backend released with the E2R classifier."""

from __future__ import annotations

import gc
import hashlib
import importlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from strategy_backend import (
    BackendPrediction,
    LABEL_CODES,
    LABELS,
    validate_thresholds,
)


RELEASE_FILES = (
    "adapter_config.json",
    "inference_config.json",
    "thresholds.json",
    "e2r_taxonomy.yaml",
    "reference_implementation/__init__.py",
    "reference_implementation/binary_relevance.py",
    "reference_implementation/taxonomy.py",
    "tokenizer_config.json",
    "tokenizer.json",
    "chat_template.jinja",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def import_reference_package(snapshot: Path, revision: str) -> tuple[Any, Any]:
    """Import a pinned reference package without colliding with later models."""

    package_dir = snapshot / "reference_implementation"
    package_name = f"_feats_e2r_reference_{revision[:12]}"
    if package_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            package_name,
            package_dir / "__init__.py",
            submodule_search_locations=[str(package_dir)],
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot import reference package from {package_dir}")
        package = importlib.util.module_from_spec(spec)
        sys.modules[package_name] = package
        spec.loader.exec_module(package)
    binary_relevance = importlib.import_module(f"{package_name}.binary_relevance")
    taxonomy_module = importlib.import_module(f"{package_name}.taxonomy")
    return binary_relevance, taxonomy_module


class QwenPairwiseBackend:
    """Six independent boolean next-token decisions for each sentence pair."""

    def __init__(self, config: Mapping[str, Any], cache_root: Path):
        self.config = dict(config)
        self.alias = str(self.config["alias"])
        self.model_id = str(self.config["model_id"])
        self.revision = str(self.config["revision"])
        self.base_model_id = str(self.config["base_model_id"])
        self.base_revision = str(self.config["base_revision"])
        self.cache_root = Path(cache_root)
        self.snapshot: Path | None = None
        self.inference_config: dict[str, Any] = {}
        self.thresholds: dict[str, float] = {}
        self.taxonomy_fingerprint = ""
        self.binary_relevance: Any = None
        self.taxonomy: Any = None
        self.tokenizer: Any = None
        self.model: Any = None

    def prepare(self) -> None:
        """Download and validate small released inference artifacts."""

        if self.snapshot is not None:
            return
        from huggingface_hub import snapshot_download

        snapshot = Path(
            snapshot_download(
                repo_id=self.model_id,
                revision=self.revision,
                cache_dir=self.cache_root,
                allow_patterns=list(RELEASE_FILES),
            )
        )
        inference_config = json.loads(
            (snapshot / "inference_config.json").read_text(encoding="utf-8")
        )
        released_thresholds = json.loads(
            (snapshot / "thresholds.json").read_text(encoding="utf-8")
        )
        if inference_config.get("label_order") != list(LABELS):
            raise ValueError("Released Qwen label order differs from Phase 3 label order.")
        if inference_config.get("architecture") != "pairwise_causal_lm":
            raise ValueError("Unexpected Qwen classifier architecture.")
        if inference_config.get("decision_method") != "boolean_next_token_probability":
            raise ValueError("Unexpected Qwen decision method.")
        thresholds = validate_thresholds(released_thresholds)
        configured_thresholds = validate_thresholds(inference_config["thresholds"])
        if thresholds != configured_thresholds:
            raise ValueError("thresholds.json and inference_config.json disagree.")

        binary_relevance, taxonomy_module = import_reference_package(
            snapshot, self.revision
        )
        taxonomy = taxonomy_module.load_taxonomy(snapshot / "e2r_taxonomy.yaml")

        self.snapshot = snapshot
        self.inference_config = inference_config
        self.thresholds = thresholds
        self.binary_relevance = binary_relevance
        self.taxonomy = taxonomy
        self.taxonomy_fingerprint = str(taxonomy.fingerprint)

    def load(self) -> None:
        """Load the pinned base model and adapter once on a CUDA GPU."""

        self.prepare()
        if self.model is not None:
            return

        import torch
        from peft import PeftModel
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )

        if not torch.cuda.is_available():
            raise RuntimeError("The Qwen pairwise backend requires a CUDA GPU.")
        if not torch.cuda.is_bf16_supported():
            raise RuntimeError(
                "The released Qwen inference uses bfloat16, but this GPU does not "
                "report bfloat16 support. Request a compatible GPU."
            )

        quantization = self.config["quantization"]
        if quantization != {
            "load_in_4bit": True,
            "quant_type": "nf4",
            "compute_dtype": "bfloat16",
            "double_quant": True,
        }:
            raise ValueError("Smoke config must reproduce the released NF4 settings.")

        tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            revision=self.revision,
            cache_dir=self.cache_root,
            trust_remote_code=False,
        )
        tokenizer.model_max_length = int(self.inference_config["max_length"])

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model_id,
            revision=self.base_revision,
            cache_dir=self.cache_root,
            quantization_config=quantization_config,
            device_map="auto",
            dtype=torch.bfloat16,
            trust_remote_code=False,
            low_cpu_mem_usage=True,
        )
        model = PeftModel.from_pretrained(
            base_model,
            self.model_id,
            revision=self.revision,
            cache_dir=self.cache_root,
            is_trainable=False,
        )
        model.eval()

        self.tokenizer = tokenizer
        self.model = model

    def _render_prompt(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    def predict_pair(self, original: str, simple: str) -> BackendPrediction:
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Call load() before predict_pair().")
        row = {"source_text": str(original), "simplified_text": str(simple)}
        scores: dict[str, float] = {}
        prompt_tokens: dict[str, int] = {}
        max_length = int(self.inference_config["max_length"])

        for label in LABELS:
            system_prompt, user_prompt = self.binary_relevance.build_binary_prompt(
                row,
                label,
                self.taxonomy,
                include_definition=True,
                demonstrations=(),
                request_confidence=False,
                response_format="boolean",
                input_mode="pair",
            )
            prompt = self._render_prompt(system_prompt, user_prompt)
            token_count = len(
                self.tokenizer.encode(prompt, add_special_tokens=True)
            )
            prompt_tokens[LABEL_CODES[label]] = token_count
            probability = self.binary_relevance.boolean_token_probability(
                self.model,
                self.tokenizer,
                prompt,
            )
            scores[label] = float(probability)
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
                "truncated": largest > max_length,
            },
        )

    def provenance(self) -> Mapping[str, Any]:
        self.prepare()
        assert self.snapshot is not None
        return {
            "backend": "qwen_pairwise",
            "alias": self.alias,
            "model_id": self.model_id,
            "revision": self.revision,
            "base_model_id": self.base_model_id,
            "base_revision": self.base_revision,
            "architecture": self.inference_config["architecture"],
            "decision_method": self.inference_config["decision_method"],
            "input_mode": self.inference_config["input_mode"],
            "max_length": int(self.inference_config["max_length"]),
            "label_order": list(LABELS),
            "label_codes": dict(LABEL_CODES),
            "thresholds": dict(self.thresholds),
            "taxonomy_fingerprint": self.taxonomy_fingerprint,
            "taxonomy_file_sha256": sha256(self.snapshot / "e2r_taxonomy.yaml"),
            "reference_files": {
                name: sha256(self.snapshot / name)
                for name in RELEASE_FILES
                if (self.snapshot / name).is_file()
            },
            "quantization": dict(self.config["quantization"]),
        }

    def close(self) -> None:
        self.model = None
        self.tokenizer = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
