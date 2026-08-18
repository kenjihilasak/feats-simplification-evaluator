"""Apply complexity-inversion and LaBSE thresholds and summarize removals."""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter
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
    write_json,
)


SUMMARY_FIELDS = [
    "language", "source", "corpus", "file", "total_pairs", "kept_pairs", "removed_pairs",
    "removed_pct", "complexity_inversion", "complexity_inversion_pct",
    "labse_below_min", "labse_below_min_pct", "labse_above_max", "labse_above_max_pct",
]


def percent(count: int, total: int) -> float:
    return count / total * 100.0 if total else 0.0


def decide_file(corpus_file, config: dict) -> dict:
    settings = config["filters"]
    smp_threshold = float(settings["smp_threshold"])
    lower = float(settings["labse_min"])
    upper = float(settings["labse_max"])
    source_records = iter_jsonl(corpus_file.path, input_limit(config))
    complexity_records = iter_jsonl(output_path(config, "scores/complexity", corpus_file))
    labse_records = iter_jsonl(output_path(config, "scores/labse", corpus_file))

    cleaned_path = output_path(config, "cleaned", corpus_file)
    decisions_path = output_path(config, "decisions", corpus_file)
    counters = Counter()
    identity = {}

    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    decisions_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_tmp = cleaned_path.with_suffix(cleaned_path.suffix + f".tmp-{os.getpid()}")
    decisions_tmp = decisions_path.with_suffix(decisions_path.suffix + f".tmp-{os.getpid()}")
    try:
        cleaned_handle = cleaned_tmp.open("w", encoding="utf-8")
        decisions_handle = decisions_tmp.open("w", encoding="utf-8")
        for source, complexity, labse in zip_longest(source_records, complexity_records, labse_records):
            if source is None or complexity is None or labse is None:
                raise RuntimeError(f"Unequal input/score lengths for {corpus_file.path}")
            if not (source["id"] == complexity["id"] == labse["id"]):
                raise RuntimeError(f"Score ID mismatch at {source['id']} in {corpus_file.path}")

            original = complexity["original"]
            simple = complexity["simple"]
            inversion = (
                original["predicted_label"] == "simple"
                and simple["predicted_label"] == "complex"
                and original["smp_max_mean_uncertainty"] < smp_threshold
                and simple["smp_max_mean_uncertainty"] < smp_threshold
            )
            similarity = float(labse["labse_similarity"])
            below = similarity < lower
            above = similarity > upper
            reasons = []
            if inversion:
                reasons.append("complexity_inversion")
            if below:
                reasons.append("labse_below_min")
            if above:
                reasons.append("labse_above_max")
            keep = not reasons

            counters["total_pairs"] += 1
            counters["kept_pairs" if keep else "removed_pairs"] += 1
            counters["complexity_inversion"] += int(inversion)
            counters["labse_below_min"] += int(below)
            counters["labse_above_max"] += int(above)
            identity.update(source=source["source"], corpus=source["corpus"])
            decision = {
                "id": source["id"],
                "keep": keep,
                "rejection_reasons": reasons,
                "labse_similarity": similarity,
                "complexity": complexity,
            }
            decisions_handle.write(json.dumps(decision, ensure_ascii=False, separators=(",", ":")) + "\n")
            if keep:
                cleaned_handle.write(json.dumps(source, ensure_ascii=False, separators=(",", ":")) + "\n")
        cleaned_handle.close()
        decisions_handle.close()
        cleaned_tmp.replace(cleaned_path)
        decisions_tmp.replace(decisions_path)
    except Exception:
        if "cleaned_handle" in locals():
            cleaned_handle.close()
        if "decisions_handle" in locals():
            decisions_handle.close()
        cleaned_tmp.unlink(missing_ok=True)
        decisions_tmp.unlink(missing_ok=True)
        raise
    total = counters["total_pairs"]
    return {
        "language": corpus_file.language,
        "source": identity.get("source", ""),
        "corpus": identity.get("corpus", ""),
        "file": corpus_file.filename,
        "total_pairs": total,
        "kept_pairs": counters["kept_pairs"],
        "removed_pairs": counters["removed_pairs"],
        "removed_pct": percent(counters["removed_pairs"], total),
        "complexity_inversion": counters["complexity_inversion"],
        "complexity_inversion_pct": percent(counters["complexity_inversion"], total),
        "labse_below_min": counters["labse_below_min"],
        "labse_below_min_pct": percent(counters["labse_below_min"], total),
        "labse_above_max": counters["labse_above_max"],
        "labse_above_max_pct": percent(counters["labse_above_max"], total),
    }


def write_reports(config: dict, rows: list[dict]) -> None:
    report_dir = run_root(config) / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / "cleaning_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    totals = Counter()
    for row in rows:
        for field in ("total_pairs", "kept_pairs", "removed_pairs", "complexity_inversion", "labse_below_min", "labse_above_max"):
            totals[field] += int(row[field])
    total = totals["total_pairs"]
    config_copy = {key: value for key, value in config.items() if not key.startswith("_")}
    write_json(run_root(config) / "run_config.json", config_copy)
    lines = [
        "# Cleaning summary", "",
        f"- Input pairs: **{total:,}**",
        f"- Retained: **{totals['kept_pairs']:,}** ({percent(totals['kept_pairs'], total):.2f}%)",
        f"- Removed by the union of filters: **{totals['removed_pairs']:,}** ({percent(totals['removed_pairs'], total):.2f}%)",
        f"- Confident complexity inversions: {totals['complexity_inversion']:,} ({percent(totals['complexity_inversion'], total):.2f}%)",
        f"- LaBSE < {config['filters']['labse_min']}: {totals['labse_below_min']:,} ({percent(totals['labse_below_min'], total):.2f}%)",
        f"- LaBSE > {config['filters']['labse_max']}: {totals['labse_above_max']:,} ({percent(totals['labse_above_max'], total):.2f}%)",
        "", "## By language and corpus", "",
        "| Language | Source | Corpus | Input | Kept | Removed | Removed % | Complexity inversion % | LaBSE low % | LaBSE high % |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['language']} | {row['source']} | {row['corpus']} | {row['total_pairs']:,} | "
            f"{row['kept_pairs']:,} | {row['removed_pairs']:,} | {row['removed_pct']:.2f} | "
            f"{row['complexity_inversion_pct']:.2f} | {row['labse_below_min_pct']:.2f} | {row['labse_above_max_pct']:.2f} |"
        )
    qualitative_reports = [
        ("qualitative_examples_en_es.md", "English and Spanish examples"),
        ("qualitative_examples_idem_saaq.md", "iDEM and Saaq al-Bambuu examples"),
    ]
    available_reports = [item for item in qualitative_reports if (report_dir / item[0]).is_file()]
    if available_reports:
        lines.extend([
            "",
            "## Qualitative spot check",
            "",
        ])
        for filename, label in available_reports:
            lines.append(f"- See [the {label}]({filename}).")
    (report_dir / "cleaning_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(config: dict) -> None:
    rows = []
    for corpus_file in input_files(config):
        expected = expected_count(corpus_file, config)
        for score_type in ("complexity", "labse"):
            score_path = output_path(config, f"scores/{score_type}", corpus_file)
            if not score_path.is_file():
                raise FileNotFoundError(score_path)
        print(f"[decisions] {corpus_file.language}/{corpus_file.filename} ({expected:,})", flush=True)
        rows.append(decide_file(corpus_file, config))
    write_reports(config, rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    run(load_config(args.config))


if __name__ == "__main__":
    main()
