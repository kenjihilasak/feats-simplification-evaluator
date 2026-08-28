#!/usr/bin/env python3
"""Build multilingual single-strategy gold candidates by label-wise voting."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import tempfile
from collections import Counter
from itertools import zip_longest
from pathlib import Path
from typing import Any, Iterable, Mapping

from experiment_config import load_json, project_path
from strategy_backend import LABEL_CODES, LABELS


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = (
    PROJECT_ROOT
    / "phase3a_strategy_detection"
    / "configs"
    / "gold_candidates"
    / "single_strategy_majority_vote_v1.json"
)
CODES = tuple(LABEL_CODES[label] for label in LABELS)
CODE_LABELS = {LABEL_CODES[label]: label for label in LABELS}
OUTPUT_FILENAME = "single_strategy_candidates.jsonl"
SELECTION_RULE = "label_majority_2_of_3_and_consensus_cardinality_1"
QUALITY_TIERS = (
    "unanimous_exact_singleton",
    "majority_exact_singleton",
    "label_majority_only",
)


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


def canonical_id(record: Mapping[str, Any]) -> str:
    return str(record.get("canonical_pair_id") or record.get("id") or "")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def percent(numerator: int, denominator: int) -> float:
    return 100.0 * numerator / denominator if denominator else 0.0


def sources_for(metadata: Mapping[str, Any]) -> list[str]:
    sources = {
        str(value)
        for value in metadata.get("sources", [])
        if str(value).strip()
    }
    for item in metadata.get("provenance", []):
        if isinstance(item, dict) and str(item.get("source", "")).strip():
            sources.add(str(item["source"]))
    if not sources:
        raise ValueError(f"Missing Phase 2b source for {canonical_id(metadata)}")
    return sorted(sources)


class Prediction:
    def __init__(
        self,
        codes: frozenset[str],
        scores: dict[str, float],
    ) -> None:
        self.codes = codes
        self.scores = scores

    @property
    def strategy_count(self) -> int:
        return len(self.codes)


def normalize_prediction(
    record: Mapping[str, Any], model_alias: str, pair_id: str
) -> Prediction:
    if canonical_id(record) != pair_id:
        raise ValueError(
            f"Prediction/input ID mismatch for {model_alias}: "
            f"{canonical_id(record)!r} != {pair_id!r}"
        )
    if record.get("model_alias") != model_alias:
        raise ValueError(f"Prediction model alias mismatch for {pair_id}")
    raw_codes = record.get("predicted_codes")
    raw_scores = record.get("strategy_scores")
    if not isinstance(raw_codes, list) or not isinstance(raw_scores, dict):
        raise ValueError(f"Invalid strategy fields for {model_alias}/{pair_id}")
    codes = frozenset(str(code) for code in raw_codes)
    if len(codes) != len(raw_codes) or not codes.issubset(CODES):
        raise ValueError(f"Invalid predicted codes for {model_alias}/{pair_id}")
    if int(record.get("strategy_count", -1)) != len(codes):
        raise ValueError(f"Invalid strategy count for {model_alias}/{pair_id}")
    if set(raw_scores) != set(CODES):
        raise ValueError(f"Invalid score inventory for {model_alias}/{pair_id}")
    scores = {code: float(raw_scores[code]) for code in CODES}
    if any(
        not math.isfinite(value) or not 0.0 <= value <= 1.0
        for value in scores.values()
    ):
        raise ValueError(f"Invalid strategy score for {model_alias}/{pair_id}")
    return Prediction(codes, scores)


def quality_tier(
    predictions: Mapping[str, Prediction], winner: str
) -> tuple[str, list[str]]:
    exact_singleton_models = [
        alias
        for alias, prediction in predictions.items()
        if prediction.codes == {winner}
    ]
    if len(exact_singleton_models) == 3:
        tier = "unanimous_exact_singleton"
    elif len(exact_singleton_models) >= 2:
        tier = "majority_exact_singleton"
    else:
        tier = "label_majority_only"
    return tier, exact_singleton_models


def candidate_record(
    metadata: Mapping[str, Any],
    predictions: Mapping[str, Prediction],
    winner: str,
    vote_counts: Mapping[str, int],
) -> dict[str, Any]:
    supporting_models = [
        alias for alias, prediction in predictions.items() if winner in prediction.codes
    ]
    tier, exact_singleton_models = quality_tier(predictions, winner)
    record = dict(metadata)
    record.update(
        {
            "candidate_schema": "feats-phase3a-single-strategy-candidate-v1",
            "candidate_status": "unreviewed_model_consensus",
            "candidate_strategy_code": winner,
            "candidate_strategy_label": CODE_LABELS[winner],
            "majority_votes": int(vote_counts[winner]),
            "supporting_models": supporting_models,
            "label_vote_counts": {
                code: int(vote_counts[code]) for code in CODES
            },
            "quality_tier": tier,
            "exact_singleton_supporting_models": exact_singleton_models,
            "selection_rule": SELECTION_RULE,
            "model_predictions": {
                alias: {
                    "predicted_codes": [
                        code for code in CODES if code in prediction.codes
                    ],
                    "strategy_count": prediction.strategy_count,
                    "strategy_scores": prediction.scores,
                }
                for alias, prediction in predictions.items()
            },
        }
    )
    return record


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write an empty report: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def validate_source_models(
    experiment_root: Path,
    model_aliases: list[str],
    expected_pairs: int,
) -> dict[str, Any]:
    provenance: dict[str, Any] = {}
    for alias in model_aliases:
        model_root = experiment_root / "models" / alias
        validation = load_json(model_root / "reports" / "validation.json")
        run_config = load_json(model_root / "run_config.json")
        if validation.get("valid") is not True:
            raise ValueError(f"Source model {alias} has not passed validation")
        if (
            int(validation.get("expected_pairs", -1)) != expected_pairs
            or int(validation.get("observed_pairs", -1)) != expected_pairs
        ):
            raise ValueError(f"Source model {alias} validation count differs")
        if run_config.get("status") != "complete":
            raise ValueError(f"Source model {alias} is not complete")
        if int(run_config.get("processed_pairs", -1)) != expected_pairs:
            raise ValueError(f"Source model {alias} processed count differs")
        model = run_config.get("model", {})
        provenance[alias] = {
            key: model[key]
            for key in (
                "model_id",
                "revision",
                "base_model_id",
                "base_revision",
                "thresholds",
                "taxonomy_fingerprint",
            )
            if key in model
        }
        provenance[alias]["model_config_sha256"] = run_config.get(
            "model_config_sha256"
        )
        provenance[alias]["input_manifest_sha256"] = run_config.get(
            "input_manifest_sha256"
        )
    return provenance


def language_rows(
    stats: Mapping[str, Counter[str]],
) -> list[dict[str, Any]]:
    rows = []
    for language in sorted(stats):
        values = stats[language]
        rows.append(
            {
                "language": language,
                "input_pairs": values["input_pairs"],
                "candidate_pairs": values["candidate_pairs"],
                "candidate_pct": percent(
                    values["candidate_pairs"], values["input_pairs"]
                ),
                "no_majority_pairs": values["no_majority_pairs"],
                "multiple_majority_pairs": values["multiple_majority_pairs"],
                "majority_2_votes_pairs": values["majority_2_votes_pairs"],
                "unanimous_3_votes_pairs": values["unanimous_3_votes_pairs"],
                **{
                    f"{tier}_pairs": values[tier]
                    for tier in QUALITY_TIERS
                },
            }
        )
    return rows


def strategy_rows(
    stats: Mapping[str, Counter[str]], total_candidates: int
) -> list[dict[str, Any]]:
    return [
        {
            "strategy_code": code,
            "strategy_label": CODE_LABELS[code],
            "candidate_pairs": stats[code]["candidate_pairs"],
            "candidate_pct": percent(
                stats[code]["candidate_pairs"], total_candidates
            ),
            "majority_2_votes_pairs": stats[code]["majority_2_votes_pairs"],
            "unanimous_3_votes_pairs": stats[code]["unanimous_3_votes_pairs"],
            **{
                f"{tier}_pairs": stats[code][tier]
                for tier in QUALITY_TIERS
            },
        }
        for code in CODES
    ]


def language_strategy_rows(
    stats: Mapping[tuple[str, str], Counter[str]],
) -> list[dict[str, Any]]:
    rows = []
    for language, code in sorted(stats):
        values = stats[(language, code)]
        rows.append(
            {
                "language": language,
                "strategy_code": code,
                "strategy_label": CODE_LABELS[code],
                "candidate_pairs": values["candidate_pairs"],
                "majority_2_votes_pairs": values["majority_2_votes_pairs"],
                "unanimous_3_votes_pairs": values["unanimous_3_votes_pairs"],
                **{
                    f"{tier}_pairs": values[tier]
                    for tier in QUALITY_TIERS
                },
            }
        )
    return rows


def source_rows(
    stats: Mapping[tuple[str, str], Counter[str]],
) -> list[dict[str, Any]]:
    rows = []
    for language, source in sorted(stats):
        values = stats[(language, source)]
        rows.append(
            {
                "language": language,
                "source": source,
                "input_pairs": values["input_pairs"],
                "candidate_pairs": values["candidate_pairs"],
                "candidate_pct": percent(
                    values["candidate_pairs"], values["input_pairs"]
                ),
            }
        )
    return rows


def markdown_report(
    path: Path,
    candidate_id: str,
    source_experiment_id: str,
    total: Counter[str],
    languages: list[dict[str, Any]],
    strategies: list[dict[str, Any]],
) -> None:
    exact_singleton_candidates = (
        total["unanimous_exact_singleton"]
        + total["majority_exact_singleton"]
    )
    lines = [
        "# Phase 3a single-strategy gold candidates",
        "",
        f"Candidate set: {candidate_id}. Source experiment: {source_experiment_id}.",
        "",
        "Each strategy receives one binary vote from Qwen, E5, and XLM-R. A pair",
        "is retained when exactly one strategy receives at least two votes.",
        "",
        "## Overall",
        "",
        "| Input pairs | Candidates | Candidate rate | No majority | Multiple majority labels |",
        "|---:|---:|---:|---:|---:|",
        f"| {total['input_pairs']:,} | {total['candidate_pairs']:,} | "
        f"{percent(total['candidate_pairs'], total['input_pairs']):.2f}% | "
        f"{total['no_majority_pairs']:,} | {total['multiple_majority_pairs']:,} |",
        "",
        "## Candidates by language",
        "",
        "| Language | Input pairs | Candidates | Rate | 2 votes | 3 votes |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in languages:
        lines.append(
            f"| {row['language']} | {int(row['input_pairs']):,} | "
            f"{int(row['candidate_pairs']):,} | "
            f"{float(row['candidate_pct']):.2f}% | "
            f"{int(row['majority_2_votes_pairs']):,} | "
            f"{int(row['unanimous_3_votes_pairs']):,} |"
        )
    lines.extend(
        [
            "",
            "## Candidates by strategy",
            "",
            "| Strategy | Candidates | Share | 2 votes | 3 votes |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in strategies:
        lines.append(
            f"| {row['strategy_code']} ({row['strategy_label']}) | "
            f"{int(row['candidate_pairs']):,} | "
            f"{float(row['candidate_pct']):.2f}% | "
            f"{int(row['majority_2_votes_pairs']):,} | "
            f"{int(row['unanimous_3_votes_pairs']):,} |"
        )
    lines.extend(
        [
            "",
        "## Agreement tiers and review priority",
        "",
        f"- Unanimous exact-singleton: {total['unanimous_exact_singleton']:,}; "
        "all three models predict only the winning strategy.",
        f"- Majority exact-singleton: {total['majority_exact_singleton']:,}; "
        "at least two models predict only the winning strategy.",
        f"- Label-majority only: {total['label_majority_only']:,}; the winning "
        "strategy receives at least two votes, but fewer than two models predict "
        "it as their complete singleton set.",
        "",
        f"The stricter exact-singleton majority subset contains "
        f"{exact_singleton_candidates:,} pairs "
        f"({percent(exact_singleton_candidates, total['candidate_pairs']):.2f}% "
        "of this candidate pool). The label-majority-only tier is retained by the "
        "configured voting rule but should receive lower review priority.",
        "",
        "These are model-consensus candidates, not verified gold labels. Human",
        "annotation and adjudication are required before calling the dataset gold.",
        "The pool is also unbalanced across languages and strategies; sampling or",
        "stratification should be performed only when designing the reviewed test set.",
    ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(
    config_path: Path,
    output_root_override: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = load_json(config_path)
    if config.get("schema") != "feats-phase3a-gold-candidate-config-v1":
        raise ValueError("Unexpected gold-candidate config schema")
    model_aliases = [str(value) for value in config["required_models"]]
    if len(model_aliases) != 3 or len(set(model_aliases)) != 3:
        raise ValueError("Majority voting requires exactly three distinct models")
    voting = config.get("voting", {})
    if voting != {
        "unit": "strategy_label",
        "minimum_votes": 2,
        "required_consensus_cardinality": 1,
    }:
        raise ValueError("Config does not reproduce the Phase 3a voting rule")

    source_config_path = project_path(config["source_experiment_config"])
    source_config = load_json(source_config_path)
    if source_config.get("schema") != "feats-phase3-experiment-v2":
        raise ValueError("Source must be a Phase 3a multi-model experiment")
    if set(source_config["models"]) != set(model_aliases):
        raise ValueError("Source experiment model set differs from required_models")
    expected_pairs = int(source_config["expected_pairs"])
    input_root = project_path(source_config["input_root"])
    source_experiment_id = str(source_config["experiment_id"])
    experiment_root = project_path(source_config["runs_root"]) / source_experiment_id
    model_provenance = validate_source_models(
        experiment_root, model_aliases, expected_pairs
    )

    output_base = (
        output_root_override.resolve()
        if output_root_override is not None
        else project_path(config["output_root"])
    )
    candidate_id = str(config["candidate_id"])
    candidate_root = output_base / candidate_id
    output_base.mkdir(parents=True, exist_ok=True)
    if candidate_root.exists() and not overwrite:
        raise FileExistsError(
            f"Candidate output already exists: {candidate_root}; use --overwrite"
        )

    temporary = Path(
        tempfile.mkdtemp(prefix=f".{candidate_id}-", dir=output_base)
    )
    try:
        data_root = temporary / "data"
        reports_root = temporary / "reports"
        reports_root.mkdir(parents=True)
        language_stats: dict[str, Counter[str]] = {}
        strategy_stats = {code: Counter() for code in CODES}
        language_strategy_stats: dict[tuple[str, str], Counter[str]] = {}
        source_stats: dict[tuple[str, str], Counter[str]] = {}
        total: Counter[str] = Counter()
        manifest: list[dict[str, Any]] = []
        missing = object()
        seen_languages: set[str] = set()

        for relative_value in source_config["selection"]["files"]:
            relative = Path(str(relative_value))
            language = relative.parent.as_posix()
            if language in seen_languages:
                raise ValueError(f"More than one selected file for {language}")
            seen_languages.add(language)
            input_path = input_root / relative
            prediction_paths = [
                experiment_root / "models" / alias / "predictions" / relative
                for alias in model_aliases
            ]
            for path in [input_path, *prediction_paths]:
                if not path.is_file():
                    raise FileNotFoundError(path)
            output_path = data_root / language / OUTPUT_FILENAME
            output_path.parent.mkdir(parents=True)
            input_count = 0
            candidate_count = 0
            streams = [read_jsonl(input_path)] + [
                read_jsonl(path) for path in prediction_paths
            ]
            with output_path.open("w", encoding="utf-8") as output_handle:
                for records in zip_longest(*streams, fillvalue=missing):
                    if any(record is missing for record in records):
                        raise ValueError(
                            f"Input/prediction lengths differ for {relative}"
                        )
                    metadata = records[0]
                    pair_id = canonical_id(metadata)
                    if not pair_id:
                        raise ValueError(f"Missing canonical ID in {input_path}")
                    if str(metadata.get("language", "")) != language:
                        raise ValueError(f"Language/path mismatch for {pair_id}")
                    predictions = {
                        alias: normalize_prediction(record, alias, pair_id)
                        for alias, record in zip(model_aliases, records[1:])
                    }
                    vote_counts = {
                        code: sum(
                            code in prediction.codes
                            for prediction in predictions.values()
                        )
                        for code in CODES
                    }
                    consensus = [
                        code
                        for code in CODES
                        if vote_counts[code] >= int(voting["minimum_votes"])
                    ]
                    sources = sources_for(metadata)
                    language_values = language_stats.setdefault(
                        language, Counter()
                    )
                    input_count += 1
                    total["input_pairs"] += 1
                    language_values["input_pairs"] += 1
                    for source in sources:
                        source_stats.setdefault((language, source), Counter())[
                            "input_pairs"
                        ] += 1
                    if not consensus:
                        total["no_majority_pairs"] += 1
                        language_values["no_majority_pairs"] += 1
                        continue
                    if len(consensus) > 1:
                        total["multiple_majority_pairs"] += 1
                        language_values["multiple_majority_pairs"] += 1
                        continue

                    winner = consensus[0]
                    record = candidate_record(
                        metadata, predictions, winner, vote_counts
                    )
                    output_handle.write(
                        json.dumps(
                            record,
                            ensure_ascii=False,
                            separators=(",", ":"),
                        )
                        + "\n"
                    )
                    candidate_count += 1
                    total["candidate_pairs"] += 1
                    language_values["candidate_pairs"] += 1
                    vote_key = (
                        "unanimous_3_votes_pairs"
                        if vote_counts[winner] == 3
                        else "majority_2_votes_pairs"
                    )
                    tier = str(record["quality_tier"])
                    total[vote_key] += 1
                    total[tier] += 1
                    language_values[vote_key] += 1
                    language_values[tier] += 1
                    strategy_values = strategy_stats[winner]
                    strategy_values["candidate_pairs"] += 1
                    strategy_values[vote_key] += 1
                    strategy_values[tier] += 1
                    grouped = language_strategy_stats.setdefault(
                        (language, winner), Counter()
                    )
                    grouped["candidate_pairs"] += 1
                    grouped[vote_key] += 1
                    grouped[tier] += 1
                    for source in sources:
                        source_stats[(language, source)]["candidate_pairs"] += 1

            manifest.append(
                {
                    "language": language,
                    "input_file": relative.as_posix(),
                    "input_pairs": input_count,
                    "candidate_pairs": candidate_count,
                    "output_file": output_path.relative_to(temporary).as_posix(),
                    "bytes": output_path.stat().st_size,
                    "sha256": sha256(output_path),
                }
            )

        if total["input_pairs"] != expected_pairs:
            raise ValueError(
                f"Observed {total['input_pairs']} source pairs, expected {expected_pairs}"
            )
        if (
            total["candidate_pairs"]
            + total["no_majority_pairs"]
            + total["multiple_majority_pairs"]
            != total["input_pairs"]
        ):
            raise RuntimeError("Candidate/exclusion counts do not partition the input")

        languages = language_rows(language_stats)
        strategies = strategy_rows(strategy_stats, total["candidate_pairs"])
        language_strategies = language_strategy_rows(language_strategy_stats)
        sources = source_rows(source_stats)
        write_csv(reports_root / "candidates_by_language.csv", languages)
        write_csv(reports_root / "candidates_by_strategy.csv", strategies)
        write_csv(
            reports_root / "candidates_by_language_strategy.csv",
            language_strategies,
        )
        write_csv(reports_root / "candidates_by_language_source.csv", sources)
        write_csv(temporary / "CANDIDATE_MANIFEST.csv", manifest)

        summary = {
            "schema": "feats-phase3a-single-strategy-summary-v1",
            "candidate_id": candidate_id,
            "candidate_status": "unreviewed_model_consensus",
            "source_experiment_id": source_experiment_id,
            "source_experiment_config": str(config["source_experiment_config"]),
            "required_models": model_aliases,
            "model_provenance": model_provenance,
            "voting": voting,
            "selection_rule": SELECTION_RULE,
            "input_pairs": total["input_pairs"],
            "candidate_pairs": total["candidate_pairs"],
            "candidate_pct": percent(
                total["candidate_pairs"], total["input_pairs"]
            ),
            "excluded": {
                "no_majority_pairs": total["no_majority_pairs"],
                "multiple_majority_pairs": total["multiple_majority_pairs"],
            },
            "vote_strength": {
                "majority_2_votes_pairs": total["majority_2_votes_pairs"],
                "unanimous_3_votes_pairs": total["unanimous_3_votes_pairs"],
            },
            "quality_tiers": {
                tier: total[tier] for tier in QUALITY_TIERS
            },
            "languages": languages,
            "strategies": strategies,
            "manifest": manifest,
            "human_validation_required": True,
        }
        (reports_root / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        markdown_report(
            reports_root / "summary.md",
            candidate_id,
            source_experiment_id,
            total,
            languages,
            strategies,
        )
        (temporary / "candidate_config.json").write_text(
            json.dumps(config, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        if candidate_root.exists():
            shutil.rmtree(candidate_root)
        temporary.replace(candidate_root)
        summary["output_root"] = str(candidate_root)
        return summary
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing candidate output with the same candidate ID.",
    )
    args = parser.parse_args()
    summary = build(args.config, args.output_root, args.overwrite)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
