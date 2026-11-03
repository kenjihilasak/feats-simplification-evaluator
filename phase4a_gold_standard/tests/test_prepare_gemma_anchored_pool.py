from __future__ import annotations

from pathlib import Path
import sys

import pytest


TESTS = Path(__file__).resolve().parent
SRC = TESTS.parent / "src"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(SRC))

from test_prepare_annotation_pool import alignment, candidate
from prepare_gemma_anchored_pool import (
    GEMMA_ALIAS,
    POOL_TYPE,
    SELECTION_RULE,
    candidate_to_records,
)


def anchored_candidate() -> dict[str, object]:
    row = candidate(
        "pair:en:strict",
        "A complex source",
        "A simple source",
        "SYN",
        ("qwen",),
        quality="gemma_plus_1_exact_singleton",
    )
    predictions = row["model_predictions"]
    assert isinstance(predictions, dict)
    predictions[GEMMA_ALIAS] = {
        "predicted_codes": ["SYN"],
        "strategy_count": 1,
        "strategy_scores": {
            code: (0.9 if code == "SYN" else 0.1)
            for code in ("SYN", "MOD", "COMP", "EXPL", "SYNT", "OMIT")
        },
    }
    row.update(
        {
            "selection_rule": SELECTION_RULE,
            "anchor_model": GEMMA_ALIAS,
            "confirming_models": ["qwen2p5_7b_pairwise_qlora"],
            "majority_votes": 2,
        }
    )
    return row


def test_gemma_anchor_and_one_exact_confirmation_build_valid_task() -> None:
    row = anchored_candidate()
    csv_record, payload, _ = candidate_to_records(row, alignment(row), POOL_TYPE)
    assert csv_record["majority_votes"] == 2
    assert csv_record["qwen_supports_strategy"] == "yes"
    assert csv_record["e5_supports_strategy"] == "no"
    assert payload["model_votes"] == {
        "gemma": "yes",
        "e5": "no",
        "qwen": "yes",
        "xlmr": "no",
    }
    assert payload["task_id"].startswith("review:en:syn:")


def test_invalid_gemma_anchor_is_rejected() -> None:
    row = anchored_candidate()
    predictions = row["model_predictions"]
    assert isinstance(predictions, dict)
    predictions[GEMMA_ALIAS]["predicted_codes"] = ["OMIT"]
    with pytest.raises(ValueError, match="Invalid Gemma anchor"):
        candidate_to_records(row, alignment(row), POOL_TYPE)
