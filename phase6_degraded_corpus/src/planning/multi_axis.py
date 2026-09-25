"""Shared detection and allocation logic for the Phase 6 multi-axis corpus."""

from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

from phase6_degraded_corpus.src.common.contracts import stable_key
from phase6_degraded_corpus.src.planning.plan_meaning_corruptions import detect as detect_meaning

AXES = ("MEANING", "FLUENCY", "OMIT", "SYN", "MOD", "ILLOC", "EXPL")
DIRECT_AXES = {"OMIT", "SYN", "MOD", "EXPL"}
GENERIC_AXES = {"MEANING", "FLUENCY", "ILLOC"}

TOKEN = re.compile(r"\b[\w’'-]+\b")
QUESTION = re.compile(r"\?\s*$")
MODAL = re.compile(
    r"\b(?:can|could|may|might|must|shall|should|will|would|need|ought)\b", re.I
)
REQUEST = re.compile(
    r"\b(?:please|tell|ask|recommend|suggest|advise|request|order|promise|warn)\b", re.I
)
CERTAINTY = re.compile(
    r"\b(?:certainly|definitely|probably|possibly|perhaps|believe|think|know)\b", re.I
)
DETERMINER = re.compile(r"\b(?:a|an|the|this|that|these|those)\b", re.I)
PREPOSITION = re.compile(
    r"\b(?:at|by|for|from|in|into|of|on|over|to|under|with|without)\b", re.I
)
AUXILIARY = re.compile(
    r"\b(?:am|are|is|was|were|be|been|being|do|does|did|has|have|had)\b", re.I
)


def _matches(pattern: re.Pattern, text: str) -> list[dict]:
    return [
        {"text": match.group(0), "start": match.start(), "end": match.end()}
        for match in pattern.finditer(text)
    ]


def _token_difference(left: str, right: str) -> list[str]:
    right_words = {token.lower() for token in TOKEN.findall(right)}
    return [token for token in TOKEN.findall(left) if token.lower() not in right_words]


def detect_fluency(text: str) -> list[dict]:
    """Return conservative local sites where one grammatical error can be injected."""
    opportunities: list[dict] = []
    for operation, pattern in (
        ("agreement_error", AUXILIARY),
        ("determiner_error", DETERMINER),
        ("preposition_error", PREPOSITION),
    ):
        for cue in _matches(pattern, text)[:2]:
            opportunities.append({"operation": operation, **cue})
    words = list(TOKEN.finditer(text))
    if len(words) >= 5:
        cue = words[min(2, len(words) - 1)]
        opportunities.append(
            {
                "operation": "local_word_order_error",
                "text": cue.group(0),
                "start": cue.start(),
                "end": cue.end(),
            }
        )
    return opportunities


def detect_illocution(original: str, simple: str) -> list[dict]:
    """Find explicit speech-act or modality cues in either side of the pair."""
    opportunities: list[dict] = []
    if bool(QUESTION.search(original)) != bool(QUESTION.search(simple)):
        opportunities.append(
            {"operation": "question_statement_reversal", "text": "?", "start": None, "end": None}
        )
    for operation, pattern in (
        ("modality_reversal", MODAL),
        ("request_assertion_reversal", REQUEST),
        ("certainty_reversal", CERTAINTY),
    ):
        source = _matches(pattern, simple) or _matches(pattern, original)
        for cue in source[:2]:
            opportunities.append({"operation": operation, **cue})
    return opportunities


def detect_direct_operation(source_strategy: str, original: str, simple: str) -> list[dict]:
    """Create an operation cue for a strategy already detected by Phase 3a."""
    if source_strategy == "OMIT":
        removed = _token_difference(original, simple)
        text = " ".join(removed[:8]) or "omitted original detail"
        return [{"operation": "restore_omitted_complex_detail", "text": text, "start": None, "end": None}]
    if source_strategy == "SYN":
        restored = _token_difference(original, simple)
        text = " ".join(restored[:4]) or "complex original expression"
        return [{"operation": "restore_complex_lexical_item", "text": text, "start": None, "end": None}]
    if source_strategy == "MOD":
        return [{"operation": "reverse_information_restructuring", "text": "sentence structure", "start": None, "end": None}]
    if source_strategy == "EXPL":
        added = _token_difference(simple, original)
        text = " ".join(added[:8]) or "added explanation"
        return [{"operation": "remove_added_explanation", "text": text, "start": None, "end": None}]
    return []


def applicability(row: dict) -> dict[str, list[dict]]:
    original = row["original"]
    simple = row["clean_simplification"]
    source_strategy = row["source_strategy"]
    meaning = []
    for operation, cues in detect_meaning(simple).items():
        meaning.extend({"operation": operation, **cue} for cue in cues)
    result = {
        "MEANING": meaning,
        "FLUENCY": detect_fluency(simple),
        "ILLOC": detect_illocution(original, simple),
    }
    for axis in DIRECT_AXES:
        result[axis] = (
            detect_direct_operation(axis, original, simple)
            if source_strategy == axis
            else []
        )
    return result


def allocate(rows: Iterable[dict], seed: int) -> tuple[list[dict], dict]:
    """Assign each applicable pair once with deterministic constrained balancing."""
    rows = list(rows)
    pair_ids = [row["canonical_pair_id"] for row in rows]
    if len(pair_ids) != len(set(pair_ids)):
        raise ValueError("duplicate canonical_pair_id in candidate inventory")

    prepared = []
    for row in rows:
        matrix = applicability(row)
        applicable_axes = [axis for axis in AXES if matrix.get(axis)]
        prepared.append((row, matrix, applicable_axes))

    counts: Counter = Counter()
    assignments: list[dict] = []
    unassigned: list[dict] = []

    # MOD is protected and removed from the competition for generic axes.
    protected = [item for item in prepared if item[0]["source_strategy"] == "MOD"]
    remaining = [item for item in prepared if item[0]["source_strategy"] != "MOD"]
    ordered = protected + sorted(
        remaining,
        key=lambda item: (
            len(item[2]),
            stable_key(seed, item[0]["canonical_pair_id"]),
        ),
    )
    for row, matrix, applicable_axes in ordered:
        if row["source_strategy"] == "MOD":
            choices = ["MOD"] if matrix["MOD"] else []
        else:
            choices = applicable_axes
        if not choices:
            unassigned.append(row)
            continue
        direct = row["source_strategy"] if row["source_strategy"] in DIRECT_AXES else None
        axis = min(
            choices,
            key=lambda candidate: (
                counts[candidate],
                0 if candidate == direct else 1,
                stable_key(seed, f'{row["canonical_pair_id"]}:{candidate}'),
            ),
        )
        cues = matrix[axis]
        cue = min(
            cues,
            key=lambda value: stable_key(
                seed, f'{row["canonical_pair_id"]}:{axis}:{value["operation"]}:{value["text"]}'
            ),
        )
        counts[axis] += 1
        assignments.append(
            {
                **row,
                "schema": "feats-phase6-degradation-plan-v2",
                "target_axis": axis,
                "clean_score": 1.0,
                "degraded_score": 0.0,
                "applicable_axes": applicable_axes,
                "applicability": matrix,
                "assigned_operation": cue["operation"],
                "target_cue": cue,
                "prompt_id": f"{axis.lower()}_degradation_v1",
                "generation_status": "ready_for_pilot",
            }
        )

    assignments.sort(key=lambda row: row["canonical_pair_id"])
    axis_source = {
        axis: dict(sorted(Counter(row["source_strategy"] for row in assignments if row["target_axis"] == axis).items()))
        for axis in AXES
    }
    report = {
        "schema": "feats-phase6-assignment-report-v2",
        "candidate_pairs": len(rows),
        "assigned_pairs": len(assignments),
        "unassigned_pairs": len(unassigned),
        "assigned_by_axis": {axis: counts[axis] for axis in AXES},
        "assigned_by_source_strategy": dict(sorted(Counter(row["source_strategy"] for row in assignments).items())),
        "assigned_by_axis_and_source_strategy": axis_source,
        "direct_matches": sum(row["source_strategy"] == row["target_axis"] for row in assignments),
        "seed": seed,
    }
    return assignments, report

