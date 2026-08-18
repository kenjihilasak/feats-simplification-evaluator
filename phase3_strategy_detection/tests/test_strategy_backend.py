from pathlib import Path
import sys

import pytest


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from strategy_backend import (  # noqa: E402
    BackendPrediction,
    LABELS,
    materialize_prediction,
)


def test_materialize_prediction_uses_fixed_order_and_thresholds():
    scores = {label: (index + 1) / 10 for index, label in enumerate(LABELS)}
    thresholds = {label: 0.35 for label in LABELS}
    result = materialize_prediction(
        "pair-1",
        "test-model",
        BackendPrediction(scores=scores, diagnostics={"truncated": False}),
        thresholds,
    )

    assert list(result["strategy_scores"]) == [
        "SYN", "MOD", "COMP", "EXPL", "SYNT", "OMIT"
    ]
    assert result["predicted_codes"] == ["EXPL", "SYNT", "OMIT"]
    assert result["predicted_labels"] == [
        "Explanation", "Syntactic Change", "Omission"
    ]
    assert result["strategy_count"] == 3


def test_materialize_prediction_rejects_missing_score():
    scores = {label: 0.5 for label in LABELS[:-1]}
    thresholds = {label: 0.5 for label in LABELS}

    with pytest.raises(ValueError, match="Score labels differ"):
        materialize_prediction(
            "pair-1", "test-model", BackendPrediction(scores=scores), thresholds
        )
