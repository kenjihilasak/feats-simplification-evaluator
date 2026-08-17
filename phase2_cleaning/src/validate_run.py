"""Validate a completed Phase 2 run record by record."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from itertools import zip_longest
from pathlib import Path

from common import (
    expected_count,
    input_files,
    input_limit,
    iter_jsonl,
    load_config,
    output_path,
    run_root,
    sha256,
    write_json,
)


COUNT_FIELDS = (
    "total_pairs",
    "kept_pairs",
    "removed_pairs",
    "complexity_inversion",
    "labse_below_min",
    "labse_above_max",
)
PERCENT_FIELDS = (
    "removed_pct",
    "complexity_inversion_pct",
    "labse_below_min_pct",
    "labse_above_max_pct",
)


def percent(count: int, total: int) -> float:
    return count / total * 100.0 if total else 0.0


def expected_reasons(complexity: dict, similarity: float, config: dict) -> list[str]:
    filters = config["filters"]
    threshold = float(filters["smp_threshold"])
    original = complexity["original"]
    simple = complexity["simple"]
    inversion = (
        original["predicted_label"] == "simple"
        and simple["predicted_label"] == "complex"
        and float(original["smp_max_mean_uncertainty"]) < threshold
        and float(simple["smp_max_mean_uncertainty"]) < threshold
    )
    reasons = []
    if inversion:
        reasons.append("complexity_inversion")
    if similarity < float(filters["labse_min"]):
        reasons.append("labse_below_min")
    if similarity > float(filters["labse_max"]):
        reasons.append("labse_above_max")
    return reasons


def output_files(root: Path, section: str) -> set[str]:
    section_root = root / section
    if not section_root.is_dir():
        return set()
    return {
        str(path.relative_to(section_root))
        for path in section_root.glob("*/*.jsonl")
        if path.is_file()
    }


def add_error(errors: list[str], message: str, maximum: int = 100) -> None:
    if len(errors) < maximum:
        errors.append(message)


def validate_file(corpus_file, config: dict, errors: list[str]) -> dict:
    label = f"{corpus_file.language}/{corpus_file.filename}"
    paths = {
        section: output_path(config, section, corpus_file)
        for section in ("scores/complexity", "scores/labse", "decisions", "cleaned")
    }
    if any(not path.is_file() for path in paths.values()):
        for section, path in paths.items():
            if not path.is_file():
                add_error(errors, f"Missing {section} file: {path}")
        return {"file": label, "complete": False}

    sources = iter_jsonl(corpus_file.path, input_limit(config))
    complexities = iter_jsonl(paths["scores/complexity"])
    similarities = iter_jsonl(paths["scores/labse"])
    decisions = iter_jsonl(paths["decisions"])
    cleaned = iter_jsonl(paths["cleaned"])
    counters = Counter()
    identity = {"source": "", "corpus": ""}

    for index, records in enumerate(
        zip_longest(sources, complexities, similarities, decisions), start=1
    ):
        source, complexity, labse, decision = records
        if any(record is None for record in records):
            add_error(errors, f"Unequal input/score/decision lengths in {label} at row {index}")
            break

        ids = (source.get("id"), complexity.get("id"), labse.get("id"), decision.get("id"))
        if len(set(ids)) != 1:
            add_error(errors, f"ID mismatch in {label} at row {index}: {ids}")

        similarity = float(labse["labse_similarity"])
        reasons = expected_reasons(complexity, similarity, config)
        keep = not reasons
        if decision.get("rejection_reasons") != reasons:
            add_error(errors, f"Incorrect rejection reasons in {label} at row {index}")
        if decision.get("keep") is not keep:
            add_error(errors, f"Incorrect keep decision in {label} at row {index}")
        if decision.get("complexity") != complexity:
            add_error(errors, f"Embedded complexity score mismatch in {label} at row {index}")
        if float(decision.get("labse_similarity")) != similarity:
            add_error(errors, f"Embedded LaBSE score mismatch in {label} at row {index}")

        counters["total_pairs"] += 1
        counters["kept_pairs" if keep else "removed_pairs"] += 1
        for reason in reasons:
            counters[reason] += 1
        identity = {"source": source.get("source", ""), "corpus": source.get("corpus", "")}

        if keep:
            clean = next(cleaned, None)
            if clean != source:
                add_error(errors, f"Cleaned/source mismatch in {label} at input row {index}")

    if next(cleaned, None) is not None:
        add_error(errors, f"Extra records in cleaned file: {label}")

    total = counters["total_pairs"]
    expected = expected_count(corpus_file, config)
    if total != expected:
        add_error(errors, f"Count mismatch in {label}: observed {total}, expected {expected}")

    row = {
        "language": corpus_file.language,
        **identity,
        "file": corpus_file.filename,
        **{field: counters[field] for field in COUNT_FIELDS},
        "removed_pct": percent(counters["removed_pairs"], total),
        "complexity_inversion_pct": percent(counters["complexity_inversion"], total),
        "labse_below_min_pct": percent(counters["labse_below_min"], total),
        "labse_above_max_pct": percent(counters["labse_above_max"], total),
        "cleaned_sha256": sha256(paths["cleaned"]),
        "complete": total == expected,
    }
    return row


def validate_report(run_path: Path, rows: list[dict], errors: list[str]) -> None:
    report_path = run_path / "reports/cleaning_summary.csv"
    if not report_path.is_file():
        add_error(errors, f"Missing report: {report_path}")
        return
    with report_path.open(newline="", encoding="utf-8") as handle:
        reported = list(csv.DictReader(handle))
    if len(reported) != len(rows):
        add_error(errors, f"Report has {len(reported)} rows; expected {len(rows)}")
        return
    for expected, observed in zip(rows, reported):
        for field in ("language", "source", "corpus", "file"):
            if str(expected[field]) != observed[field]:
                add_error(errors, f"Report field mismatch for {expected['file']}: {field}")
        for field in COUNT_FIELDS:
            if int(expected[field]) != int(observed[field]):
                add_error(errors, f"Report count mismatch for {expected['file']}: {field}")
        for field in PERCENT_FIELDS:
            if abs(float(expected[field]) - float(observed[field])) > 1e-9:
                add_error(errors, f"Report percentage mismatch for {expected['file']}: {field}")


def validate(config: dict) -> dict:
    errors: list[str] = []
    files = input_files(config)
    root = run_root(config)
    expected_layout = {f"{item.language}/{item.filename}" for item in files}
    for section in ("scores/complexity", "scores/labse", "decisions", "cleaned"):
        observed = output_files(root, section)
        if observed != expected_layout:
            missing = sorted(expected_layout - observed)
            extra = sorted(observed - expected_layout)
            add_error(errors, f"{section} layout mismatch; missing={missing}, extra={extra}")

    temporary = sorted(str(path.relative_to(root)) for path in root.rglob("*.tmp-*"))
    if temporary:
        add_error(errors, f"Temporary files remain: {temporary}")

    rows = [validate_file(item, config, errors) for item in files]
    complete_rows = [row for row in rows if row.get("complete")]
    validate_report(root, complete_rows, errors)

    config_path = root / "run_config.json"
    expected_config = {key: value for key, value in config.items() if not key.startswith("_")}
    if not config_path.is_file():
        add_error(errors, f"Missing run configuration: {config_path}")
    elif json.loads(config_path.read_text(encoding="utf-8")) != expected_config:
        add_error(errors, "run_config.json does not match the requested configuration")

    totals = Counter()
    for row in complete_rows:
        for field in COUNT_FIELDS:
            totals[field] += int(row[field])
    return {
        "valid": not errors,
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": config["run_id"],
        "files_expected": len(files),
        "files_validated": len(complete_rows),
        "totals": dict(totals),
        "errors": errors,
        "files": complete_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    config = load_config(args.config)
    result = validate(config)
    output = args.output or run_root(config) / "reports/validation.json"
    write_json(output, result)
    print(json.dumps({key: result[key] for key in ("valid", "files_validated", "totals", "errors")}, indent=2))
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
