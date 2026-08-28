#!/usr/bin/env python3
"""Build Stanza UD syntax sidecars and materialize them into UI payloads."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from collections import Counter
from itertools import zip_longest
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

try:
    from .data_contracts import (
        PAYLOAD_SCHEMA,
        SYNTAX_CONFIG_SCHEMA,
        SYNTAX_MANIFEST_SCHEMA,
        SYNTAX_SCHEMA,
        canonical_json,
        load_json,
        project_path,
        read_jsonl,
        sha256,
        with_payload_hash,
        write_jsonl_record,
    )
except ImportError:
    from data_contracts import (
        PAYLOAD_SCHEMA,
        SYNTAX_CONFIG_SCHEMA,
        SYNTAX_MANIFEST_SCHEMA,
        SYNTAX_SCHEMA,
        canonical_json,
        load_json,
        project_path,
        read_jsonl,
        sha256,
        with_payload_hash,
        write_jsonl_record,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = (
    PROJECT_ROOT / "phase4a_gold_standard" / "configs" / "stanza_ud_syntax_v1.json"
)
PAYLOAD_FILENAME = "annotation_tasks.jsonl"
SIDECAR_FILENAME = "stanza_ud_syntax.jsonl"
SYNTAX_MANIFEST_FILENAME = "SYNTAX_MANIFEST.json"
MATERIALIZED_MANIFEST_FILENAME = "MATERIALIZED_PAYLOAD_MANIFEST.json"
TERMINAL_TOKENS = frozenset({".", "!", "?", "。", "！", "？"})


class ParseContractError(ValueError):
    """A parser result violated the strict pretokenized 1:1 contract."""


def parse_feats(value: Any) -> dict[str, str]:
    if value in (None, "", "_"):
        return {}
    result: dict[str, str] = {}
    for item in str(value).split("|"):
        if "=" not in item:
            raise ParseContractError(f"Invalid UD feature: {item!r}")
        key, feature_value = item.split("=", 1)
        if not key or not feature_value or key in result:
            raise ParseContractError(f"Invalid or duplicate UD feature: {item!r}")
        result[key] = feature_value
    return dict(sorted(result.items()))


def validate_base_tokens(
    tokens: Any, text: str, *, task_id: str, side: str
) -> list[dict[str, Any]]:
    if not isinstance(tokens, list):
        raise ParseContractError(f"{side} tokens are not a list for {task_id}")
    result: list[dict[str, Any]] = []
    required = {"index", "text", "start", "end", "orthographic_parent_index"}
    for index, raw in enumerate(tokens):
        if not isinstance(raw, dict) or not required.issubset(raw):
            raise ParseContractError(f"Invalid {side} token {index} for {task_id}")
        token = dict(raw)
        if int(token["index"]) != index:
            raise ParseContractError(f"Non-global {side} token index for {task_id}")
        start, end = int(token["start"]), int(token["end"])
        if start < 0 or end < start or end > len(text):
            raise ParseContractError(f"Out-of-range {side} offset for {task_id}")
        if text[start:end] != token["text"]:
            raise ParseContractError(f"Inexact {side} token text for {task_id}")
        token["index"] = index
        token["start"] = start
        token["end"] = end
        token["orthographic_parent_index"] = int(
            token["orthographic_parent_index"]
        )
        result.append(token)
    return result


def sentence_ranges(
    tokens: Sequence[Mapping[str, Any]], text: str, *, split_sentences: bool
) -> list[tuple[int, int]]:
    if not tokens:
        return []
    if not split_sentences:
        return [(0, len(tokens))]
    result: list[tuple[int, int]] = []
    start = 0
    for index, token in enumerate(tokens):
        boundary = str(token["text"]) in TERMINAL_TOKENS
        if index + 1 < len(tokens):
            gap = text[int(token["end"]) : int(tokens[index + 1]["start"])]
            boundary = boundary or "\n" in gap or "\r" in gap
        if boundary:
            result.append((start, index + 1))
            start = index + 1
    if start < len(tokens):
        result.append((start, len(tokens)))
    return result


def fallback_tokens(
    tokens: Sequence[Mapping[str, Any]],
    ranges: Sequence[tuple[int, int]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for sentence_id, (start, end) in enumerate(ranges):
        for local_index, global_index in enumerate(range(start, end)):
            value = dict(tokens[global_index])
            value.update(
                {
                    "index": global_index,
                    "sentence_id": sentence_id,
                    "sentence_token_index": local_index,
                    "lemma": None,
                    "upos": None,
                    "xpos": None,
                    "feats": {},
                    "head_index": None,
                    "deprel": None,
                    "parse_status": "fallback",
                }
            )
            output.append(value)
    return output


def parse_side(
    pipeline: Any,
    base_tokens: Sequence[Mapping[str, Any]],
    text: str,
    *,
    task_id: str,
    side: str,
    split_sentences: bool,
) -> list[dict[str, Any]]:
    tokens = validate_base_tokens(base_tokens, text, task_id=task_id, side=side)
    ranges = sentence_ranges(tokens, text, split_sentences=split_sentences)
    if not tokens:
        return []
    pretokenized = [
        [str(tokens[index]["text"]) for index in range(start, end)]
        for start, end in ranges
    ]
    document = pipeline(pretokenized)
    sentences = list(getattr(document, "sentences", []))
    if len(sentences) != len(ranges):
        raise ParseContractError(
            f"{side} sentence count changed for {task_id}: "
            f"{len(ranges)} -> {len(sentences)}"
        )

    output: list[dict[str, Any]] = []
    for sentence_id, ((start, end), sentence) in enumerate(zip(ranges, sentences)):
        words = list(getattr(sentence, "words", []))
        if len(words) != end - start:
            raise ParseContractError(
                f"{side} token count changed in sentence {sentence_id} for {task_id}"
            )
        for local_index, (global_index, word) in enumerate(
            zip(range(start, end), words)
        ):
            word_id = getattr(word, "id", None)
            if isinstance(word_id, (list, tuple)) or int(word_id) != local_index + 1:
                raise ParseContractError(
                    f"{side} parser IDs are not 1:1 for {task_id}"
                )
            if str(getattr(word, "text", "")) != tokens[global_index]["text"]:
                raise ParseContractError(
                    f"{side} parser changed token text for {task_id}"
                )
            local_head = int(getattr(word, "head", 0) or 0)
            if local_head < 0 or local_head > len(words):
                raise ParseContractError(f"Invalid UD head for {task_id}")
            value = dict(tokens[global_index])
            value.update(
                {
                    "index": global_index,
                    "sentence_id": sentence_id,
                    "sentence_token_index": local_index,
                    "lemma": getattr(word, "lemma", None),
                    "upos": getattr(word, "upos", None),
                    "xpos": getattr(word, "xpos", None),
                    "feats": parse_feats(getattr(word, "feats", None)),
                    "head_index": (
                        None if local_head == 0 else start + local_head - 1
                    ),
                    "deprel": getattr(word, "deprel", None),
                    "parse_status": "parsed",
                }
            )
            output.append(value)
    if len(output) != len(tokens) or any(
        token["index"] != index for index, token in enumerate(output)
    ):
        raise ParseContractError(f"{side} global 1:1 validation failed for {task_id}")
    return output


def model_metadata(
    config: Mapping[str, Any], language: str
) -> dict[str, Any]:
    languages = config.get("languages")
    if not isinstance(languages, dict) or not isinstance(
        languages.get(language), dict
    ):
        raise ValueError(f"No pinned Stanza model configuration for {language}")
    language_config = languages[language]
    processors = language_config.get("packages")
    if not isinstance(processors, dict) or set(processors) != {
        "tokenize",
        "lemma",
        "pos",
        "depparse",
    }:
        raise ValueError(f"Incomplete processor package pin for {language}")
    stanza_version = str(config.get("stanza_version") or "")
    resources_version = str(config.get("resources_version") or "")
    if not stanza_version or not resources_version:
        raise ValueError("Stanza and resources versions must be pinned")
    return {
        "engine": "stanza",
        "stanza_version": stanza_version,
        "resources_version": resources_version,
        "language": str(language_config.get("stanza_language") or language),
        "packages": dict(processors),
        "model_md5": dict(language_config.get("model_md5") or {}),
        "use_gpu": bool(config.get("use_gpu", False)),
        "tokenize_pretokenized": True,
        "processors": ["tokenize", "pos", "lemma", "depparse"],
    }


def default_pipeline_factory(
    metadata: Mapping[str, Any],
    *,
    model_dir: Path,
) -> Any:
    try:
        import stanza
    except ImportError as error:
        raise RuntimeError("stanza is required to build syntax sidecars") from error
    actual_version = str(getattr(stanza, "__version__", ""))
    if actual_version != metadata["stanza_version"]:
        raise RuntimeError(
            f"Stanza version {actual_version!r} does not match "
            f"pin {metadata['stanza_version']!r}"
        )
    return stanza.Pipeline(
        lang=metadata["language"],
        processors="tokenize,pos,lemma,depparse",
        package=metadata["packages"],
        model_dir=str(model_dir),
        tokenize_pretokenized=True,
        download_method=None,
        use_gpu=bool(metadata.get("use_gpu", False)),
        verbose=False,
    )


def syntax_record(
    payload: Mapping[str, Any],
    pipeline: Any,
    metadata: Mapping[str, Any],
    *,
    split_sentences: bool,
    pipeline_error: str | None = None,
    fail_on_parse_error: bool = False,
) -> dict[str, Any]:
    if payload.get("schema") != PAYLOAD_SCHEMA:
        raise ValueError("Unexpected annotation payload schema")
    task_id = str(payload.get("task_id") or "")
    if not task_id:
        raise ValueError("Payload has no task_id")
    errors: dict[str, str] = {}
    parsed: dict[str, list[dict[str, Any]]] = {}
    sides = (
        ("source", "source_text", "source_tokens"),
        ("target", "target_text", "target_tokens"),
    )
    for side, text_key, token_key in sides:
        text = payload.get(text_key)
        if not isinstance(text, str):
            raise ValueError(f"Missing {side} text for {task_id}")
        base = validate_base_tokens(
            payload.get(token_key), text, task_id=task_id, side=side
        )
        ranges = sentence_ranges(base, text, split_sentences=split_sentences)
        try:
            if pipeline_error:
                raise RuntimeError(pipeline_error)
            parsed[side] = parse_side(
                pipeline,
                base,
                text,
                task_id=task_id,
                side=side,
                split_sentences=split_sentences,
            )
        except Exception as error:
            if fail_on_parse_error:
                raise
            errors[side] = f"{type(error).__name__}: {error}"
            parsed[side] = fallback_tokens(base, ranges)
    status = "parsed" if not errors else "fallback"
    return {
        "schema": SYNTAX_SCHEMA,
        "task_id": task_id,
        "review_task_id": payload.get("review_task_id", task_id),
        "canonical_pair_id": payload["canonical_pair_id"],
        "language": payload["language"],
        "status": status,
        "errors": errors,
        "model": dict(metadata),
        "source_tokens": parsed["source"],
        "target_tokens": parsed["target"],
    }


def resolve_payload_files(
    payload_root: Path, selected_languages: Sequence[str] | None
) -> list[tuple[str, Path]]:
    manifest_path = payload_root / "pool_manifest.json"
    if manifest_path.is_file():
        manifest = load_json(manifest_path)
        rows = manifest.get("files")
        if not isinstance(rows, list):
            raise ValueError("Invalid annotation pool manifest")
        values = [
            (str(row["language"]), payload_root / str(row["payload_file"]))
            for row in rows
        ]
    else:
        values = [
            (path.parent.name, path)
            for path in sorted((payload_root / "payloads").glob(f"*/{PAYLOAD_FILENAME}"))
        ]
    if selected_languages is not None:
        selected = set(selected_languages)
        values = [item for item in values if item[0] in selected]
        if {language for language, _ in values} != selected:
            raise ValueError("Some selected languages have no payload file")
    if not values:
        raise ValueError(f"No annotation payloads found under {payload_root}")
    return sorted(values)


def build(
    config_path: Path = DEFAULT_CONFIG,
    payload_root_override: Path | None = None,
    output_root_override: Path | None = None,
    overwrite: bool = False,
    fail_on_parse_error: bool = False,
    selected_languages_override: Sequence[str] | None = None,
    pipeline_factory: Callable[..., Any] = default_pipeline_factory,
) -> dict[str, Any]:
    config = load_json(config_path.resolve())
    if config.get("schema") != SYNTAX_CONFIG_SCHEMA:
        raise ValueError("Unexpected syntax config schema")
    payload_root = (
        payload_root_override.resolve()
        if payload_root_override is not None
        else project_path(config["payload_root"])
    )
    output_base = (
        output_root_override.resolve()
        if output_root_override is not None
        else project_path(config["output_root"])
    )
    syntax_id = str(config["syntax_id"])
    syntax_root = output_base / syntax_id
    if syntax_root.exists() and not overwrite:
        raise FileExistsError(f"Syntax output exists: {syntax_root}; use --overwrite")
    output_base.mkdir(parents=True, exist_ok=True)
    selected = config.get("selected_languages")
    selected_languages = (
        None if selected is None else [str(value) for value in selected]
    )
    if selected_languages_override is not None:
        selected_languages = [str(value) for value in selected_languages_override]
        if not selected_languages:
            raise ValueError("At least one selected language is required")
        if len(set(selected_languages)) != len(selected_languages):
            raise ValueError("Selected languages must be unique")
    files = resolve_payload_files(payload_root, selected_languages)
    model_dir = project_path(config["model_dir"])
    split_sentences = bool(config.get("split_sentences", True))
    temporary = Path(tempfile.mkdtemp(prefix=f".{syntax_id}-", dir=output_base))
    manifest_rows = []
    total_counts: Counter[str] = Counter()
    try:
        for language, payload_path in files:
            metadata = model_metadata(config, language)
            pipeline = None
            pipeline_error = None
            try:
                pipeline = pipeline_factory(metadata, model_dir=model_dir)
            except Exception as error:
                if fail_on_parse_error:
                    raise
                pipeline_error = f"{type(error).__name__}: {error}"
            output_path = (
                temporary / "sidecars" / language / SIDECAR_FILENAME
            )
            output_path.parent.mkdir(parents=True)
            counts: Counter[str] = Counter()
            with output_path.open("w", encoding="utf-8", newline="\n") as handle:
                for payload in read_jsonl(payload_path):
                    record = syntax_record(
                        payload,
                        pipeline,
                        metadata,
                        split_sentences=split_sentences,
                        pipeline_error=pipeline_error,
                        fail_on_parse_error=fail_on_parse_error,
                    )
                    write_jsonl_record(handle, record)
                    counts[record["status"]] += 1
                    total_counts[record["status"]] += 1
            manifest_rows.append(
                {
                    "language": language,
                    "input_payload_file": str(payload_path),
                    "input_payload_sha256": sha256(payload_path),
                    "sidecar_file": output_path.relative_to(temporary).as_posix(),
                    "sidecar_bytes": output_path.stat().st_size,
                    "sidecar_sha256": sha256(output_path),
                    "tasks": sum(counts.values()),
                    "parsed_tasks": counts["parsed"],
                    "fallback_tasks": counts["fallback"],
                    "model": metadata,
                    "pipeline_initialization_error": pipeline_error,
                }
            )
        manifest = {
            "schema": SYNTAX_MANIFEST_SCHEMA,
            "syntax_id": syntax_id,
            "payload_root": str(payload_root),
            "split_sentences": split_sentences,
            "tasks": sum(total_counts.values()),
            "parsed_tasks": total_counts["parsed"],
            "fallback_tasks": total_counts["fallback"],
            "files": manifest_rows,
        }
        (temporary / SYNTAX_MANIFEST_FILENAME).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        stored_config = dict(config)
        stored_config["source_config"] = str(config_path.resolve())
        (temporary / "syntax_config.json").write_text(
            json.dumps(stored_config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if syntax_root.exists():
            shutil.rmtree(syntax_root)
        temporary.replace(syntax_root)
        manifest["output_root"] = str(syntax_root)
        return manifest
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise


def _validate_materialized_tokens(
    base: Mapping[str, Any],
    parsed: Any,
    *,
    task_id: str,
    side: str,
) -> None:
    if not isinstance(parsed, list) or len(parsed) != len(base):
        raise ValueError(f"Syntax sidecar is not 1:1 on {side} for {task_id}")
    for index, (original, token) in enumerate(zip(base, parsed)):
        if (
            token.get("index") != index
            or token.get("text") != original.get("text")
            or token.get("start") != original.get("start")
            or token.get("end") != original.get("end")
            or token.get("orthographic_parent_index")
            != original.get("orthographic_parent_index")
            or token.get("parse_status") not in {"parsed", "fallback"}
        ):
            raise ValueError(f"Syntax/base token mismatch on {side} for {task_id}")


def materialize(
    payload_root: Path,
    syntax_root: Path,
    output_root: Path,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    payload_root = payload_root.resolve()
    syntax_root = syntax_root.resolve()
    output_root = output_root.resolve()
    syntax_manifest = load_json(syntax_root / SYNTAX_MANIFEST_FILENAME)
    if syntax_manifest.get("schema") != SYNTAX_MANIFEST_SCHEMA:
        raise ValueError("Unexpected syntax manifest schema")
    if output_root.exists() and not overwrite:
        raise FileExistsError(f"Materialized output exists: {output_root}; use --overwrite")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{output_root.name}-", dir=output_root.parent)
    )
    missing = object()
    manifest_rows = []
    try:
        for item in syntax_manifest["files"]:
            language = str(item["language"])
            payload_path = Path(item["input_payload_file"])
            sidecar_path = syntax_root / str(item["sidecar_file"])
            output_path = temporary / "payloads" / language / PAYLOAD_FILENAME
            output_path.parent.mkdir(parents=True)
            count = 0
            with output_path.open("w", encoding="utf-8", newline="\n") as handle:
                for payload, sidecar in zip_longest(
                    read_jsonl(payload_path), read_jsonl(sidecar_path), fillvalue=missing
                ):
                    if payload is missing or sidecar is missing:
                        raise ValueError(f"Payload/sidecar lengths differ for {language}")
                    task_id = str(payload.get("task_id") or "")
                    if (
                        sidecar.get("schema") != SYNTAX_SCHEMA
                        or sidecar.get("task_id") != task_id
                        or sidecar.get("canonical_pair_id")
                        != payload.get("canonical_pair_id")
                    ):
                        raise ValueError(f"Payload/sidecar identity mismatch for {task_id}")
                    _validate_materialized_tokens(
                        payload["source_tokens"],
                        sidecar["source_tokens"],
                        task_id=task_id,
                        side="source",
                    )
                    _validate_materialized_tokens(
                        payload["target_tokens"],
                        sidecar["target_tokens"],
                        task_id=task_id,
                        side="target",
                    )
                    value = dict(payload)
                    value["source_tokens"] = sidecar["source_tokens"]
                    value["target_tokens"] = sidecar["target_tokens"]
                    metadata = dict(value.get("public_metadata") or {})
                    metadata["syntax"] = {
                        "schema": SYNTAX_SCHEMA,
                        "status": sidecar["status"],
                        "errors": sidecar["errors"],
                        "model": sidecar["model"],
                    }
                    value["public_metadata"] = metadata
                    value = with_payload_hash(value)
                    write_jsonl_record(handle, value)
                    count += 1
            manifest_rows.append(
                {
                    "language": language,
                    "source_payload_file": str(payload_path),
                    "source_sidecar_file": str(sidecar_path),
                    "payload_file": output_path.relative_to(temporary).as_posix(),
                    "payload_bytes": output_path.stat().st_size,
                    "payload_sha256": sha256(output_path),
                    "tasks": count,
                }
            )
        manifest = {
            "schema": "feats-phase4a-syntax-materialized-payload-manifest-v1",
            "source_pool": str(payload_root),
            "syntax_root": str(syntax_root),
            "tasks": sum(int(row["tasks"]) for row in manifest_rows),
            "files": manifest_rows,
        }
        (temporary / MATERIALIZED_MANIFEST_FILENAME).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if output_root.exists():
            shutil.rmtree(output_root)
        temporary.replace(output_root)
        manifest["output_root"] = str(output_root)
        return manifest
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build", help="Build syntax sidecars.")
    build_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    build_parser.add_argument("--payload-root", type=Path)
    build_parser.add_argument("--output-root", type=Path)
    build_parser.add_argument("--language", action="append", dest="languages")
    build_parser.add_argument("--overwrite", action="store_true")
    build_parser.add_argument("--fail-on-parse-error", action="store_true")

    merge_parser = subparsers.add_parser(
        "materialize", help="Merge sidecars into import-ready payload JSONL."
    )
    merge_parser.add_argument("--payload-root", type=Path, required=True)
    merge_parser.add_argument("--syntax-root", type=Path, required=True)
    merge_parser.add_argument("--output-root", type=Path, required=True)
    merge_parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.command == "build":
        result = build(
            config_path=args.config,
            payload_root_override=args.payload_root,
            output_root_override=args.output_root,
            overwrite=args.overwrite,
            fail_on_parse_error=args.fail_on_parse_error,
            selected_languages_override=args.languages,
        )
    else:
        result = materialize(
            args.payload_root,
            args.syntax_root,
            args.output_root,
            overwrite=args.overwrite,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
