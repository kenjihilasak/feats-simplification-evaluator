"""Model-independent contract for Phase 3 strategy classifiers."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


LABELS = (
    "Synonymy",
    "Modulation",
    "Compression",
    "Explanation",
    "Syntactic Change",
    "Omission",
)

LABEL_CODES = {
    "Synonymy": "SYN",
    "Modulation": "MOD",
    "Compression": "COMP",
    "Explanation": "EXPL",
    "Syntactic Change": "SYNT",
    "Omission": "OMIT",
}


@dataclass(frozen=True)
class BackendPrediction:
    """Raw model probabilities and optional inference diagnostics."""

    scores: Mapping[str, float]
    diagnostics: Mapping[str, Any] = field(default_factory=dict)


class StrategyBackend(Protocol):
    """Interface that every Phase 3 model backend must implement."""

    alias: str
    thresholds: Mapping[str, float]

    def prepare(self) -> None: ...

    def load(self) -> None: ...

    def predict_pair(self, original: str, simple: str) -> BackendPrediction: ...

    def provenance(self) -> Mapping[str, Any]: ...

    def close(self) -> None: ...


def validate_thresholds(thresholds: Mapping[str, float]) -> dict[str, float]:
    """Validate and normalize thresholds in the fixed six-label order."""

    if set(thresholds) != set(LABELS):
        raise ValueError(
            "Threshold labels differ from the fixed inventory: "
            f"expected={list(LABELS)}, received={sorted(thresholds)}"
        )
    normalized = {label: float(thresholds[label]) for label in LABELS}
    if any(
        not math.isfinite(value) or not 0.0 <= value <= 1.0
        for value in normalized.values()
    ):
        raise ValueError("Every strategy threshold must be finite and within [0, 1].")
    return normalized


def normalize_scores(scores: Mapping[str, float]) -> dict[str, float]:
    """Validate and normalize scores in the fixed six-label order."""

    if set(scores) != set(LABELS):
        raise ValueError(
            "Score labels differ from the fixed inventory: "
            f"expected={list(LABELS)}, received={sorted(scores)}"
        )
    normalized = {label: float(scores[label]) for label in LABELS}
    if any(
        not math.isfinite(value) or not 0.0 <= value <= 1.0
        for value in normalized.values()
    ):
        raise ValueError("Every strategy probability must be finite and within [0, 1].")
    return normalized


def materialize_prediction(
    pair_id: str,
    model_alias: str,
    prediction: BackendPrediction,
    thresholds: Mapping[str, float],
) -> dict[str, Any]:
    """Convert backend probabilities to the stable Phase 3 JSONL schema."""

    scores = normalize_scores(prediction.scores)
    checked_thresholds = validate_thresholds(thresholds)
    predicted_labels = [
        label for label in LABELS if scores[label] >= checked_thresholds[label]
    ]
    return {
        "id": str(pair_id),
        "model_alias": str(model_alias),
        "strategy_scores": {
            LABEL_CODES[label]: scores[label] for label in LABELS
        },
        "predicted_codes": [LABEL_CODES[label] for label in predicted_labels],
        "predicted_labels": predicted_labels,
        "strategy_count": len(predicted_labels),
        "diagnostics": dict(prediction.diagnostics),
    }
