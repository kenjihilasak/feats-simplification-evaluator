#!/usr/bin/env python3
"""Build and validate strict single-strategy candidates anchored in Gemma."""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import tempfile
from collections import Counter
from itertools import zip_longest
from pathlib import Path
from typing import Any, Mapping

from build_single_strategy_gold_candidates import (
    CODES,
    CODE_LABELS,
    OUTPUT_FILENAME,
    Prediction,
    canonical_id,
    normalize_prediction,
    percent,
    read_jsonl,
    sha256,
    sources_for,
    validate_source_models,
    write_csv,
)
from experiment_config import load_json, project_path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = (
    PROJECT_ROOT
    / "phase3a_strategy_detection"
    / "configs"
    / "gold_candidates"
    / "single_strategy_gemma_anchored_strict_v1.json"
)
CONFIG_SCHEMA = "feats-phase3a-gemma-anchored-candidate-config-v1"
SUMMARY_SCHEMA = "feats-phase3a-gemma-anchored-summary-v1"
VALIDATION_SCHEMA = "feats-phase3a-gemma-anchored-validation-v1"
SELECTION_RULE = "gemma_singleton_plus_exact_singleton_confirmation"


def prediction_payload(prediction: Prediction) -> dict[str, Any]:
    return {
        "predicted_codes": [code for code in CODES if code in prediction.codes],
        "strategy_count": prediction.strategy_count,
        "strategy_scores": prediction.scores,
    }


def confirmation_tier(count: int) -> str:
    if count not in (1, 2, 3):
        raise ValueError(f"Invalid confirmation count: {count}")
    return f"gemma_plus_{count}_exact_singleton"


def candidate_record(
    metadata: Mapping[str, Any],
    predictions: Mapping[str, Prediction],
    anchor_model: str,
    confirmation_models: list[str],
    winner: str,
    confirmers: list[str],
) -> dict[str, Any]:
    supporters = [anchor_model, *confirmers]
    votes = {
        code: sum(code in prediction.codes for prediction in predictions.values())
        for code in CODES
    }
    record = dict(metadata)
    record.update(
        {
            "candidate_schema": "feats-phase3a-single-strategy-candidate-v1",
            "candidate_status": "unreviewed_model_consensus",
            "candidate_strategy_code": winner,
            "candidate_strategy_label": CODE_LABELS[winner],
            "majority_votes": len(supporters),
            "supporting_models": supporters,
            "label_vote_counts": votes,
            "quality_tier": confirmation_tier(len(confirmers)),
            "exact_singleton_supporting_models": supporters,
            "selection_rule": SELECTION_RULE,
            "anchor_model": anchor_model,
            "confirmation_models": confirmation_models,
            "confirming_models": confirmers,
            "confirmation_count": len(confirmers),
            "model_predictions": {
                alias: prediction_payload(predictions[alias])
                for alias in [anchor_model, *confirmation_models]
            },
        }
    )
    return record


def summary_markdown(
    path: Path,
    candidate_id: str,
    input_pairs: int,
    candidate_pairs: int,
    language_rows: list[dict[str, Any]],
    strategy_rows: list[dict[str, Any]],
    tier_counts: Counter[str],
) -> None:
    lines = [
        "# Gemma-anchored strict single-strategy candidates",
        "",
        f"Candidate set: `{candidate_id}`.",
        "",
        "Gemma must predict exactly one strategy and at least one of E5, Qwen,",
        "or XLM-R must predict exactly the same singleton. These remain unreviewed",
        "model-consensus candidates, not verified gold labels.",
        "",
        "## Overall",
        "",
        "| Input pairs | Candidates | Rate |",
        "|---:|---:|---:|",
        f"| {input_pairs:,} | {candidate_pairs:,} | {percent(candidate_pairs, input_pairs):.2f}% |",
        "",
        "## By language",
        "",
        "| Language | Candidates |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {row['language']} | {int(row['candidate_pairs']):,} |"
        for row in language_rows
    )
    lines.extend(
        [
            "",
            "## By strategy",
            "",
            "| Strategy | Candidates |",
            "|---|---:|",
        ]
    )
    lines.extend(
        f"| {row['strategy_code']} ({row['strategy_label']}) | {int(row['candidate_pairs']):,} |"
        for row in strategy_rows
    )
    lines.extend(
        [
            "",
            "## Exact-singleton confirmation strength",
            "",
            "| Additional confirming models | Candidates |",
            "|---:|---:|",
            *[
                f"| {count} | {tier_counts[confirmation_tier(count)]:,} |"
                for count in (1, 2, 3)
            ],
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(config_path: Path, overwrite: bool = False) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = load_json(config_path)
    if config.get("schema") != CONFIG_SCHEMA:
        raise ValueError("Unexpected Gemma-anchored candidate config schema")
    anchor_model = str(config["anchor_model"])
    confirmation_models = [str(value) for value in config["confirmation_models"]]
    if len(confirmation_models) != 3 or len(set(confirmation_models)) != 3:
        raise ValueError("Exactly three distinct confirmation models are required")
    if anchor_model in confirmation_models:
        raise ValueError("The anchor cannot also be a confirmation model")
    if config.get("selection") != {
        "anchor_strategy_count": 1,
        "confirmation_mode": "exact_singleton",
        "minimum_confirmation_models": 1,
    }:
        raise ValueError("Config does not reproduce the strict anchored rule")

    source_config = load_json(project_path(config["source_experiment_config"]))
    model_aliases = [anchor_model, *confirmation_models]
    if set(source_config.get("models", {})) != set(model_aliases):
        raise ValueError("Source experiment does not contain the required four models")
    expected_pairs = int(source_config["expected_pairs"])
    expected_candidates = int(config["expected_candidates"])
    input_root = project_path(source_config["input_root"])
    experiment_root = (
        project_path(source_config["runs_root"])
        / str(source_config["experiment_id"])
    )
    model_provenance = validate_source_models(
        experiment_root, model_aliases, expected_pairs
    )

    output_base = project_path(config["output_root"])
    candidate_id = str(config["candidate_id"])
    candidate_root = output_base / candidate_id
    output_base.mkdir(parents=True, exist_ok=True)
    if candidate_root.exists() and not overwrite:
        raise FileExistsError(f"Candidate output exists: {candidate_root}")
    temporary = Path(tempfile.mkdtemp(prefix=f".{candidate_id}-", dir=output_base))
    try:
        reports_root = temporary / "reports"
        reports_root.mkdir(parents=True)
        total = Counter()
        languages: dict[str, Counter[str]] = {}
        strategies = {code: Counter() for code in CODES}
        sources: dict[tuple[str, str], Counter[str]] = {}
        confirmers_stats: Counter[str] = Counter()
        tiers: Counter[str] = Counter()
        manifest: list[dict[str, Any]] = []
        missing = object()

        for relative_value in source_config["selection"]["files"]:
            relative = Path(str(relative_value))
            language = relative.parent.as_posix()
            input_path = input_root / relative
            prediction_paths = [
                experiment_root / "models" / alias / "predictions" / relative
                for alias in model_aliases
            ]
            output_path = temporary / "data" / language / OUTPUT_FILENAME
            output_path.parent.mkdir(parents=True)
            language_stats = languages.setdefault(language, Counter())
            streams = [read_jsonl(input_path)] + [
                read_jsonl(path) for path in prediction_paths
            ]
            input_count = 0
            candidate_count = 0
            previous_id = ""
            with output_path.open("w", encoding="utf-8") as handle:
                for records in zip_longest(*streams, fillvalue=missing):
                    if any(record is missing for record in records):
                        raise ValueError(f"Input/prediction lengths differ for {relative}")
                    metadata = records[0]
                    pair_id = canonical_id(metadata)
                    if not pair_id or pair_id <= previous_id:
                        raise ValueError(f"Input IDs are missing or unsorted at {pair_id!r}")
                    previous_id = pair_id
                    if metadata.get("language") != language:
                        raise ValueError(f"Language/path mismatch for {pair_id}")
                    predictions = {
                        alias: normalize_prediction(record, alias, pair_id)
                        for alias, record in zip(model_aliases, records[1:])
                    }
                    input_count += 1
                    total["input_pairs"] += 1
                    language_stats["input_pairs"] += 1
                    anchor = predictions[anchor_model]
                    if anchor.strategy_count != 1:
                        total["anchor_not_singleton"] += 1
                        continue
                    winner = next(iter(anchor.codes))
                    confirmers = [
                        alias
                        for alias in confirmation_models
                        if predictions[alias].codes == {winner}
                    ]
                    if not confirmers:
                        total["no_exact_confirmation"] += 1
                        continue
                    record = candidate_record(
                        metadata,
                        predictions,
                        anchor_model,
                        confirmation_models,
                        winner,
                        confirmers,
                    )
                    handle.write(
                        json.dumps(record, ensure_ascii=False, separators=(",", ":"))
                        + "\n"
                    )
                    candidate_count += 1
                    total["candidate_pairs"] += 1
                    language_stats["candidate_pairs"] += 1
                    strategies[winner]["candidate_pairs"] += 1
                    tier = str(record["quality_tier"])
                    tiers[tier] += 1
                    for alias in confirmers:
                        confirmers_stats[alias] += 1
                    for source in sources_for(metadata):
                        sources.setdefault((language, source), Counter())[
                            "candidate_pairs"
                        ] += 1
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
            raise ValueError("Source pair total differs from the experiment config")
        if total["candidate_pairs"] != expected_candidates:
            raise ValueError(
                f"Observed {total['candidate_pairs']} candidates, expected {expected_candidates}"
            )
        if sum(tiers.values()) != expected_candidates:
            raise RuntimeError("Confirmation tiers do not partition candidates")

        language_rows = [
            {
                "language": language,
                "input_pairs": values["input_pairs"],
                "candidate_pairs": values["candidate_pairs"],
                "candidate_pct": percent(values["candidate_pairs"], values["input_pairs"]),
            }
            for language, values in sorted(languages.items())
        ]
        strategy_rows = [
            {
                "strategy_code": code,
                "strategy_label": CODE_LABELS[code],
                "candidate_pairs": strategies[code]["candidate_pairs"],
                "candidate_pct": percent(
                    strategies[code]["candidate_pairs"], expected_candidates
                ),
            }
            for code in CODES
        ]
        source_rows = [
            {
                "language": language,
                "source": source,
                "candidate_pairs": values["candidate_pairs"],
            }
            for (language, source), values in sorted(sources.items())
        ]
        confirmer_rows = [
            {
                "confirming_model": alias,
                "candidate_pairs": confirmers_stats[alias],
                "candidate_pct": percent(confirmers_stats[alias], expected_candidates),
            }
            for alias in confirmation_models
        ]
        write_csv(temporary / "CANDIDATE_MANIFEST.csv", manifest)
        write_csv(reports_root / "candidates_by_language.csv", language_rows)
        write_csv(reports_root / "candidates_by_strategy.csv", strategy_rows)
        write_csv(reports_root / "candidates_by_language_source.csv", source_rows)
        write_csv(reports_root / "candidates_by_confirming_model.csv", confirmer_rows)
        summary = {
            "schema": SUMMARY_SCHEMA,
            "candidate_id": candidate_id,
            "candidate_status": "unreviewed_model_consensus",
            "source_experiment_id": source_config["experiment_id"],
            "source_experiment_config": config["source_experiment_config"],
            "anchor_model": anchor_model,
            "confirmation_models": confirmation_models,
            "model_provenance": model_provenance,
            "selection": config["selection"],
            "selection_rule": SELECTION_RULE,
            "input_pairs": total["input_pairs"],
            "candidate_pairs": total["candidate_pairs"],
            "candidate_pct": percent(total["candidate_pairs"], total["input_pairs"]),
            "excluded": {
                "anchor_not_singleton": total["anchor_not_singleton"],
                "no_exact_confirmation": total["no_exact_confirmation"],
            },
            "confirmation_tiers": dict(sorted(tiers.items())),
            "confirming_models": dict(sorted(confirmers_stats.items())),
            "languages": language_rows,
            "strategies": strategy_rows,
            "manifest": manifest,
            "human_validation_required": True,
        }
        (reports_root / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        summary_markdown(
            reports_root / "summary.md",
            candidate_id,
            total["input_pairs"],
            total["candidate_pairs"],
            language_rows,
            strategy_rows,
            tiers,
        )
        (temporary / "candidate_config.json").write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
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


def normalized_codes(
    prediction: Mapping[str, Any], alias: str, pair_id: str
) -> list[str]:
    codes = prediction.get("predicted_codes")
    scores = prediction.get("strategy_scores")
    if not isinstance(codes, list) or not isinstance(scores, dict):
        raise ValueError(f"Invalid prediction for {alias}/{pair_id}")
    values = [str(code) for code in codes]
    if values != [code for code in CODES if code in values]:
        raise ValueError(f"Unordered or invalid codes for {alias}/{pair_id}")
    if int(prediction.get("strategy_count", -1)) != len(values):
        raise ValueError(f"Invalid strategy count for {alias}/{pair_id}")
    if set(scores) != set(CODES) or any(
        not math.isfinite(float(scores[code])) or not 0 <= float(scores[code]) <= 1
        for code in CODES
    ):
        raise ValueError(f"Invalid scores for {alias}/{pair_id}")
    return values


def validate(candidate_root: Path) -> dict[str, Any]:
    candidate_root = candidate_root.resolve()
    config = load_json(candidate_root / "candidate_config.json")
    summary = load_json(candidate_root / "reports" / "summary.json")
    if config.get("schema") != CONFIG_SCHEMA or summary.get("schema") != SUMMARY_SCHEMA:
        raise ValueError("Unexpected candidate config or summary schema")
    anchor = str(config["anchor_model"])
    confirmation_models = [str(value) for value in config["confirmation_models"]]
    model_aliases = [anchor, *confirmation_models]
    with (candidate_root / "CANDIDATE_MANIFEST.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        manifest = list(csv.DictReader(handle))
    if not manifest:
        raise ValueError("Empty candidate manifest")

    seen: set[str] = set()
    language_counts: Counter[str] = Counter()
    strategy_counts: Counter[str] = Counter()
    tier_counts: Counter[str] = Counter()
    confirmer_counts: Counter[str] = Counter()
    files: list[dict[str, Any]] = []
    for item in manifest:
        language = str(item["language"])
        path = candidate_root / str(item["output_file"])
        if path.stat().st_size != int(item["bytes"]) or sha256(path) != item["sha256"]:
            raise ValueError(f"Manifest integrity failure: {path}")
        lines = 0
        for record in read_jsonl(path):
            pair_id = canonical_id(record)
            if not pair_id or pair_id in seen:
                raise ValueError(f"Missing or duplicate candidate ID: {pair_id!r}")
            seen.add(pair_id)
            if record.get("language") != language:
                raise ValueError(f"Language/path mismatch for {pair_id}")
            if record.get("selection_rule") != SELECTION_RULE:
                raise ValueError(f"Selection-rule mismatch for {pair_id}")
            winner = str(record.get("candidate_strategy_code", ""))
            if winner not in CODES or record.get("candidate_strategy_label") != CODE_LABELS[winner]:
                raise ValueError(f"Invalid strategy for {pair_id}")
            predictions = record.get("model_predictions")
            if not isinstance(predictions, dict) or list(predictions) != model_aliases:
                raise ValueError(f"Prediction model inventory mismatch for {pair_id}")
            codes = {
                alias: normalized_codes(predictions[alias], alias, pair_id)
                for alias in model_aliases
            }
            if codes[anchor] != [winner]:
                raise ValueError(f"Gemma is not an exact singleton for {pair_id}")
            confirmers = [
                alias for alias in confirmation_models if codes[alias] == [winner]
            ]
            if not confirmers:
                raise ValueError(f"Candidate has no exact confirmation: {pair_id}")
            supporters = [anchor, *confirmers]
            if (
                record.get("anchor_model") != anchor
                or record.get("confirmation_models") != confirmation_models
                or record.get("confirming_models") != confirmers
                or int(record.get("confirmation_count", -1)) != len(confirmers)
                or record.get("supporting_models") != supporters
                or record.get("exact_singleton_supporting_models") != supporters
                or int(record.get("majority_votes", -1)) != len(supporters)
                or record.get("quality_tier") != confirmation_tier(len(confirmers))
            ):
                raise ValueError(f"Stored confirmation metadata differs for {pair_id}")
            lines += 1
            language_counts[language] += 1
            strategy_counts[winner] += 1
            tier_counts[confirmation_tier(len(confirmers))] += 1
            for alias in confirmers:
                confirmer_counts[alias] += 1
        if lines != int(item["candidate_pairs"]):
            raise ValueError(f"Manifest line count differs for {path}")
        files.append(
            {
                "language": language,
                "file": item["output_file"],
                "pairs": lines,
                "bytes": path.stat().st_size,
                "sha256": item["sha256"],
            }
        )

    observed = len(seen)
    if observed != int(summary["candidate_pairs"]):
        raise ValueError("Validated total differs from summary")
    expected_languages = {
        str(row["language"]): int(row["candidate_pairs"])
        for row in summary["languages"]
    }
    if dict(sorted(language_counts.items())) != expected_languages:
        raise ValueError("Validated language counts differ from summary")
    expected_strategies = {
        str(row["strategy_code"]): int(row["candidate_pairs"])
        for row in summary["strategies"]
    }
    if {code: strategy_counts[code] for code in CODES} != expected_strategies:
        raise ValueError("Validated strategy counts differ from summary")
    if dict(sorted(tier_counts.items())) != summary["confirmation_tiers"]:
        raise ValueError("Validated tier counts differ from summary")
    if dict(sorted(confirmer_counts.items())) != summary["confirming_models"]:
        raise ValueError("Validated confirmer counts differ from summary")
    result = {
        "schema": VALIDATION_SCHEMA,
        "candidate_id": summary["candidate_id"],
        "valid": True,
        "candidate_pairs": observed,
        "unique_canonical_pair_ids": observed,
        "languages": dict(sorted(language_counts.items())),
        "strategies": {code: strategy_counts[code] for code in CODES},
        "confirmation_tiers": dict(sorted(tier_counts.items())),
        "confirming_models": dict(sorted(confirmer_counts.items())),
        "files": files,
        "errors": [],
    }
    (candidate_root / "reports" / "validation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--validate-only", type=Path)
    args = parser.parse_args()
    if args.validate_only is not None:
        result = validate(args.validate_only)
    else:
        built = build(args.config, args.overwrite)
        result = {
            "build": built,
            "validation": validate(Path(built["output_root"])),
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
