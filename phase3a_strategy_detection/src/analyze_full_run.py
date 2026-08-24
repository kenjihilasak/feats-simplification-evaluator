#!/usr/bin/env python3
"""Analyze a validated Phase 3a full run by language and Phase 2b provenance."""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass, field
from itertools import combinations, zip_longest
from pathlib import Path
from typing import Any, Iterable

from experiment_config import load_json, project_path
from strategy_backend import LABEL_CODES, LABELS


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = (
    PROJECT_ROOT
    / "phase3a_strategy_detection"
    / "configs"
    / "experiments"
    / "three_models_phase2b_full_v1.json"
)
CODES = tuple(LABEL_CODES[label] for label in LABELS)
CODE_LABELS = {LABEL_CODES[label]: label for label in LABELS}


def percent(numerator: int, denominator: int) -> float:
    return 100.0 * numerator / denominator if denominator else 0.0


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON at {path}:{line_number}") from error
            if not isinstance(value, dict):
                raise ValueError(f"Expected an object at {path}:{line_number}")
            yield value


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write an empty analysis table: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def canonical_id(record: dict[str, Any]) -> str:
    return str(record.get("canonical_pair_id") or record.get("id") or "")


def provenance_groups(
    metadata: dict[str, Any],
) -> tuple[list[str], list[tuple[str, str]]]:
    sources = {
        str(source)
        for source in metadata.get("sources", [])
        if str(source).strip()
    }
    corpora = {
        (str(item.get("source", "")), str(item.get("corpus", "")))
        for item in metadata.get("corpora", [])
        if isinstance(item, dict)
        and str(item.get("source", "")).strip()
        and str(item.get("corpus", "")).strip()
    }
    for item in metadata.get("provenance", []):
        if not isinstance(item, dict):
            continue
        source = str(item.get("source", ""))
        corpus = str(item.get("corpus", ""))
        if source:
            sources.add(source)
        if source and corpus:
            corpora.add((source, corpus))
    if not sources or not corpora:
        raise ValueError(f"Missing Phase 2b provenance for {canonical_id(metadata)}")
    return sorted(sources), sorted(corpora)


@dataclass(frozen=True)
class NormalizedPrediction:
    codes: frozenset[str]
    scores: tuple[float, ...]
    strategy_count: int


def normalize_prediction(
    prediction: dict[str, Any], model_alias: str, pair_id: str
) -> NormalizedPrediction:
    if canonical_id(prediction) != pair_id:
        raise ValueError(
            f"Prediction/input ID mismatch for {model_alias}: "
            f"{canonical_id(prediction)!r} != {pair_id!r}"
        )
    if prediction.get("model_alias") != model_alias:
        raise ValueError(f"Prediction model alias mismatch for {pair_id}")
    raw_codes = prediction.get("predicted_codes")
    raw_scores = prediction.get("strategy_scores")
    if not isinstance(raw_codes, list) or not isinstance(raw_scores, dict):
        raise ValueError(f"Invalid strategy fields for {model_alias}/{pair_id}")
    codes = frozenset(str(code) for code in raw_codes)
    if len(codes) != len(raw_codes) or not codes.issubset(CODES):
        raise ValueError(f"Invalid predicted codes for {model_alias}/{pair_id}")
    strategy_count = int(prediction.get("strategy_count", -1))
    if strategy_count != len(codes):
        raise ValueError(f"Invalid strategy count for {model_alias}/{pair_id}")
    if set(raw_scores) != set(CODES):
        raise ValueError(f"Invalid score inventory for {model_alias}/{pair_id}")
    scores = tuple(float(raw_scores[code]) for code in CODES)
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in scores):
        raise ValueError(f"Invalid strategy score for {model_alias}/{pair_id}")
    return NormalizedPrediction(codes, scores, strategy_count)


@dataclass
class CardinalityStats:
    pairs: int = 0
    strategy_count_sum: int = 0
    strategy_count_square_sum: int = 0
    distribution: list[int] = field(default_factory=lambda: [0] * (len(CODES) + 1))
    predicted_by_code: dict[str, int] = field(
        default_factory=lambda: {code: 0 for code in CODES}
    )
    score_sum_by_code: dict[str, float] = field(
        default_factory=lambda: {code: 0.0 for code in CODES}
    )

    def update(self, prediction: NormalizedPrediction) -> None:
        count = prediction.strategy_count
        self.pairs += 1
        self.strategy_count_sum += count
        self.strategy_count_square_sum += count * count
        self.distribution[count] += 1
        for index, code in enumerate(CODES):
            self.predicted_by_code[code] += code in prediction.codes
            self.score_sum_by_code[code] += prediction.scores[index]

    def _rank(self, rank: int) -> int:
        seen = 0
        for count, frequency in enumerate(self.distribution):
            seen += frequency
            if seen > rank:
                return count
        raise RuntimeError("Cardinality rank exceeds the observed distribution")

    def row(self, dimensions: dict[str, str]) -> dict[str, Any]:
        mean = self.strategy_count_sum / self.pairs
        variance = max(
            self.strategy_count_square_sum / self.pairs - mean * mean,
            0.0,
        )
        lower = self._rank((self.pairs - 1) // 2)
        upper = self._rank(self.pairs // 2)
        row: dict[str, Any] = {
            **dimensions,
            "pairs": self.pairs,
            "mean_strategy_count": mean,
            "median_strategy_count": (lower + upper) / 2.0,
            "std_strategy_count": math.sqrt(variance),
            "zero_strategy_pairs": self.distribution[0],
            "zero_strategy_pct": percent(self.distribution[0], self.pairs),
            "single_strategy_pairs": self.distribution[1],
            "single_strategy_pct": percent(self.distribution[1], self.pairs),
            "multilabel_pairs": sum(self.distribution[2:]),
            "multilabel_pct": percent(sum(self.distribution[2:]), self.pairs),
        }
        for count, frequency in enumerate(self.distribution):
            row[f"strategy_count_{count}_pairs"] = frequency
            row[f"strategy_count_{count}_pct"] = percent(frequency, self.pairs)
        return row

    def prevalence_rows(self, dimensions: dict[str, str]) -> list[dict[str, Any]]:
        return [
            {
                **dimensions,
                "pairs": self.pairs,
                "strategy_code": code,
                "strategy_label": CODE_LABELS[code],
                "predicted_pairs": self.predicted_by_code[code],
                "predicted_pct": percent(
                    self.predicted_by_code[code], self.pairs
                ),
                "mean_score": self.score_sum_by_code[code] / self.pairs,
            }
            for code in CODES
        ]


@dataclass
class AgreementStats:
    pairs: int = 0
    exact_matches: int = 0
    jaccard_sum: float = 0.0
    label_differences: int = 0
    strategy_count_abs_difference_sum: int = 0
    score_mae_sum: float = 0.0

    def update(
        self, first: NormalizedPrediction, second: NormalizedPrediction
    ) -> None:
        union = first.codes | second.codes
        self.pairs += 1
        self.exact_matches += first.codes == second.codes
        self.jaccard_sum += (
            len(first.codes & second.codes) / len(union) if union else 1.0
        )
        self.label_differences += len(first.codes ^ second.codes)
        self.strategy_count_abs_difference_sum += abs(
            first.strategy_count - second.strategy_count
        )
        self.score_mae_sum += sum(
            abs(left - right) for left, right in zip(first.scores, second.scores)
        ) / len(CODES)

    def row(self, dimensions: dict[str, str]) -> dict[str, Any]:
        return {
            **dimensions,
            "pairs": self.pairs,
            "exact_set_match_pct": percent(self.exact_matches, self.pairs),
            "mean_jaccard": self.jaccard_sum / self.pairs,
            "label_agreement_pct": 100.0
            * (1.0 - self.label_differences / (self.pairs * len(CODES))),
            "mean_abs_strategy_count_difference": (
                self.strategy_count_abs_difference_sum / self.pairs
            ),
            "mean_score_mae": self.score_mae_sum / self.pairs,
        }


def update_cardinality(
    groups: dict[tuple[str, ...], CardinalityStats],
    key: tuple[str, ...],
    prediction: NormalizedPrediction,
) -> None:
    groups.setdefault(key, CardinalityStats()).update(prediction)


def update_agreement(
    groups: dict[tuple[str, ...], AgreementStats],
    key: tuple[str, ...],
    first: NormalizedPrediction,
    second: NormalizedPrediction,
) -> None:
    groups.setdefault(key, AgreementStats()).update(first, second)


def cardinality_rows(
    groups: dict[tuple[str, ...], CardinalityStats], names: tuple[str, ...]
) -> list[dict[str, Any]]:
    return [
        groups[key].row(dict(zip(names, key)))
        for key in sorted(groups)
    ]


def prevalence_rows(
    groups: dict[tuple[str, ...], CardinalityStats], names: tuple[str, ...]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(groups):
        rows.extend(groups[key].prevalence_rows(dict(zip(names, key))))
    return rows


def agreement_rows(
    groups: dict[tuple[str, ...], AgreementStats], names: tuple[str, ...]
) -> list[dict[str, Any]]:
    return [groups[key].row(dict(zip(names, key))) for key in sorted(groups)]


def mean_table(
    rows: list[dict[str, Any]],
    group_fields: tuple[str, ...],
    model_aliases: list[str],
) -> list[str]:
    lookup = {
        (str(row["model_alias"]),)
        + tuple(str(row[field]) for field in group_fields): row
        for row in rows
    }
    groups = sorted(
        {
            tuple(str(row[field]) for field in group_fields)
            for row in rows
        }
    )
    headers = [field.replace("_", " ").title() for field in group_fields]
    lines = [
        "| " + " | ".join([*headers, "Pairs", *model_aliases]) + " |",
        "|"
        + "|".join(
            ["---"] * len(headers)
            + ["---:"]
            + ["---:"] * len(model_aliases)
        )
        + "|",
    ]
    for group in groups:
        model_rows = [lookup[(alias, *group)] for alias in model_aliases]
        if len({int(row["pairs"]) for row in model_rows}) != 1:
            raise RuntimeError(f"Model pair counts differ for group {group}")
        lines.append(
            "| "
            + " | ".join(
                [
                    *group,
                    f"{int(model_rows[0]['pairs']):,}",
                    *[
                        f"{float(row['mean_strategy_count']):.3f}"
                        for row in model_rows
                    ],
                ]
            )
            + " |"
        )
    return lines


def markdown_report(
    path: Path,
    experiment_id: str,
    total_pairs: int,
    model_aliases: list[str],
    language: list[dict[str, Any]],
    language_source: list[dict[str, Any]],
    overall: list[dict[str, Any]],
    prevalence: list[dict[str, Any]],
    agreement: list[dict[str, Any]],
) -> None:
    overall_by_model = {str(row["model_alias"]): row for row in overall}
    prevalence_by_model: dict[str, list[dict[str, Any]]] = {
        alias: [row for row in prevalence if row["model_alias"] == alias]
        for alias in model_aliases
    }
    lines = [
        "# Phase 3a full-run analysis",
        "",
        f"Experiment: `{experiment_id}`. Canonical pairs: {total_pairs:,}.",
        "",
        "All statistics are reported separately by model because their thresholds",
        "differ. A canonical pair is counted once per language and once per distinct",
        "Phase 2b source; a pair shared by two sources contributes once to each source.",
        "",
        "## Mean strategies detected per pair, by language",
        "",
        *mean_table(language, ("language",), model_aliases),
        "",
        "## Mean strategies detected per pair, by source within language",
        "",
        *mean_table(language_source, ("language", "source"), model_aliases),
        "",
        "## Additional diagnostics",
        "",
        "| Model | Mean strategies | Zero-strategy pairs | Multilabel pairs | Most frequent strategy |",
        "|---|---:|---:|---:|---|",
    ]
    for alias in model_aliases:
        row = overall_by_model[alias]
        highest = max(
            prevalence_by_model[alias],
            key=lambda item: float(item["predicted_pct"]),
        )
        lines.append(
            f"| `{alias}` | {float(row['mean_strategy_count']):.3f} | "
            f"{float(row['zero_strategy_pct']):.2f}% | "
            f"{float(row['multilabel_pct']):.2f}% | "
            f"{highest['strategy_code']} ({float(highest['predicted_pct']):.2f}%) |"
        )
    lines.extend(
        [
            "",
            "### Pairwise model agreement",
            "",
            "| Models | Exact strategy-set match | Mean Jaccard | Label agreement | Score MAE |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in agreement:
        lines.append(
            f"| `{row['model_a']}` / `{row['model_b']}` | "
            f"{float(row['exact_set_match_pct']):.2f}% | "
            f"{float(row['mean_jaccard']):.3f} | "
            f"{float(row['label_agreement_pct']):.2f}% | "
            f"{float(row['mean_score_mae']):.3f} |"
        )
    lines.extend(
        [
            "",
            "These are descriptive model-output statistics, not accuracy estimates:",
            "the full corpus has no verified gold strategy labels. Detailed CSVs also",
            "report the complete 0–6 cardinality distribution, per-strategy prevalence",
            "and mean score, language/source/corpus breakdowns, and model agreement by",
            "language and source.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze(config_path: Path) -> dict[str, Any]:
    config = load_json(config_path.resolve())
    if config.get("schema") != "feats-phase3-experiment-v2":
        raise ValueError("Full analysis requires a multi-model Phase 3a experiment")
    model_aliases = sorted(str(alias) for alias in config["models"])
    if len(model_aliases) < 2:
        raise ValueError("Full analysis requires at least two models")
    input_root = project_path(config["input_root"])
    experiment_id = str(config["experiment_id"])
    experiment_root = project_path(config["runs_root"]) / experiment_id
    reports_root = experiment_root / "reports"

    for alias in model_aliases:
        validation = load_json(
            experiment_root / "models" / alias / "reports" / "validation.json"
        )
        if validation.get("valid") is not True:
            raise ValueError(f"Model {alias} must pass validation before analysis")

    overall_stats: dict[tuple[str, ...], CardinalityStats] = {}
    language_stats: dict[tuple[str, ...], CardinalityStats] = {}
    source_stats: dict[tuple[str, ...], CardinalityStats] = {}
    corpus_stats: dict[tuple[str, ...], CardinalityStats] = {}
    agreement_overall: dict[tuple[str, ...], AgreementStats] = {}
    agreement_language: dict[tuple[str, ...], AgreementStats] = {}
    agreement_source: dict[tuple[str, ...], AgreementStats] = {}
    model_pairs = list(combinations(model_aliases, 2))
    total_pairs = 0
    language_pair_counts: dict[str, int] = {}
    missing = object()

    for relative_value in config["selection"]["files"]:
        relative = Path(str(relative_value))
        input_path = input_root / relative
        prediction_paths = [
            experiment_root / "models" / alias / "predictions" / relative
            for alias in model_aliases
        ]
        streams = [read_jsonl(input_path)] + [
            read_jsonl(path) for path in prediction_paths
        ]
        file_pairs = 0
        for records in zip_longest(*streams, fillvalue=missing):
            if any(record is missing for record in records):
                raise ValueError(f"Input/prediction lengths differ for {relative}")
            metadata = records[0]
            pair_id = canonical_id(metadata)
            language = str(metadata.get("language", ""))
            if not pair_id or not language:
                raise ValueError(f"Missing canonical ID/language in {input_path}")
            if language != relative.parent.as_posix():
                raise ValueError(f"Language/path mismatch for {pair_id}")
            sources, corpora = provenance_groups(metadata)
            predictions = {
                alias: normalize_prediction(record, alias, pair_id)
                for alias, record in zip(model_aliases, records[1:])
            }
            for alias, prediction in predictions.items():
                update_cardinality(overall_stats, (alias,), prediction)
                update_cardinality(language_stats, (alias, language), prediction)
                for source in sources:
                    update_cardinality(
                        source_stats, (alias, language, source), prediction
                    )
                for source, corpus in corpora:
                    update_cardinality(
                        corpus_stats,
                        (alias, language, source, corpus),
                        prediction,
                    )
            for model_a, model_b in model_pairs:
                first = predictions[model_a]
                second = predictions[model_b]
                update_agreement(
                    agreement_overall, (model_a, model_b), first, second
                )
                update_agreement(
                    agreement_language,
                    (model_a, model_b, language),
                    first,
                    second,
                )
                for source in sources:
                    update_agreement(
                        agreement_source,
                        (model_a, model_b, language, source),
                        first,
                        second,
                    )
            file_pairs += 1
        language_pair_counts[relative.parent.as_posix()] = file_pairs
        total_pairs += file_pairs

    expected_pairs = int(config.get("expected_pairs", total_pairs))
    if total_pairs != expected_pairs:
        raise ValueError(
            f"Full analysis observed {total_pairs}, expected {expected_pairs} pairs"
        )

    cardinality_overall = cardinality_rows(overall_stats, ("model_alias",))
    cardinality_language = cardinality_rows(
        language_stats, ("model_alias", "language")
    )
    cardinality_source = cardinality_rows(
        source_stats, ("model_alias", "language", "source")
    )
    cardinality_corpus = cardinality_rows(
        corpus_stats, ("model_alias", "language", "source", "corpus")
    )
    prevalence_overall = prevalence_rows(overall_stats, ("model_alias",))
    prevalence_language = prevalence_rows(
        language_stats, ("model_alias", "language")
    )
    prevalence_source = prevalence_rows(
        source_stats, ("model_alias", "language", "source")
    )
    agreement_overall_rows = agreement_rows(
        agreement_overall, ("model_a", "model_b")
    )
    agreement_language_rows = agreement_rows(
        agreement_language, ("model_a", "model_b", "language")
    )
    agreement_source_rows = agreement_rows(
        agreement_source, ("model_a", "model_b", "language", "source")
    )

    reports_root.mkdir(parents=True, exist_ok=True)
    tables = {
        "strategy_cardinality_overall.csv": cardinality_overall,
        "strategy_cardinality_by_language.csv": cardinality_language,
        "strategy_cardinality_by_language_source.csv": cardinality_source,
        "strategy_cardinality_by_language_source_corpus.csv": cardinality_corpus,
        "strategy_prevalence_overall.csv": prevalence_overall,
        "strategy_prevalence_by_language.csv": prevalence_language,
        "strategy_prevalence_by_language_source.csv": prevalence_source,
        "model_agreement_overall.csv": agreement_overall_rows,
        "model_agreement_by_language.csv": agreement_language_rows,
        "model_agreement_by_language_source.csv": agreement_source_rows,
    }
    for name, rows in tables.items():
        write_csv(reports_root / name, rows)

    summary = {
        "schema": "feats-phase3a-full-analysis-v1",
        "experiment_id": experiment_id,
        "canonical_pairs": total_pairs,
        "languages": language_pair_counts,
        "models": model_aliases,
        "source_counting": (
            "Each canonical pair is counted once per distinct Phase 2b source."
        ),
        "overall_cardinality": cardinality_overall,
        "overall_prevalence": prevalence_overall,
        "overall_model_agreement": agreement_overall_rows,
        "tables": sorted(tables),
    }
    (reports_root / "full_analysis.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_report(
        reports_root / "full_analysis.md",
        experiment_id,
        total_pairs,
        model_aliases,
        cardinality_language,
        cardinality_source,
        cardinality_overall,
        prevalence_overall,
        agreement_overall_rows,
    )
    result = {
        "experiment_id": experiment_id,
        "canonical_pairs": total_pairs,
        "models": model_aliases,
        "reports_root": str(reports_root),
        "report_files": len(tables) + 2,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    print(json.dumps(analyze(args.config), indent=2))


if __name__ == "__main__":
    main()
