"""Deterministic campaign exports and aggregate quality reports."""

from __future__ import annotations

import csv
import io
from collections import Counter
from typing import Any, Iterable, Mapping, Sequence

from .security import canonical_json


EXPORT_COLUMNS = (
    "export_schema",
    "campaign_id",
    "task_id",
    "canonical_pair_id",
    "language",
    "sources",
    "source_text",
    "target_text",
    "candidate_strategy",
    "annotation_state",
    "annotation_version",
    "verdict",
    "corrected_strategy",
    "reviewer_username",
    "reviewer_display_name",
    "source_evidence",
    "target_evidence",
    "simalign_links",
    "alignment_judgments",
    "human_added_links",
    "notes",
    "skip_reason",
    "started_at",
    "updated_at",
    "submitted_at",
    "active_duration_seconds",
    "model_votes",
)


def render_jsonl(records: Iterable[Mapping[str, Any]]) -> str:
    return "".join(canonical_json(dict(record)) + "\n" for record in records)


def render_csv(records: Iterable[Mapping[str, Any]]) -> str:
    """Render a stable UTF-8 CSV; nested values remain canonical JSON."""

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=EXPORT_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for record in records:
        row: dict[str, Any] = {}
        for key in EXPORT_COLUMNS:
            value = record.get(key)
            if isinstance(value, (dict, list, tuple)):
                value = canonical_json(value)
            row[key] = value
        writer.writerow(row)
    return output.getvalue()


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def _correctness_bucket() -> dict[str, int]:
    return {
        "submitted_denominator": 0,
        "correct": 0,
        "incorrect": 0,
        "uncertain": 0,
    }


def _correctness_result(bucket: Mapping[str, int]) -> dict[str, Any]:
    submitted = int(bucket["submitted_denominator"])
    correct = int(bucket["correct"])
    incorrect = int(bucket["incorrect"])
    uncertain = int(bucket["uncertain"])
    determinate = correct + incorrect
    return {
        "submitted_denominator": submitted,
        "determinate_denominator": determinate,
        "correct": correct,
        "incorrect": incorrect,
        "uncertain": uncertain,
        "correct_rate_among_determinate": _ratio(correct, determinate),
        "correct_rate_among_submitted": _ratio(correct, submitted),
        "uncertain_rate": _ratio(uncertain, submitted),
    }


def _alignment_bucket() -> dict[str, int]:
    return {
        "submitted_tasks": 0,
        "tasks_with_judgments": 0,
        "available_simalign_links": 0,
        "judged_denominator": 0,
        "valid": 0,
        "invalid": 0,
        "human_added_links": 0,
    }


def _alignment_result(bucket: Mapping[str, int]) -> dict[str, Any]:
    result = {key: int(value) for key, value in bucket.items()}
    result["acceptance_rate"] = _ratio(result["valid"], result["judged_denominator"])
    result["judgment_coverage_rate"] = _ratio(
        result["judged_denominator"], result["available_simalign_links"]
    )
    return result


def _dimension_rows(
    values: Mapping[str, Mapping[str, int]], converter: Any, name: str
) -> list[dict[str, Any]]:
    return [{name: key, **converter(values[key])} for key in sorted(values)]


def _stable_progress(progress: Mapping[str, Any] | None) -> dict[str, Any]:
    if progress is None:
        return {}

    def clean(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                key: clean(value[key])
                for key in sorted(value)
                if key != "generated_at"
            }
        if isinstance(value, list):
            if all(isinstance(item, Mapping) and "username" in item for item in value):
                value = sorted(value, key=lambda item: str(item["username"]))
            return [clean(item) for item in value]
        return value

    return clean(progress)


def build_report(
    records: Sequence[Mapping[str, Any]], *, progress: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Build the Phase 4a report with explicit, auditable denominators.

    Only submitted annotations contribute to linguistic quality measures.
    Drafts and skipped tasks remain visible in the progress section.
    """

    correctness_overall = _correctness_bucket()
    correctness_dimensions: dict[str, dict[str, dict[str, int]]] = {
        "language": {},
        "source": {},
        "strategy": {},
    }
    alignment_overall = _alignment_bucket()
    alignment_dimensions: dict[str, dict[str, dict[str, int]]] = {
        "language": {},
        "source": {},
        "strategy": {},
    }
    evidence_tokens: Counter[tuple[str, str, str, str, str, str, str]] = Counter()
    evidence_pos: Counter[tuple[str, str, str, str]] = Counter()
    corrected: Counter[str] = Counter()

    def dimension_values(record: Mapping[str, Any]) -> dict[str, list[str]]:
        sources = sorted({str(value) for value in record.get("sources", [])})
        return {
            "language": [str(record["language"])],
            "source": sources or ["<unspecified>"],
            "strategy": [str(record["candidate_strategy"])],
        }

    def correctness_add(bucket: dict[str, int], verdict: str) -> None:
        bucket["submitted_denominator"] += 1
        bucket[verdict] += 1

    def alignment_add(bucket: dict[str, int], record: Mapping[str, Any]) -> None:
        judgments = list(record.get("alignment_judgments") or [])
        bucket["submitted_tasks"] += 1
        bucket["available_simalign_links"] += len(record.get("simalign_links") or [])
        if judgments:
            bucket["tasks_with_judgments"] += 1
        bucket["judged_denominator"] += len(judgments)
        bucket["valid"] += sum(item.get("judgment") == "valid" for item in judgments)
        bucket["invalid"] += sum(item.get("judgment") == "invalid" for item in judgments)
        bucket["human_added_links"] += len(record.get("human_added_links") or [])

    submitted_records = sorted(
        (record for record in records if record.get("annotation_state") == "submitted"),
        key=lambda record: (str(record.get("language")), str(record.get("task_id"))),
    )
    for record in submitted_records:
        verdict = str(record.get("verdict"))
        if verdict not in {"correct", "incorrect", "uncertain"}:
            continue
        values = dimension_values(record)
        correctness_add(correctness_overall, verdict)
        alignment_add(alignment_overall, record)
        for dimension, keys in values.items():
            for key in keys:
                correctness_bucket = correctness_dimensions[dimension].setdefault(
                    key, _correctness_bucket()
                )
                correctness_add(correctness_bucket, verdict)
                alignment_bucket = alignment_dimensions[dimension].setdefault(
                    key, _alignment_bucket()
                )
                alignment_add(alignment_bucket, record)
        if record.get("corrected_strategy"):
            corrected[str(record["corrected_strategy"])] += 1

        for side in ("source", "target"):
            for evidence in record.get(f"{side}_evidence") or []:
                language = str(record["language"])
                role = str(evidence.get("role") or "")
                text = str(evidence.get("text") or "")
                upos = str(evidence.get("upos") or "UNKNOWN")
                xpos = str(evidence.get("xpos") or "")
                strategy = str(record["candidate_strategy"])
                evidence_tokens[(language, strategy, side, role, text, upos, xpos)] += 1
                evidence_pos[(language, side, role, upos)] += 1

    correctness = {
        "overall": _correctness_result(correctness_overall),
        "by_language": _dimension_rows(
            correctness_dimensions["language"], _correctness_result, "language"
        ),
        "by_source": _dimension_rows(
            correctness_dimensions["source"], _correctness_result, "source"
        ),
        "by_strategy": _dimension_rows(
            correctness_dimensions["strategy"], _correctness_result, "strategy"
        ),
        "corrected_strategy_counts": [
            {"corrected_strategy": key, "count": corrected[key]} for key in sorted(corrected)
        ],
    }
    alignment = {
        "overall": _alignment_result(alignment_overall),
        "by_language": _dimension_rows(
            alignment_dimensions["language"], _alignment_result, "language"
        ),
        "by_source": _dimension_rows(
            alignment_dimensions["source"], _alignment_result, "source"
        ),
        "by_strategy": _dimension_rows(
            alignment_dimensions["strategy"], _alignment_result, "strategy"
        ),
    }
    evidence = {
        "selected_token_denominator": sum(evidence_tokens.values()),
        "tokens": [
            {
                "language": key[0],
                "strategy": key[1],
                "side": key[2],
                "role": key[3],
                "text": key[4],
                "upos": key[5],
                "xpos": key[6] or None,
                "count": count,
            }
            for key, count in sorted(evidence_tokens.items())
        ],
        "pos": [
            {
                "language": key[0],
                "side": key[1],
                "role": key[2],
                "upos": key[3],
                "count": count,
            }
            for key, count in sorted(evidence_pos.items())
        ],
    }
    campaign_id = str(records[0].get("campaign_id")) if records else None
    return {
        "report_schema": "feats-phase4a-quality-report-v1",
        "campaign_id": campaign_id,
        "strategy_correctness": correctness,
        "evidence": evidence,
        "alignment": alignment,
        "progress": _stable_progress(progress),
    }
