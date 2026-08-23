"""Validate Phase 3b v2 sidecars against their canonical Phase 2b inputs."""

from __future__ import annotations

import argparse
import json
from itertools import islice, zip_longest
from pathlib import Path
from typing import Any

from run_word_alignment import (
    INPUT_SCHEMA,
    OUTPUT_SCHEMA,
    atomic_json,
    language_files,
    load_config,
    resolve_project_path,
    sha256,
    text_sha256,
    tokenizer_id_for,
)


def _valid_offset(value: Any, text_length: int) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(item, int) for item in value)
        and 0 <= value[0] < value[1] <= text_length
    )


def validate_token_side(
    source_record: dict[str, Any],
    aligned: dict[str, Any],
    side: str,
    prefix: str,
) -> list[str]:
    errors: list[str] = []
    text_field = "original" if side == "original" else "simple"
    text = str(source_record.get(text_field, ""))
    tokens = aligned.get(f"{side}_tokens")
    offsets = aligned.get(f"{side}_token_offsets")
    orthographic_tokens = aligned.get(f"{side}_orthographic_tokens")
    orthographic_offsets = aligned.get(f"{side}_orthographic_token_offsets")
    parents = aligned.get(f"{side}_token_parent_indices")

    if not isinstance(tokens, list) or not tokens or not all(
        isinstance(token, str) and token for token in tokens
    ):
        errors.append(f"{prefix}: invalid {side}_tokens")
        tokens = []
    if not isinstance(offsets, list) or len(offsets) != len(tokens):
        errors.append(f"{prefix}: {side}_token_offsets is inconsistent")
        offsets = []
    if aligned.get(f"{side}_token_offsets_exact") is not True:
        errors.append(f"{prefix}: {side}_token_offsets_exact must be true")
    if not isinstance(orthographic_tokens, list) or not orthographic_tokens or not all(
        isinstance(token, str) and token for token in orthographic_tokens
    ):
        errors.append(f"{prefix}: invalid {side}_orthographic_tokens")
        orthographic_tokens = []
    if not isinstance(orthographic_offsets, list) or len(orthographic_offsets) != len(
        orthographic_tokens
    ):
        errors.append(f"{prefix}: {side}_orthographic_token_offsets is inconsistent")
        orthographic_offsets = []
    if not isinstance(parents, list) or len(parents) != len(tokens):
        errors.append(f"{prefix}: {side}_token_parent_indices is inconsistent")
        parents = []

    if aligned.get(f"n_{side}_tokens") != len(tokens):
        errors.append(f"{prefix}: n_{side}_tokens is inconsistent")
    if aligned.get(f"n_{side}_orthographic_tokens") != len(orthographic_tokens):
        errors.append(f"{prefix}: n_{side}_orthographic_tokens is inconsistent")
    if aligned.get(f"{side}_text_sha256") != text_sha256(text):
        errors.append(f"{prefix}: {side}_text_sha256 is inconsistent")

    previous_end = 0
    for index, (token, offset) in enumerate(zip(tokens, offsets)):
        if not _valid_offset(offset, len(text)):
            errors.append(f"{prefix}: invalid {side} token offset at index {index}")
            continue
        start, end = offset
        if start < previous_end:
            errors.append(f"{prefix}: overlapping/out-of-order {side} token offsets")
        previous_end = end
        if text[start:end] != token:
            errors.append(f"{prefix}: {side} token is not the exact source span at index {index}")

    previous_end = 0
    for index, (token, offset) in enumerate(zip(orthographic_tokens, orthographic_offsets)):
        if not _valid_offset(offset, len(text)):
            errors.append(f"{prefix}: invalid {side} orthographic offset at index {index}")
            continue
        start, end = offset
        if start < previous_end:
            errors.append(f"{prefix}: overlapping/out-of-order {side} orthographic offsets")
        previous_end = end
        if text[start:end] != token:
            errors.append(
                f"{prefix}: {side} orthographic token is not the exact source span at index {index}"
            )

    if parents and orthographic_tokens:
        if not all(isinstance(parent, int) for parent in parents):
            errors.append(f"{prefix}: non-integer {side} token parent")
        elif any(parent < 0 or parent >= len(orthographic_tokens) for parent in parents):
            errors.append(f"{prefix}: out-of-bounds {side} token parent")
        else:
            if parents != sorted(parents):
                errors.append(f"{prefix}: {side} token parents are out of order")
            if set(parents) != set(range(len(orthographic_tokens))):
                errors.append(f"{prefix}: {side} token parents do not cover orthographic tokens")
            for parent_index, orthographic_token in enumerate(orthographic_tokens):
                children = [
                    token for token, parent in zip(tokens, parents) if parent == parent_index
                ]
                if "".join(children) != orthographic_token:
                    errors.append(
                        f"{prefix}: {side} child tokens do not reconstruct orthographic token "
                        f"{parent_index}"
                    )
    return errors


def validate_record(
    source: dict[str, Any],
    aligned: dict[str, Any],
    language: str,
    index: int,
    expected_tokenizer_id: str,
) -> list[str]:
    pair_id = str(source.get("id", ""))
    prefix = f"{language}:{index + 1}:{pair_id}"
    errors: list[str] = []
    if aligned.get("schema") != OUTPUT_SCHEMA:
        errors.append(f"{prefix}: invalid output schema")
    if aligned.get("input_schema") != INPUT_SCHEMA:
        errors.append(f"{prefix}: invalid input schema")
    if str(aligned.get("id", "")) != pair_id:
        errors.append(f"{prefix}: output ID/order differs from input")
    if str(aligned.get("canonical_pair_id", "")) != pair_id:
        errors.append(f"{prefix}: canonical_pair_id is inconsistent")
    if aligned.get("language") != language or source.get("language") != language:
        errors.append(f"{prefix}: language is inconsistent")
    if aligned.get("input_index") != index:
        errors.append(f"{prefix}: input_index is inconsistent")
    if aligned.get("tokenizer_id") != expected_tokenizer_id:
        errors.append(f"{prefix}: tokenizer_id is inconsistent")

    errors.extend(validate_token_side(source, aligned, "original", prefix))
    errors.extend(validate_token_side(source, aligned, "simple", prefix))
    source_tokens = aligned.get("original_tokens")
    target_tokens = aligned.get("simple_tokens")
    source_tokens = source_tokens if isinstance(source_tokens, list) else []
    target_tokens = target_tokens if isinstance(target_tokens, list) else []

    links = aligned.get("alignment")
    if not isinstance(links, list):
        errors.append(f"{prefix}: alignment is not a list")
        links = []
    normalized_links: list[tuple[int, int]] = []
    for link in links:
        if (
            not isinstance(link, list)
            or len(link) != 2
            or not all(isinstance(value, int) for value in link)
        ):
            errors.append(f"{prefix}: malformed alignment link")
            continue
        source_index, target_index = link
        if not (0 <= source_index < len(source_tokens)) or not (
            0 <= target_index < len(target_tokens)
        ):
            errors.append(f"{prefix}: alignment link is out of bounds")
            continue
        normalized_links.append((source_index, target_index))
    if normalized_links != sorted(set(normalized_links)):
        errors.append(f"{prefix}: alignment links are not sorted and unique")
    if aligned.get("n_alignment_links") != len(links):
        errors.append(f"{prefix}: n_alignment_links is inconsistent")
    expected_pharaoh = " ".join(
        f"{source_index}-{target_index}" for source_index, target_index in normalized_links
    )
    if aligned.get("alignment_pharaoh") != expected_pharaoh:
        errors.append(f"{prefix}: alignment_pharaoh is inconsistent")

    linked_source = {source_index for source_index, _ in normalized_links}
    linked_target = {target_index for _, target_index in normalized_links}
    expected_unaligned_source = [
        token_index for token_index in range(len(source_tokens)) if token_index not in linked_source
    ]
    expected_unaligned_target = [
        token_index for token_index in range(len(target_tokens)) if token_index not in linked_target
    ]
    if aligned.get("unaligned_original_indices") != expected_unaligned_source:
        errors.append(f"{prefix}: unaligned_original_indices is inconsistent")
    if aligned.get("unaligned_simple_indices") != expected_unaligned_target:
        errors.append(f"{prefix}: unaligned_simple_indices is inconsistent")

    status = aligned.get("status")
    if status not in {"aligned", "skipped_model_length"}:
        errors.append(f"{prefix}: invalid status")
    if status == "skipped_model_length" and links:
        errors.append(f"{prefix}: skipped record contains alignment links")
    return errors


def validate_language(config: dict[str, Any], language: str) -> tuple[Path, dict[str, Any]]:
    files = language_files(config)
    if language not in files:
        raise ValueError(f"Language {language!r} is not selected by the config.")
    input_root = resolve_project_path(str(config["input_root"]))
    output_root = resolve_project_path(str(config["output_root"]))
    input_path = input_root / files[language]
    language_root = output_root / language
    output_path = language_root / "alignments" / "feats_word_alignments.jsonl"
    manifest_path = language_root / "input_manifest.json"
    run_config_path = language_root / "run_config.json"
    summary_path = language_root / "reports" / "summary.json"
    report_path = language_root / "reports" / "validation.json"
    expected_tokenizer_id = tokenizer_id_for(language, config["tokenization"])
    errors: list[str] = []
    error_count = 0

    def add_errors(values: list[str] | str) -> None:
        nonlocal error_count
        new_values = [values] if isinstance(values, str) else values
        error_count += len(new_values)
        if len(errors) < 100:
            errors.extend(new_values[: 100 - len(errors)])

    for required in (input_path, output_path, manifest_path, run_config_path, summary_path):
        if not required.is_file():
            add_errors(f"Missing required file: {required}")

    observed = 0
    status_counts = {"aligned": 0, "skipped_model_length": 0}
    limit = config["selection"].get("limit_per_file")
    if input_path.is_file() and output_path.is_file():
        with input_path.open(encoding="utf-8") as source_handle, output_path.open(
            encoding="utf-8"
        ) as output_handle:
            source_lines = islice(source_handle, limit) if limit is not None else source_handle
            for index, (source_line, output_line) in enumerate(
                zip_longest(source_lines, output_handle)
            ):
                if source_line is None:
                    add_errors("Output has more records than the selected input.")
                    break
                if output_line is None:
                    add_errors("Output has fewer records than the selected input.")
                    break
                try:
                    source = json.loads(source_line)
                    aligned = json.loads(output_line)
                except json.JSONDecodeError as error:
                    add_errors(f"{language}:{index + 1}: invalid JSON: {error}")
                    continue
                observed += 1
                status = aligned.get("status")
                if status in status_counts:
                    status_counts[status] += 1
                add_errors(
                    validate_record(
                        source, aligned, language, index, expected_tokenizer_id
                    )
                )

    expected_total = int(config["expected_counts"][language])
    expected = min(expected_total, limit) if limit is not None else expected_total
    if observed != expected:
        add_errors(f"Expected {expected} records, observed {observed}.")

    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema") != "feats-phase3b-input-manifest-v2":
            add_errors("input_manifest schema is inconsistent")
        if manifest.get("source_phase") != "phase2b_consolidation":
            add_errors("input_manifest source_phase is inconsistent")
        if manifest.get("input_schema") != INPUT_SCHEMA:
            add_errors("input_manifest input_schema is inconsistent")
        if manifest.get("input_file") != files[language]:
            add_errors("input_manifest input_file is inconsistent")
        if manifest.get("selected_pairs") != expected:
            add_errors("input_manifest selected_pairs is inconsistent")
        if input_path.is_file() and manifest.get("input_sha256") != sha256(input_path):
            add_errors("Input SHA-256 differs from input_manifest")

    if run_config_path.is_file():
        run_config = json.loads(run_config_path.read_text(encoding="utf-8"))
        if run_config.get("schema") != "feats-phase3b-run-v2":
            add_errors("run_config schema is inconsistent")
        if run_config.get("status") != "complete":
            add_errors("run_config status is not complete")
        if run_config.get("processed_pairs") != expected:
            add_errors("run_config processed_pairs is inconsistent")
        if run_config.get("tokenizer_id") != expected_tokenizer_id:
            add_errors("run_config tokenizer_id is inconsistent")
        if run_config.get("config") != config:
            add_errors("run_config captured config differs from the requested config")
    if summary_path.is_file() and output_path.is_file():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if summary.get("schema") != "feats-phase3b-summary-v2":
            add_errors("summary schema is inconsistent")
        if summary.get("processed_pairs") != expected:
            add_errors("summary processed_pairs is inconsistent")
        if summary.get("status_counts") != status_counts:
            add_errors("summary status_counts is inconsistent")
        if summary.get("tokenizer_id") != expected_tokenizer_id:
            add_errors("summary tokenizer_id is inconsistent")
        if summary.get("output_sha256") != sha256(output_path):
            add_errors("Output SHA-256 differs from summary")

    report = {
        "schema": "feats-phase3b-validation-v2",
        "run_id": config["run_id"],
        "language": language,
        "tokenizer_id": expected_tokenizer_id,
        "valid": error_count == 0,
        "expected_pairs": expected,
        "observed_pairs": observed,
        "status_counts": status_counts,
        "error_count": error_count,
        "errors": errors,
    }
    atomic_json(report_path, report)
    return report_path, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--language", action="append", dest="languages")
    args = parser.parse_args()
    config = load_config(args.config.resolve())
    languages = args.languages or list(language_files(config))
    valid = True
    for language in languages:
        report_path, report = validate_language(config, language)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"Validation report: {report_path}")
        valid = valid and bool(report["valid"])
    if not valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
