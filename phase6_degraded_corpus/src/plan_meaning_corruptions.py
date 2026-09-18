#!/usr/bin/env python3
"""Detect opportunities and assign one reproducible meaning corruption per pair."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from contracts import read_jsonl, stable_key, write_jsonl

YEAR = re.compile(r"\b(?:1[5-9]\d{2}|20\d{2}|2100)\b")
NUMBER = re.compile(r"\b\d+(?:[.,]\d+)?%?\b")
MONTH = re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b")
ENTITY = re.compile(r"\b(?:[A-Z][\w’'-]+(?:\s+[A-Z][\w’'-]+){0,3})\b")
AUXILIARY = re.compile(r"\b(?:is|are|was|were|has|have|had|can|could|will|would|did|does|do|may|might|must|should)\b", re.I)
NEGATION = re.compile(r"\b(?:not|never|no)\b", re.I)
PROPERTY_WORDS = {
    "north", "south", "east", "west", "northern", "southern", "eastern", "western",
    "large", "small", "high", "low", "old", "new", "first", "last", "public", "private",
}
EVENT_VERBS = {
    "born", "died", "won", "lost", "founded", "built", "opened", "closed", "elected",
    "appointed", "joined", "left", "created", "destroyed", "published", "released",
}


def spans(pattern: re.Pattern, text: str) -> list[dict]:
    return [{"text": m.group(0), "start": m.start(), "end": m.end()} for m in pattern.finditer(text)]


def word_spans(text: str, vocabulary: set[str]) -> list[dict]:
    result = []
    for match in re.finditer(r"\b[\w’'-]+\b", text):
        if match.group(0).lower() in vocabulary:
            result.append({"text": match.group(0), "start": match.start(), "end": match.end()})
    return result


def detect(text: str) -> dict[str, list[dict]]:
    dates = spans(YEAR, text) + spans(MONTH, text)
    date_ranges = {(x["start"], x["end"]) for x in dates}
    numbers = [x for x in spans(NUMBER, text) if (x["start"], x["end"]) not in date_ranges]
    entities = [x for x in spans(ENTITY, text) if x["start"] != 0]
    negation = spans(NEGATION, text) or spans(AUXILIARY, text)
    properties = word_spans(text, PROPERTY_WORDS)
    events = word_spans(text, EVENT_VERBS)
    # Relation reversal needs semantic planning; an auxiliary/event is a conservative cue.
    relations = (events or spans(AUXILIARY, text))[:2]
    return {
        "entity_replacement": entities,
        "number_replacement": numbers,
        "date_replacement": dates,
        "negation_reversal": negation,
        "property_replacement": properties,
        "relation_reversal": relations,
        # Event replacement may use the explicit verb or Qwen's central-fact planner.
        "event_replacement": events or [{"text": "central event", "start": None, "end": None}],
    }


def choose(applicable: list[str], counts: Counter, targets: dict[str, int], seed: int, pair_id: str) -> str:
    if not applicable:
        raise ValueError(f"no applicable corruption for {pair_id}")
    return min(
        applicable,
        key=lambda kind: (
            counts[kind] / max(1, targets[kind]),
            stable_key(seed, f"{pair_id}:{kind}"),
        ),
    )


def plan(config: dict) -> tuple[list[dict], dict]:
    rows = read_jsonl(Path(config["input_file"]))
    targets = config["target_counts"]
    allowed = config["corruption_types"]
    counts = Counter()
    output = []
    for row in sorted(rows, key=lambda x: stable_key(config["seed"], x["canonical_pair_id"])):
        opportunities = detect(row["clean_simplification"])
        applicable = [kind for kind in allowed if opportunities.get(kind)]
        assigned = choose(applicable, counts, targets, config["seed"], row["canonical_pair_id"])
        counts[assigned] += 1
        cue = opportunities[assigned][0]
        output.append({
            "schema": "feats-phase6-corruption-plan-v1",
            "canonical_pair_id": row["canonical_pair_id"],
            "canonical_original_id": row["canonical_original_id"],
            "original": row["original"],
            "clean_simplification": row["clean_simplification"],
            "clean_source_tier": row["clean_source_tier"],
            "clean_review_status": row["clean_review_status"],
            "predicted_strategy": row["predicted_strategy"],
            "target_axis": config["target_axis"],
            "target_score": config["target_score"],
            "applicable_corruptions": applicable,
            "opportunities": opportunities,
            "assigned_corruption": assigned,
            "target_cue": cue,
            "prompt_id": "meaning_severe_v1",
            "generation_status": "ready" if row["clean_review_status"] == "accepted" else "blocked_clean_review",
        })
    report = {
        "schema": "feats-phase6-corruption-assignment-report-v1",
        "pairs": len(output),
        "assigned_by_type": dict(sorted(counts.items())),
        "ready_for_generation": sum(x["generation_status"] == "ready" for x in output),
        "blocked_clean_review": sum(x["generation_status"] == "blocked_clean_review" for x in output),
        "seed": config["seed"],
    }
    return output, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    rows, report = plan(config)
    output = Path(config["output_dir"])
    write_jsonl(output / "corruption_plan.jsonl", rows)
    (output / "assignment_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
