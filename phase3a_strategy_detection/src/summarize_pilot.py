"""Summarize Phase 3a pilot quality, cardinality, and projected cost."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from strategy_backend import LABEL_CODES, LABELS


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODES = tuple(LABEL_CODES[label] for label in LABELS)


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            yield json.loads(line)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def percent(numerator: int, denominator: int) -> float:
    return 100.0 * numerator / denominator if denominator else 0.0


def summarize_group(
    key: tuple[str, ...],
    items: list[tuple[dict[str, Any], dict[str, Any]]],
    names: tuple[str, ...],
) -> dict[str, Any]:
    counts = Counter(
        code
        for _, prediction in items
        for code in prediction["predicted_codes"]
    )
    pair_count = len(items)
    cardinalities = [
        int(prediction["strategy_count"]) for _, prediction in items
    ]
    row: dict[str, Any] = dict(zip(names, key))
    row.update(
        {
            "pairs": pair_count,
            "mean_strategy_count": (
                sum(cardinalities) / pair_count if pair_count else 0.0
            ),
            "zero_strategy_pct": percent(
                sum(value == 0 for value in cardinalities), pair_count
            ),
            "multilabel_pct": percent(
                sum(value >= 2 for value in cardinalities), pair_count
            ),
        }
    )
    for code in CODES:
        row[f"{code}_pct"] = percent(counts[code], pair_count)
    return row


def grouped_rows(
    joined: list[tuple[dict[str, Any], dict[str, Any]]],
    fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    grouped: defaultdict[
        tuple[str, ...], list[tuple[dict[str, Any], dict[str, Any]]]
    ] = defaultdict(list)
    for metadata, prediction in joined:
        key = tuple(str(metadata[field]) for field in fields)
        grouped[key].append((metadata, prediction))
    return [
        summarize_group(key, grouped[key], fields)
        for key in sorted(grouped)
    ]


def agreement(
    joined: list[tuple[dict[str, Any], dict[str, Any]]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    labelled = [
        (metadata, prediction)
        for metadata, prediction in joined
        if metadata.get("is_labelled") is True
        and isinstance(metadata.get("strategy_labels"), list)
    ]
    rows: list[dict[str, Any]] = []
    totals = Counter()
    exact = 0
    hamming_errors = 0
    reference_cardinality = 0
    predicted_cardinality = 0

    for metadata, prediction in labelled:
        reference = set(metadata["strategy_labels"])
        predicted = set(prediction["predicted_labels"])
        exact += reference == predicted
        hamming_errors += len(reference.symmetric_difference(predicted))
        reference_cardinality += len(reference)
        predicted_cardinality += len(predicted)

    for label in LABELS:
        tp = fp = fn = tn = 0
        for metadata, prediction in labelled:
            reference = label in metadata["strategy_labels"]
            predicted = label in prediction["predicted_labels"]
            tp += reference and predicted
            fp += (not reference) and predicted
            fn += reference and (not predicted)
            tn += (not reference) and (not predicted)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = (
            2.0 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        rows.append(
            {
                "code": LABEL_CODES[label],
                "label": label,
                "pairs": len(labelled),
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }
        )
        totals.update({"tp": tp, "fp": fp, "fn": fn, "tn": tn})

    micro_precision = (
        totals["tp"] / (totals["tp"] + totals["fp"])
        if totals["tp"] + totals["fp"]
        else 0.0
    )
    micro_recall = (
        totals["tp"] / (totals["tp"] + totals["fn"])
        if totals["tp"] + totals["fn"]
        else 0.0
    )
    micro_f1 = (
        2.0 * micro_precision * micro_recall
        / (micro_precision + micro_recall)
        if micro_precision + micro_recall
        else 0.0
    )
    summary = {
        "labelled_pairs": len(labelled),
        "exact_match": exact / len(labelled) if labelled else 0.0,
        "hamming_loss": (
            hamming_errors / (len(labelled) * len(LABELS))
            if labelled
            else 0.0
        ),
        "micro_precision": micro_precision,
        "micro_recall": micro_recall,
        "micro_f1": micro_f1,
        "macro_f1": (
            sum(row["f1"] for row in rows) / len(rows) if rows else 0.0
        ),
        "mean_reference_strategy_count": (
            reference_cardinality / len(labelled) if labelled else 0.0
        ),
        "mean_predicted_strategy_count": (
            predicted_cardinality / len(labelled) if labelled else 0.0
        ),
    }
    return summary, rows


def agreement_grouped_rows(
    joined: list[tuple[dict[str, Any], dict[str, Any]]],
    fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    grouped: defaultdict[
        tuple[str, ...], list[tuple[dict[str, Any], dict[str, Any]]]
    ] = defaultdict(list)
    for metadata, prediction in joined:
        if metadata.get("is_labelled") is not True:
            continue
        if not isinstance(metadata.get("strategy_labels"), list):
            continue
        key = tuple(str(metadata[field]) for field in fields)
        grouped[key].append((metadata, prediction))

    rows = []
    for key in sorted(grouped):
        summary, _ = agreement(grouped[key])
        rows.append({**dict(zip(fields, key)), **summary})
    return rows


def markdown_text(value: object, limit: int = 500) -> str:
    text = str(value).replace("\n", " ").replace("|", "\\|").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def example_row(
    metadata: dict[str, Any],
    prediction: dict[str, Any],
) -> str:
    scores = ", ".join(
        f"{code}={float(prediction['strategy_scores'][code]):.3f}"
        for code in CODES
    )
    predicted = ", ".join(prediction["predicted_codes"]) or "none"
    reference_labels = metadata.get("strategy_labels")
    reference = (
        ", ".join(LABEL_CODES[label] for label in reference_labels)
        if isinstance(reference_labels, list)
        else "not labelled upstream"
    )
    source = (
        f"{metadata['source']} / {metadata['corpus']} / "
        f"{metadata['language']}"
    )
    return (
        f"| {markdown_text(metadata['original'])} "
        f"| {markdown_text(metadata['simple'])} "
        f"| {predicted} | {reference} | {scores} | {markdown_text(source)} |"
    )


def qualitative_report(
    path: Path,
    joined: list[tuple[dict[str, Any], dict[str, Any]]],
    threshold_by_code: dict[str, float],
) -> None:
    labelled = [
        item
        for item in joined
        if item[0].get("is_labelled") is True
        and isinstance(item[0].get("strategy_labels"), list)
    ]
    disagreements = sorted(
        labelled,
        key=lambda item: (
            len(
                set(item[0]["strategy_labels"]).symmetric_difference(
                    item[1]["predicted_labels"]
                )
            ),
            item[0]["language"],
        ),
        reverse=True,
    )[:12]

    lines = [
        "# Phase 3a pilot qualitative examples",
        "",
        "The source corpus is always shown in the final column. These examples are",
        "diagnostic only; the pilot deliberately oversamples long pairs.",
        "The existing strategy labels are upstream metadata from iDEM and Saaq",
        "al-Bambuu. Their annotation provenance is unverified, so they are not treated",
        "as human annotations or gold labels.",
        "",
        "",
        "## Largest disagreements with upstream labels",
        "",
        "| Original | Simplification | Predicted | Upstream labels | Scores | Source |",
        "|---|---|---|---|---|---|",
    ]
    lines.extend(example_row(*item) for item in disagreements)

    lines.extend(
        [
            "",
            "## Predictions nearest to each decision threshold",
            "",
        ]
    )
    for code in CODES:
        nearest = sorted(
            joined,
            key=lambda item: abs(
                float(item[1]["strategy_scores"][code])
                - threshold_by_code[code]
            ),
        )[:2]
        lines.extend(
            [
                f"### {code} (threshold {threshold_by_code[code]:.2f})",
                "",
                "| Original | Simplification | Predicted | Upstream labels | Scores | Source |",
                "|---|---|---|---|---|---|",
            ]
        )
        lines.extend(example_row(*item) for item in nearest)
        lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    input_root = resolve_project_path(config["input_root"])
    run_root = resolve_project_path(config["runs_root"]) / config["run_id"]
    reports_root = run_root / "reports"
    reports_root.mkdir(parents=True, exist_ok=True)
    run_config = json.loads(
        (run_root / "run_config.json").read_text(encoding="utf-8")
    )
    validation = json.loads(
        (reports_root / "validation.json").read_text(encoding="utf-8")
    )
    if not validation.get("valid"):
        raise ValueError("Pilot must pass validation before summarization.")

    metadata_by_id: dict[str, dict[str, Any]] = {}
    predictions_by_id: dict[str, dict[str, Any]] = {}
    for relative in config["selection"]["files"]:
        for record in read_jsonl(input_root / relative):
            pair_id = str(record["id"])
            if pair_id in metadata_by_id:
                raise ValueError(f"Duplicate sample ID: {pair_id}")
            metadata_by_id[pair_id] = record
        output_path = run_root / "predictions" / relative
        for record in read_jsonl(output_path):
            predictions_by_id[str(record["id"])] = record

    if set(metadata_by_id) != set(predictions_by_id):
        raise ValueError("Pilot metadata and prediction ID sets differ.")
    joined = [
        (metadata_by_id[pair_id], predictions_by_id[pair_id])
        for pair_id in metadata_by_id
    ]

    language_rows = grouped_rows(joined, ("language",))
    language_source_rows = grouped_rows(joined, ("language", "source"))
    detailed_rows = grouped_rows(
        joined, ("language", "source", "corpus")
    )
    write_csv(reports_root / "strategy_summary_language.csv", language_rows)
    write_csv(
        reports_root / "strategy_summary_language_source.csv",
        language_source_rows,
    )
    write_csv(
        reports_root / "strategy_summary_language_source_corpus.csv",
        detailed_rows,
    )

    distribution = Counter(
        prediction["strategy_count"] for _, prediction in joined
    )
    write_csv(
        reports_root / "strategy_count_distribution.csv",
        [
            {
                "strategy_count": count,
                "pairs": distribution[count],
                "percent": percent(distribution[count], len(joined)),
            }
            for count in range(len(LABELS) + 1)
        ],
    )

    agreement_summary, agreement_rows = agreement(joined)
    write_csv(reports_root / "upstream_label_comparison.csv", agreement_rows)
    write_csv(
        reports_root / "upstream_label_comparison_by_language.csv",
        agreement_grouped_rows(joined, ("language", "source", "corpus")),
    )
    (reports_root / "upstream_label_comparison.json").write_text(
        json.dumps(agreement_summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    thresholds = run_config["model"]["thresholds"]
    threshold_by_code = {
        LABEL_CODES[label]: float(thresholds[label]) for label in LABELS
    }
    qualitative_report(
        reports_root / "qualitative_examples.md",
        joined,
        threshold_by_code,
    )

    truncated_pairs = sum(
        bool(prediction.get("diagnostics", {}).get("truncated"))
        for _, prediction in joined
    )
    max_prompt_tokens = max(
        (
            int(
                prediction.get("diagnostics", {}).get(
                    "max_prompt_tokens", 0
                )
            )
            for _, prediction in joined
        ),
        default=0,
    )
    prediction_diagnostics = {
        "pairs": len(joined),
        "truncated_pairs": truncated_pairs,
        "max_prompt_tokens": max_prompt_tokens,
    }
    (reports_root / "prediction_diagnostics.json").write_text(
        json.dumps(prediction_diagnostics, indent=2) + "\n",
        encoding="utf-8",
    )

    overall = summarize_group(("all",), joined, ("scope",))
    inference_seconds = float(
        run_config.get("timings", {}).get("inference_seconds", 0.0)
    )
    seconds_per_pair = (
        inference_seconds / len(joined) if joined else 0.0
    )
    full_pairs = int(config["full_corpus_pairs"])
    full_gpu_hours = seconds_per_pair * full_pairs / 3600.0
    runner_elapsed_seconds = float(run_config.get("elapsed_seconds", 0.0))
    startup_seconds = float(run_config["timings"]["prepare_seconds"]) + float(
        run_config["timings"]["model_load_seconds"]
    )
    projected_hours = {gpus: full_gpu_hours / gpus for gpus in (2, 4, 8)}
    prevalence = {
        code: overall[f"{code}_pct"] for code in CODES
    }
    highest = max(prevalence, key=prevalence.get)
    lowest = min(prevalence, key=prevalence.get)
    hardware = run_config.get("hardware", {})
    hardware_name = hardware.get("cuda_device_name", "see Slurm log")
    label_rows_by_f1 = sorted(agreement_rows, key=lambda row: row["f1"])
    weakest_labels = ", ".join(
        f"{row['code']}={row['f1']:.3f}" for row in label_rows_by_f1[:2]
    )
    strongest_labels = ", ".join(
        f"{row['code']}={row['f1']:.3f}"
        for row in reversed(label_rows_by_f1[-2:])
    )
    cardinality_gap = (
        agreement_summary["mean_predicted_strategy_count"]
        - agreement_summary["mean_reference_strategy_count"]
    )
    lowest_language = min(
        language_rows, key=lambda row: row["mean_strategy_count"]
    )
    highest_language = max(
        language_rows, key=lambda row: row["mean_strategy_count"]
    )

    report_lines = [
        "# Phase 3a stratified pilot: quality and cost",
        "",
        "This historical run evaluates only Qwen2.5-7B on Phase 2a occurrence IDs.",
        "It does not validate all three checkpoints on canonical Phase 2b input.",
        "",
        "## Coverage",
        "",
        f"- Pairs: {len(joined):,}",
        f"- Files/corpora: {len(config['selection']['files'])}",
        f"- Languages: {len({item[0]['language'] for item in joined})}",
        "- Sampling: 25 deterministic random pairs plus 5 longest pairs per file,",
        "  with overlaps removed.",
        "",
        "This is a diagnostic sample, not an unbiased corpus estimate: every source",
        "has similar weight and long pairs are intentionally oversampled.",
        "",
        "## Automatic prediction profile",
        "",
        f"- Mean strategies per pair: {overall['mean_strategy_count']:.3f}",
        f"- Zero-strategy pairs: {overall['zero_strategy_pct']:.2f}%",
        f"- Pairs with at least two strategies: {overall['multilabel_pct']:.2f}%",
        f"- Most frequent strategy: {highest} ({prevalence[highest]:.2f}%)",
        f"- Least frequent strategy: {lowest} ({prevalence[lowest]:.2f}%)",
        "",
        "## Comparison with existing upstream labels",
        "",
        f"- Labelled pilot pairs: {agreement_summary['labelled_pairs']}",
        f"- Exact match: {agreement_summary['exact_match']:.3f}",
        f"- Micro F1: {agreement_summary['micro_f1']:.3f}",
        f"- Macro F1: {agreement_summary['macro_f1']:.3f}",
        f"- Hamming loss: {agreement_summary['hamming_loss']:.3f}",
        f"- Mean upstream strategies: {agreement_summary['mean_reference_strategy_count']:.3f}",
        f"- Mean predicted strategies: {agreement_summary['mean_predicted_strategy_count']:.3f}",
        "",
        "These labels come from the upstream iDEM/Saaq dataset.csv. Their provenance",
        "is not documented locally: they may be human, LLM-generated, or classifier",
        "predictions. The scores below are descriptive comparisons, not gold evaluation.",
        "",
        "## Short quality review",
        "",
        f"- Strongest per-label F1: {strongest_labels}.",
        f"- Weakest per-label F1: {weakest_labels}.",
        f"- The model predicts {cardinality_gap:.3f} more strategies per labelled pair",
        "  than the upstream labels. SYNT and COMP account for many mismatches, but",
        "  these cannot be called false positives without verified reference labels.",
        f"- Mean strategy count ranges from {lowest_language['mean_strategy_count']:.2f}",
        f"  for {lowest_language['language']} to {highest_language['mean_strategy_count']:.2f}",
        f"  for {highest_language['language']}. This may partly reflect corpus differences,",
        "  but it is too large to assume equal calibration across languages.",
        f"- Truncated pairs: {truncated_pairs}/{len(joined)}; maximum prompt length:",
        f"  {max_prompt_tokens} tokens. Truncation does not explain the disagreement.",
        "",
        "Manual reading confirms meaningful mismatches, but their direction cannot be",
        "decided from unverified upstream labels alone. Therefore, the released",
        "thresholds are adequate for pipeline testing, but the full corpus should not be",
        "processed until a small language-balanced manual review and a comparison with",
        "the encoder checkpoints are completed.",
        "",
        "## Runtime and projected cost",
        "",
        f"- GPU: {hardware_name}",
        f"- End-to-end runner time: {runner_elapsed_seconds:.2f} seconds",
        f"- Model preparation: {run_config['timings']['prepare_seconds']:.2f} seconds",
        f"- Model load: {run_config['timings']['model_load_seconds']:.2f} seconds",
        f"- Preparation plus load overhead: {startup_seconds:.2f} seconds",
        f"- Pilot inference: {inference_seconds:.2f} seconds",
        f"- Inference seconds per pair: {seconds_per_pair:.4f}",
        f"- Projected single-GPU time for {full_pairs:,} pairs: {full_gpu_hours:.2f} hours",
        f"- Idealized 2-GPU inference time: {projected_hours[2]:.2f} hours",
        f"- Idealized 4-GPU inference time: {projected_hours[4]:.2f} hours",
        f"- Idealized 8-GPU inference time: {projected_hours[8]:.2f} hours",
        "",
        "The projection assumes this pilot's deliberately long-text-heavy mixture and",
        "the same GPU type. The later full-run sharding decision should use this as",
        "an engineering estimate, not a guaranteed runtime. Multi-GPU figures assume",
        "perfect balancing and exclude repeated model startup for each shard.",
        "",
        "## Detailed files",
        "",
        "- strategy_summary_language.csv",
        "- strategy_summary_language_source.csv",
        "- strategy_summary_language_source_corpus.csv",
        "- strategy_count_distribution.csv",
        "- upstream_label_comparison.csv and .json",
        "- upstream_label_comparison_by_language.csv",
        "- prediction_diagnostics.json",
        "- [Qualitative examples](qualitative_examples.md)",
    ]
    (reports_root / "pilot_quality_cost.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )
    print("\n".join(report_lines))


if __name__ == "__main__":
    main()
