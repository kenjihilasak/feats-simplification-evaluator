from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from phase4a_gold_standard.backend.cli import _import_in_batches
from phase4a_gold_standard.backend.errors import ValidationError
from phase4a_gold_standard.backend.service import AnnotationService, ServiceSettings


def task_record() -> dict[str, Any]:
    return {
        "task_id": "review:en:syn:test",
        "canonical_pair_id": "pair:en:test",
        "language": "en",
        "sources": ["fixture"],
        "source_text": "Difficult word",
        "target_text": "Easy word",
        "candidate_strategy": "SYN",
        "source_tokens": [
            {
                "index": 0,
                "text": "Difficult",
                "start": 0,
                "end": 9,
                "lemma": "difficult",
                "upos": "ADJ",
                "xpos": "JJ",
                "deprel": "amod",
                "head_index": 1,
                "parse_status": "parsed",
            },
            {"index": 1, "text": "word", "start": 10, "end": 14},
        ],
        "target_tokens": [
            {
                "index": 0,
                "text": "Easy",
                "start": 0,
                "end": 4,
                "lemma": "easy",
                "upos": "ADJ",
                "xpos": "JJ",
                "deprel": "amod",
                "head_index": 1,
                "parse_status": "parsed",
            },
            {"index": 1, "text": "word", "start": 5, "end": 9},
        ],
        "simalign_links": [{"source_index": 0, "target_index": 0}],
        "public_metadata": {
            "candidate_strategy_label": "Synonymy",
            "majority_votes": 2,
            "quality_tier": "two_of_three",
            "pool_type": "primary_single_strategy_majority_vote",
        },
        "model_votes": {"e5": "yes", "qwen": "yes", "xlmr": "no"},
        "queue_rank": 0,
    }


def test_review_submission_export_and_report(tmp_path: Path) -> None:
    service = AnnotationService(
        ServiceSettings(
            database_path=tmp_path / "annotations.sqlite3",
            session_secret="test-secret",
            lease_seconds=120,
        )
    )
    assert service.import_tasks([task_record()]) == {"inserted": 1, "unchanged": 0}
    service.create_user(
        username="reviewer-en",
        display_name="English Reviewer",
        password="correct horse battery staple",
        role="reviewer",
        allowed_languages=["en"],
    )
    _, user = service.login("reviewer-en", "correct horse battery staple")

    task = service.claim_next(user)
    assert task is not None
    assert "model_votes" not in task
    assert "majority_votes" not in task["metadata"]
    assert "quality_tier" not in task["metadata"]

    with pytest.raises(ValidationError, match="source evidence"):
        service.save(
            task["task_id"],
            user,
            annotation={"verdict": "correct"},
            expected_version=0,
            submit=True,
        )

    submitted = service.save(
        task["task_id"],
        user,
        annotation={
            "verdict": "correct",
            "source_evidence": [{"token_index": 0, "role": "replaced"}],
            "target_evidence": [{"token_index": 0, "role": "replacement"}],
            "alignment_judgments": [
                {"source_index": 0, "target_index": 0, "judgment": "valid"}
            ],
        },
        expected_version=0,
        submit=True,
    )
    assert submitted["state"] == "submitted"

    rows = list(service.database.iter_export_rows(include_model_votes=True))
    assert len(rows) == 1
    assert rows[0]["model_votes"]["majority_votes"] == 2
    assert rows[0]["model_votes"]["quality_tier"] == "two_of_three"
    assert rows[0]["source_evidence"][0]["text"] == "Difficult"
    assert rows[0]["source_evidence"][0]["lemma"] == "difficult"
    assert rows[0]["source_evidence"][0]["deprel"] == "amod"

    report = service.database.progress()
    assert report["totals"]["submitted"] == 1
    quality = service.report(
        type("Admin", (), {"role": "admin"})()
    )
    assert quality["strategy_correctness"]["overall"]["correct"] == 1
    assert quality["alignment"]["overall"]["acceptance_rate"] == 1.0


class FakeService:
    def __init__(self) -> None:
        self.batch_sizes: list[int] = []

    def import_tasks(self, records: list[dict[str, Any]]) -> dict[str, int]:
        self.batch_sizes.append(len(records))
        return {"inserted": len(records), "unchanged": 0}


def test_cli_import_batches_large_jsonl_stream() -> None:
    service = FakeService()
    result = _import_in_batches(
        service, ({"task_id": str(index)} for index in range(2005))
    )
    assert service.batch_sizes == [1000, 1000, 5]
    assert result == {"inserted": 2005, "unchanged": 0}


def test_database_backup_is_consistent(tmp_path: Path) -> None:
    service = AnnotationService(
        ServiceSettings(
            database_path=tmp_path / "annotations.sqlite3",
            session_secret="test-secret",
        )
    )
    assert service.import_tasks([task_record()]) == {"inserted": 1, "unchanged": 0}

    output = tmp_path / "backups" / "annotations.sqlite3"
    result = service.database.backup(output)
    restored = AnnotationService(
        ServiceSettings(database_path=output, session_secret="restored-secret")
    )

    assert result["bytes"] == output.stat().st_size
    assert restored.database.progress()["totals"]["total"] == 1
