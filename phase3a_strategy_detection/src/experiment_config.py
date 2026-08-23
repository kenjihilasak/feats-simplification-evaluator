"""Resolve legacy single-model runs and shared multi-model experiments."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


@dataclass(frozen=True)
class ResolvedRun:
    config_path: Path
    requested_config: dict[str, Any]
    model_config_path: Path | None
    model_config: dict[str, Any]
    experiment_id: str
    input_root: Path
    runs_root: Path
    cache_root: Path
    selection: dict[str, Any]
    experiment_root: Path
    model_root: Path
    manifest_path: Path
    legacy: bool


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def resolve_run(config_path: Path, model_alias: str | None = None) -> ResolvedRun:
    config_path = config_path.resolve()
    requested = load_json(config_path)

    if "run_id" in requested and "model" in requested:
        configured_alias = str(requested["model"]["alias"])
        if model_alias is not None and model_alias != configured_alias:
            raise ValueError(
                f"Legacy config contains only model {configured_alias!r}, "
                f"not {model_alias!r}."
            )
        runs_root = project_path(requested["runs_root"])
        root = runs_root / str(requested["run_id"])
        return ResolvedRun(
            config_path=config_path,
            requested_config=requested,
            model_config_path=None,
            model_config=dict(requested["model"]),
            experiment_id=str(requested["run_id"]),
            input_root=project_path(requested["input_root"]),
            runs_root=runs_root,
            cache_root=project_path(requested["cache_root"]),
            selection=dict(requested["selection"]),
            experiment_root=root,
            model_root=root,
            manifest_path=root / "input_manifest.csv",
            legacy=True,
        )

    if requested.get("schema") != "feats-phase3-experiment-v2":
        raise ValueError(
            "Expected a legacy run config or schema feats-phase3-experiment-v2."
        )
    models = requested.get("models")
    if not isinstance(models, dict) or not models:
        raise ValueError("Experiment models must be a non-empty alias-to-path map.")
    if model_alias is None:
        raise ValueError(
            "--model-alias is required for a multi-model experiment. "
            f"Available: {sorted(models)}"
        )
    if model_alias not in models:
        raise ValueError(
            f"Unknown experiment model {model_alias!r}; available: {sorted(models)}"
        )

    model_path = project_path(str(models[model_alias])).resolve()
    model_config = load_json(model_path)
    if model_config.get("schema") != "feats-phase3-model-v1":
        raise ValueError(f"Unexpected model-config schema: {model_path}")
    if model_config.get("alias") != model_alias:
        raise ValueError(
            f"Model alias/path mismatch: key={model_alias!r}, "
            f"config={model_config.get('alias')!r}"
        )

    runs_root = project_path(requested["runs_root"])
    experiment_id = str(requested["experiment_id"])
    experiment_root = runs_root / experiment_id
    return ResolvedRun(
        config_path=config_path,
        requested_config=requested,
        model_config_path=model_path,
        model_config=model_config,
        experiment_id=experiment_id,
        input_root=project_path(requested["input_root"]),
        runs_root=runs_root,
        cache_root=project_path(requested["cache_root"]),
        selection=dict(requested["selection"]),
        experiment_root=experiment_root,
        model_root=experiment_root / "models" / model_alias,
        manifest_path=experiment_root / "input_manifest.csv",
        legacy=False,
    )
