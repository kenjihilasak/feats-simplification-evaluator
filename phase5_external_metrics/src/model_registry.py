"""Lazy external-metric backend registry."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Mapping


BACKENDS = {
    "lens_salsa": ("lens_backend", "LensSalsaBackend"),
    "referee": ("referee_backend", "RefereeBackend"),
}


def create_backend(config: Mapping[str, Any], cache_root: Path):
    name = str(config.get("backend", ""))
    if name not in BACKENDS:
        raise ValueError(f"Unknown backend {name!r}; available: {sorted(BACKENDS)}")
    module_name, class_name = BACKENDS[name]
    return getattr(importlib.import_module(module_name), class_name)(config, cache_root)

