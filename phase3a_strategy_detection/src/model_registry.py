"""Registry for Phase 3a strategy-classifier backends."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Mapping

from strategy_backend import StrategyBackend


BACKENDS = {
    "encoder_multilabel": ("encoder_multilabel", "EncoderMultilabelBackend"),
    "qwen_pairwise": ("qwen_pairwise", "QwenPairwiseBackend"),
}


def create_backend(
    model_config: Mapping[str, Any],
    cache_root: Path,
) -> StrategyBackend:
    """Instantiate the backend named in a run configuration."""

    backend_name = str(model_config.get("backend", ""))
    if backend_name not in BACKENDS:
        raise ValueError(
            f"Unknown strategy backend {backend_name!r}. "
            f"Available backends: {sorted(BACKENDS)}"
        )
    module_name, class_name = BACKENDS[backend_name]
    module = importlib.import_module(module_name)
    backend_class = getattr(module, class_name)
    return backend_class(dict(model_config), cache_root=cache_root)
