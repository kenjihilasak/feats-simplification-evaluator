"""Load frozen human-rating and heldout-review evaluation sets."""

from __future__ import annotations

import csv
import hashlib
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from contracts import strong_key


def load_simplicity_da(path: Path, aspect: str = "meaning") -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [{
        "evaluation_id": f"simplicity_da:{row['sent_id']}:{row['sys_name']}",
        "dataset": "simplicity_da", "original_id": f"simplicity_da:{row['sent_id']}",
        "original": row["orig_sent"], "candidate": row["simp_sent"], "system": row["sys_name"],
        "human_score": float(row[f"{aspect}_zscore"]), "human_scale": f"{aspect}_zscore",
    } for row in rows]


def load_human_likert(path: Path, aspect: str = "meaning") -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["aspect"].strip().casefold() == aspect:
                grouped[(row["sentence_id"], row["system_name"], row["simplification"])].append(row)
    result = []
    for (sentence_id, system, candidate), rows in grouped.items():
        originals = {strong_key(row["source"]): row["source"] for row in rows}
        if len(originals) != 1:
            raise ValueError(f"Inconsistent originals for Human-Likert {sentence_id}/{system}")
        result.append({
            "evaluation_id": f"human_likert:{sentence_id}:{system}:{hashlib.sha256(candidate.encode('utf-8')).hexdigest()[:12]}", "dataset": "human_likert",
            "aggregation_id": f"human_likert:{sentence_id}:{system}",
            "original_id": f"human_likert:{sentence_id}", "original": next(iter(originals.values())),
            "candidate": candidate, "system": system,
            "human_score": mean(float(row["rating"]) for row in rows), "human_scale": f"{aspect}_likert_mean",
            "rating_count": len(rows),
        })
    return sorted(result, key=lambda row: row["evaluation_id"])


def load_simpeval_2022(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [{
        "evaluation_id": f"simpeval_2022:{row['original_id']}:{row['system']}",
        "dataset": "simpeval_2022", "original_id": f"simpeval_2022:{row['original_id']}",
        "original": row["original"], "candidate": row["generation"], "system": row["system"],
        "human_score": mean(float(row[f"rating_{i}"]) for i in (1, 2, 3)),
        "human_scale": "overall_mean",
    } for row in rows]


CASE_RE = re.compile(r"^### Case (H\d+)\s*$")
FIELD_RE = re.compile(r"^\* \*\*(Axis|Source|Original|Simplified|Degraded):\*\*\s*(.*)$")
ANSWER_RE = re.compile(r"^\* \[([ xX])\] (Valid|Invalid|Unsure)\s*$")


def parse_review(path: Path) -> dict[str, dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}
    current: dict[str, Any] | None = None
    case_id = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        if match := CASE_RE.match(raw):
            case_id = match.group(1)
            current = cases.setdefault(case_id, {"case_id": case_id, "checked_answers": []})
        elif current is not None and (match := FIELD_RE.match(raw)):
            key, value = match.groups()
            value = value.strip().strip("*")
            if key == "Axis":
                value = value.split()[0].strip("`")
            current[key.casefold()] = value
        elif current is not None and (match := ANSWER_RE.match(raw)) and match.group(1).strip():
            current["checked_answers"].append(match.group(2))
    missing = [key for key, row in cases.items() if not row["checked_answers"]]
    if missing:
        raise ValueError(f"Cases without a checked review in {path}: {missing}")
    for row in cases.values():
        answers = list(dict.fromkeys(row.pop("checked_answers")))
        row["review"] = answers[0] if len(answers) == 1 else "Conflicting"
    return cases


def load_heldout_review(review_path: Path, key_path: Path) -> list[dict[str, Any]]:
    import json
    reviews = parse_review(review_path)
    keys = json.loads(key_path.read_text(encoding="utf-8"))
    if set(reviews) != set(keys):
        raise ValueError(f"Review/key mismatch: {set(reviews) ^ set(keys)}")
    result = []
    for case_id, review in reviews.items():
        key = keys[case_id]
        for review_field, key_field in (("axis", "axis"), ("source", "corpus")):
            if review[review_field].casefold() != str(key[key_field]).casefold():
                raise ValueError(f"Review/key {key_field} mismatch for {case_id}")
        result.append({
            "evaluation_id": f"heldout:{key['axis']}:{case_id}", "dataset": "heldout_review",
            "case_id": case_id, "original_id": key["canonical_original_id"],
            "canonical_pair_id": key["canonical_pair_id"], "original": review["original"],
            "clean": review["simplified"], "degraded": review["degraded"], "axis": key["axis"],
            "source": key["corpus"], "operation": key["operation"], "review": review["review"],
            "included": review["review"] in {"Valid", "Unsure"},
        })
    return result


def evaluation_originals(rows: list[dict[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in rows:
        key = strong_key(row["original"])
        result.setdefault(key, row["original"])
    return result
