"""Run the canonical FEATS Phase 3b word-alignment pipeline."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_SCHEMA = "feats-phase2b-consolidated"
OUTPUT_SCHEMA = "feats-phase3b-word-alignment-v2"
CONFIG_SCHEMA = "feats-phase3b-word-alignment-config-v2"
REQUIRED_INPUT_FIELDS = {
    "id",
    "canonical_pair_id",
    "language",
    "original",
    "simple",
}
REQUIRED_SPECIALIZED_BACKENDS = {
    "ar": "camel_atb_surface",
    "ja": "spacy_sudachi",
    "sl": "stanza",
    "ur": "stanza",
}


@dataclass(frozen=True)
class TokenizationResult:
    """Alignment tokens plus their lossless relationship to the source text."""

    tokens: list[str]
    offsets: list[list[int]]
    orthographic_tokens: list[str]
    orthographic_offsets: list[list[int]]
    parent_indices: list[int]
    offset_exact: bool = True


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def environment_info() -> dict[str, Any]:
    packages = (
        "simalign",
        "spacy",
        "torch",
        "transformers",
        "tokenizers",
        "numpy",
        "SudachiPy",
        "SudachiDict-core",
        "camel-tools",
        "stanza",
    )
    info: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": {name: package_version(name) for name in packages},
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "slurm_array_job_id": os.environ.get("SLURM_ARRAY_JOB_ID"),
        "slurm_array_task_id": os.environ.get("SLURM_ARRAY_TASK_ID"),
    }
    try:
        import torch
    except ImportError:
        info["cuda_available"] = False
        return info
    info["cuda_available"] = bool(torch.cuda.is_available())
    if torch.cuda.is_available():
        info["cuda_device_name"] = torch.cuda.get_device_name(0)
    return info


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema") != CONFIG_SCHEMA:
        raise ValueError(f"Expected config schema {CONFIG_SCHEMA}: {path}")
    if config.get("input_schema") != INPUT_SCHEMA:
        raise ValueError(f"Expected input_schema {INPUT_SCHEMA}: {path}")
    if config.get("output_schema") != OUTPUT_SCHEMA:
        raise ValueError(f"Expected output_schema {OUTPUT_SCHEMA}: {path}")
    if config.get("aligner", {}).get("name") != "simalign":
        raise ValueError("Phase 3b currently supports aligner.name=simalign only.")
    files = config.get("selection", {}).get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("selection.files must be a non-empty list.")
    languages = [Path(str(value)).parent.as_posix() for value in files]
    if len(languages) != len(set(languages)):
        raise ValueError("selection.files must contain one file per language.")
    expected_counts = config.get("expected_counts", {})
    if set(expected_counts) != set(languages):
        raise ValueError("expected_counts must cover exactly the selected languages.")
    limit = config["selection"].get("limit_per_file")
    if limit is not None and (not isinstance(limit, int) or limit < 1):
        raise ValueError("selection.limit_per_file must be null or a positive integer.")
    max_subwords = config["aligner"].get("max_subwords_per_side")
    if not isinstance(max_subwords, int) or max_subwords < 1:
        raise ValueError("aligner.max_subwords_per_side must be a positive integer.")
    tokenization = config.get("tokenization", {})
    if not isinstance(tokenization.get("default"), dict):
        raise ValueError("tokenization.default must be configured.")
    specialized = tokenization.get("languages", {})
    for language, backend in REQUIRED_SPECIALIZED_BACKENDS.items():
        if language in languages and specialized.get(language, {}).get("backend") != backend:
            raise ValueError(f"Language {language} requires tokenization backend {backend}.")
    return config


def language_files(config: dict[str, Any]) -> dict[str, str]:
    return {
        Path(str(relative)).parent.as_posix(): str(relative)
        for relative in config["selection"]["files"]
    }


def line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def selected_count(total: int, limit: int | None) -> int:
    return total if limit is None else min(total, limit)


def read_input(path: Path, limit: int | None) -> Iterable[tuple[int, dict[str, Any]]]:
    with path.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if limit is not None and index >= limit:
                break
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON at {path}:{index + 1}: {error}") from error
            missing = REQUIRED_INPUT_FIELDS - set(record)
            if missing:
                raise ValueError(f"{path}:{index + 1} missing fields: {sorted(missing)}")
            pair_id = str(record["id"])
            if str(record["canonical_pair_id"]) != pair_id:
                raise ValueError(f"{path}:{index + 1} has inconsistent canonical ID")
            yield index, record


def normalize_spacy_language(language: str, configured: dict[str, str]) -> str:
    return configured.get(language, language.split("-", 1)[0])


def resolved_tokenizer_spec(language: str, tokenization: dict[str, Any]) -> dict[str, Any]:
    spec = dict(tokenization["default"])
    spec.update(tokenization.get("languages", {}).get(language, {}))
    return spec


def tokenizer_id_for(language: str, tokenization: dict[str, Any]) -> str:
    spec = resolved_tokenizer_spec(language, tokenization)
    backend = str(spec["backend"])
    if backend == "spacy_blank":
        code = normalize_spacy_language(
            language, dict(tokenization.get("spacy_language_map", {}))
        )
        return f"spacy:{code}:blank"
    if backend == "spacy_sudachi":
        return f"spacy:ja:sudachi:{spec.get('split_mode', 'A')}"
    if backend == "stanza":
        return f"stanza:{language}:{spec['package']}"
    if backend == "camel_atb_surface":
        return (
            f"camel-tools:{spec['model']}:{spec.get('scheme', 'atbtok')}:"
            "surface-preserving"
        )
    raise ValueError(f"Unsupported tokenizer backend {backend!r} for {language}.")


def _identity_result(tokens: list[str], offsets: list[list[int]]) -> TokenizationResult:
    if not tokens:
        raise ValueError("Tokenizer produced an empty token sequence.")
    return TokenizationResult(
        tokens=tokens,
        offsets=offsets,
        orthographic_tokens=list(tokens),
        orthographic_offsets=[list(offset) for offset in offsets],
        parent_indices=list(range(len(tokens))),
    )


class SpacyTokenizerAdapter:
    def __init__(self, language: str, tokenization: dict[str, Any], spec: dict[str, Any]):
        try:
            import spacy
        except ImportError as error:
            raise RuntimeError("spaCy is required for Phase 3b tokenization.") from error
        backend = spec["backend"]
        if backend == "spacy_sudachi":
            try:
                from spacy.lang.ja import Japanese, JapaneseTokenizer
            except ImportError as error:
                raise RuntimeError(
                    "Japanese tokenization requires SudachiPy and SudachiDict-core. "
                    "Run phase3b_word_alignment/jobs/setup_environment.sh."
                ) from error
            self.nlp = Japanese()
            self.nlp.tokenizer = JapaneseTokenizer(
                self.nlp.vocab, split_mode=str(spec.get("split_mode", "A"))
            )
        else:
            code = normalize_spacy_language(
                language, dict(tokenization.get("spacy_language_map", {}))
            )
            self.nlp = spacy.blank(code)
        self.tokenizer_id = tokenizer_id_for(language, tokenization)

    def tokenize(self, text: str) -> TokenizationResult:
        doc = self.nlp.make_doc(text)
        tokens = [token.text for token in doc if not token.is_space]
        offsets = [
            [token.idx, token.idx + len(token.text)] for token in doc if not token.is_space
        ]
        return _identity_result(tokens, offsets)


class StanzaTokenizerAdapter:
    def __init__(self, language: str, tokenization: dict[str, Any], spec: dict[str, Any]):
        try:
            import stanza
        except ImportError as error:
            raise RuntimeError(
                "Stanza is required for Urdu and Slovenian tokenization. "
                "Run phase3b_word_alignment/jobs/setup_environment.sh."
            ) from error
        model_dir = resolve_project_path(str(spec["model_dir"]))
        if not model_dir.is_dir():
            raise FileNotFoundError(f"Missing Stanza model directory: {model_dir}")
        self.pipeline = stanza.Pipeline(
            lang=language,
            processors="tokenize",
            package=str(spec["package"]),
            model_dir=str(model_dir),
            download_method=None,
            use_gpu=False,
            verbose=False,
        )
        self.tokenizer_id = tokenizer_id_for(language, tokenization)

    def tokenize(self, text: str) -> TokenizationResult:
        document = self.pipeline(text)
        stanza_tokens = [token for sentence in document.sentences for token in sentence.tokens]
        tokens = [str(token.text) for token in stanza_tokens]
        offsets = [[int(token.start_char), int(token.end_char)] for token in stanza_tokens]
        return _identity_result(tokens, offsets)


def surface_preserving_atb_ranges(surface: str, pieces: list[str]) -> list[tuple[int, int]]:
    """Use CAMeL clitic markers as boundaries without emitting normalized analyses."""

    prefixes: list[str] = []
    suffixes: list[str] = []
    cores: list[str] = []
    for piece in pieces:
        if piece.endswith("+") and not piece.startswith("+"):
            value = piece.rstrip("+").replace("_", "")
            if value:
                prefixes.append(value)
        elif piece.startswith("+") and not piece.endswith("+"):
            value = piece.lstrip("+").replace("_", "")
            if value:
                suffixes.append(value)
        else:
            value = piece.replace("_", "")
            if value:
                cores.append(value)

    start = 0
    prefix_ranges: list[tuple[int, int]] = []
    for prefix in prefixes:
        if not surface.startswith(prefix, start):
            return [(0, len(surface))]
        prefix_ranges.append((start, start + len(prefix)))
        start += len(prefix)

    # CAMeL may normalize a suffix, for example عن_+ني for the surface عني.
    # When the analysed core itself is an exact span, keep that boundary and
    # assign the remaining literal characters to the suffix instead of
    # emitting or matching the normalized suffix string.
    core = "".join(cores)
    if suffixes and core and surface.startswith(core, start):
        core_end = start + len(core)
        if core_end < len(surface):
            ranges = [*prefix_ranges, (start, core_end)]
            suffix_start = core_end
            later_suffix_ranges_reversed: list[tuple[int, int]] = []
            suffix_end = len(surface)
            for suffix in reversed(suffixes[1:]):
                candidate = suffix_end - len(suffix)
                if candidate <= suffix_start or surface[candidate:suffix_end] != suffix:
                    return [(0, len(surface))]
                later_suffix_ranges_reversed.append((candidate, suffix_end))
                suffix_end = candidate
            ranges.append((suffix_start, suffix_end))
            ranges.extend(reversed(later_suffix_ranges_reversed))
            if "".join(surface[left:right] for left, right in ranges) == surface:
                return ranges

    end = len(surface)
    suffix_ranges_reversed: list[tuple[int, int]] = []
    for suffix in reversed(suffixes):
        suffix_start = end - len(suffix)
        if suffix_start < start or surface[suffix_start:end] != suffix:
            return [(0, len(surface))]
        suffix_ranges_reversed.append((suffix_start, end))
        end = suffix_start

    ranges = list(prefix_ranges)
    if start < end:
        ranges.append((start, end))
    ranges.extend(reversed(suffix_ranges_reversed))
    if not ranges or "".join(surface[left:right] for left, right in ranges) != surface:
        return [(0, len(surface))]
    return ranges


class CamelATBSurfaceTokenizer:
    def __init__(self, language: str, tokenization: dict[str, Any], spec: dict[str, Any]):
        data_dir = resolve_project_path(str(spec["data_dir"]))
        if not data_dir.is_dir():
            raise FileNotFoundError(f"Missing CAMeL Tools data directory: {data_dir}")
        os.environ["CAMELTOOLS_DATA"] = str(data_dir)
        try:
            from camel_tools.disambig.mle import MLEDisambiguator
            from camel_tools.tokenizers.morphological import MorphologicalTokenizer
            from camel_tools.tokenizers.word import simple_word_tokenize
        except ImportError as error:
            raise RuntimeError(
                "CAMeL Tools is required for Arabic tokenization. "
                "Run phase3b_word_alignment/jobs/setup_environment.sh."
            ) from error
        disambiguator = MLEDisambiguator.pretrained(str(spec["model"]))
        self.morphological = MorphologicalTokenizer(
            disambiguator,
            scheme=str(spec.get("scheme", "atbtok")),
            split=True,
            diac=False,
        )
        self.simple_word_tokenize = simple_word_tokenize
        self.tokenizer_id = tokenizer_id_for(language, tokenization)

    def tokenize(self, text: str) -> TokenizationResult:
        orthographic_tokens = list(self.simple_word_tokenize(text))
        if not orthographic_tokens:
            raise ValueError("Tokenizer produced an empty token sequence.")
        orthographic_offsets: list[list[int]] = []
        cursor = 0
        for token in orthographic_tokens:
            start = text.find(token, cursor)
            if start < 0:
                raise ValueError(f"CAMeL orthographic token is not an exact text span: {token!r}")
            end = start + len(token)
            orthographic_offsets.append([start, end])
            cursor = end

        tokens: list[str] = []
        offsets: list[list[int]] = []
        parent_indices: list[int] = []
        for parent, (surface, orthographic_offset) in enumerate(
            zip(orthographic_tokens, orthographic_offsets, strict=True)
        ):
            pieces = list(self.morphological.tokenize([surface]))
            for relative_start, relative_end in surface_preserving_atb_ranges(surface, pieces):
                tokens.append(surface[relative_start:relative_end])
                offsets.append(
                    [
                        orthographic_offset[0] + relative_start,
                        orthographic_offset[0] + relative_end,
                    ]
                )
                parent_indices.append(parent)
        return TokenizationResult(
            tokens=tokens,
            offsets=offsets,
            orthographic_tokens=orthographic_tokens,
            orthographic_offsets=orthographic_offsets,
            parent_indices=parent_indices,
        )


def build_tokenizer(language: str, tokenization: dict[str, Any]) -> Any:
    spec = resolved_tokenizer_spec(language, tokenization)
    backend = spec["backend"]
    if backend in {"spacy_blank", "spacy_sudachi"}:
        return SpacyTokenizerAdapter(language, tokenization, spec)
    if backend == "stanza":
        return StanzaTokenizerAdapter(language, tokenization, spec)
    if backend == "camel_atb_surface":
        return CamelATBSurfaceTokenizer(language, tokenization, spec)
    raise ValueError(f"Unsupported tokenizer backend {backend!r} for {language}.")


def init_aligner(settings: dict[str, Any], device_override: str | None = None) -> Any:
    try:
        import torch
        from simalign import SentenceAligner
    except ImportError as error:
        raise RuntimeError(
            "SimAlign and torch are required. "
            "Run phase3b_word_alignment/jobs/setup_environment.sh."
        ) from error
    requested_device = device_override or str(settings.get("device", "auto"))
    device = (
        "cuda"
        if requested_device == "auto" and torch.cuda.is_available()
        else "cpu"
        if requested_device == "auto"
        else requested_device
    )
    if device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false.")
    return SentenceAligner(
        model=str(settings["model"]),
        token_type=str(settings.get("token_type", "bpe")),
        matching_methods=str(settings.get("matching_methods", "i")),
        device=device,
        layer=int(settings.get("layer", 8)),
    )


def subword_count(aligner: Any, tokens: list[str]) -> int:
    tokenizer = aligner.embed_loader.tokenizer
    return sum(len(tokenizer.tokenize(token)) for token in tokens)


def sanitize_links(
    raw_links: Iterable[tuple[int, int]], source_len: int, target_len: int
) -> list[list[int]]:
    links = {
        (int(source), int(target))
        for source, target in raw_links
        if 0 <= int(source) < source_len and 0 <= int(target) < target_len
    }
    return [[source, target] for source, target in sorted(links)]


def materialize_alignment(
    record: dict[str, Any],
    input_index: int,
    tokenizer: Any,
    aligner: Any,
    settings: dict[str, Any],
) -> dict[str, Any]:
    original_text = str(record["original"])
    simple_text = str(record["simple"])
    source = tokenizer.tokenize(original_text)
    target = tokenizer.tokenize(simple_text)
    source_subwords = subword_count(aligner, source.tokens)
    target_subwords = subword_count(aligner, target.tokens)
    maximum = int(settings["max_subwords_per_side"])
    status = "aligned"
    links: list[list[int]] = []
    if source_subwords > maximum or target_subwords > maximum:
        status = "skipped_model_length"
    else:
        alignments = aligner.get_word_aligns(source.tokens, target.tokens)
        heuristic = str(settings["heuristic"])
        if heuristic not in alignments:
            raise RuntimeError(
                f"SimAlign did not return heuristic {heuristic!r}; keys={sorted(alignments)}"
            )
        links = sanitize_links(
            alignments[heuristic], len(source.tokens), len(target.tokens)
        )

    linked_source = {source_index for source_index, _ in links}
    linked_target = {target_index for _, target_index in links}
    return {
        "schema": OUTPUT_SCHEMA,
        "input_schema": INPUT_SCHEMA,
        "id": str(record["id"]),
        "canonical_pair_id": str(record["canonical_pair_id"]),
        "language": str(record["language"]),
        "input_index": input_index,
        "original_text_sha256": text_sha256(original_text),
        "simple_text_sha256": text_sha256(simple_text),
        "tokenizer_id": str(tokenizer.tokenizer_id),
        "status": status,
        "original_tokens": source.tokens,
        "simple_tokens": target.tokens,
        "original_token_offsets": source.offsets,
        "simple_token_offsets": target.offsets,
        "original_token_offsets_exact": source.offset_exact,
        "simple_token_offsets_exact": target.offset_exact,
        "original_orthographic_tokens": source.orthographic_tokens,
        "simple_orthographic_tokens": target.orthographic_tokens,
        "original_orthographic_token_offsets": source.orthographic_offsets,
        "simple_orthographic_token_offsets": target.orthographic_offsets,
        "original_token_parent_indices": source.parent_indices,
        "simple_token_parent_indices": target.parent_indices,
        "alignment": links,
        "alignment_pharaoh": " ".join(
            f"{source_index}-{target_index}" for source_index, target_index in links
        ),
        "unaligned_original_indices": [
            index for index in range(len(source.tokens)) if index not in linked_source
        ],
        "unaligned_simple_indices": [
            index for index in range(len(target.tokens)) if index not in linked_target
        ],
        "n_original_tokens": len(source.tokens),
        "n_simple_tokens": len(target.tokens),
        "n_original_orthographic_tokens": len(source.orthographic_tokens),
        "n_simple_orthographic_tokens": len(target.orthographic_tokens),
        "n_original_subwords": source_subwords,
        "n_simple_subwords": target_subwords,
        "n_alignment_links": len(links),
    }


def recover_partial(path: Path, expected_schema: str = OUTPUT_SCHEMA) -> tuple[int, str | None]:
    """Drop an interrupted final line and return complete record count/last ID."""

    if not path.exists():
        return 0, None
    count = 0
    last_id: str | None = None
    with path.open("rb+") as handle:
        while True:
            start = handle.tell()
            line = handle.readline()
            if not line:
                break
            if not line.endswith(b"\n"):
                handle.truncate(start)
                break
            try:
                record = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                handle.truncate(start)
                break
            if record.get("schema") != expected_schema or not record.get("id"):
                handle.truncate(start)
                break
            count += 1
            last_id = str(record["id"])
    return count, last_id


def build_manifest(
    input_path: Path,
    relative_input: str,
    expected_total: int,
    limit: int | None,
) -> dict[str, Any]:
    if not input_path.is_file():
        raise FileNotFoundError(f"Phase 2b input does not exist: {input_path}")
    total = line_count(input_path)
    if total != expected_total:
        raise ValueError(
            f"Expected {expected_total} pairs in {relative_input}, observed {total}."
        )
    return {
        "schema": "feats-phase3b-input-manifest-v2",
        "source_phase": "phase2b_consolidation",
        "input_schema": INPUT_SCHEMA,
        "input_file": relative_input,
        "input_size_bytes": input_path.stat().st_size,
        "input_sha256": sha256(input_path),
        "total_pairs": total,
        "selected_pairs": selected_count(total, limit),
    }


def summarize_output(path: Path) -> dict[str, Any]:
    summary = {
        "processed_pairs": 0,
        "status_counts": {"aligned": 0, "skipped_model_length": 0},
        "tokens": {"original": 0, "simple": 0},
        "orthographic_tokens": {"original": 0, "simple": 0},
        "alignment_links": 0,
    }
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            summary["processed_pairs"] += 1
            summary["status_counts"][record["status"]] += 1
            summary["tokens"]["original"] += int(record["n_original_tokens"])
            summary["tokens"]["simple"] += int(record["n_simple_tokens"])
            summary["orthographic_tokens"]["original"] += int(
                record["n_original_orthographic_tokens"]
            )
            summary["orthographic_tokens"]["simple"] += int(
                record["n_simple_orthographic_tokens"]
            )
            summary["alignment_links"] += int(record["n_alignment_links"])
    return summary


def process_language(
    config: dict[str, Any],
    language: str,
    aligner: Any,
    resume: bool,
    overwrite: bool,
) -> Path:
    files = language_files(config)
    if language not in files:
        raise ValueError(f"Language {language!r} is not selected by the config.")
    input_root = resolve_project_path(str(config["input_root"]))
    output_root = resolve_project_path(str(config["output_root"]))
    run_root = output_root / language
    relative_input = files[language]
    input_path = input_root / relative_input
    output_path = run_root / "alignments" / "feats_word_alignments.jsonl"
    partial_path = output_path.with_suffix(output_path.suffix + ".partial")
    manifest_path = run_root / "input_manifest.json"
    run_config_path = run_root / "run_config.json"
    summary_path = run_root / "reports" / "summary.json"
    limit = config["selection"].get("limit_per_file")

    if output_path.exists():
        if resume and not overwrite:
            print(f"[{language}] already complete: {output_path}")
            return output_path
        if not overwrite:
            raise FileExistsError(f"Output exists; use --overwrite: {output_path}")
        output_path.unlink()
    if partial_path.exists() and overwrite:
        partial_path.unlink()
    if partial_path.exists() and not resume:
        raise FileExistsError(f"Partial output exists; use --resume or --overwrite: {partial_path}")

    manifest = build_manifest(
        input_path,
        relative_input,
        int(config["expected_counts"][language]),
        limit,
    )
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing != manifest:
            raise ValueError(f"Existing input manifest differs: {manifest_path}")
    else:
        atomic_json(manifest_path, manifest)

    processed, last_partial_id = recover_partial(partial_path) if resume else (0, None)
    if processed > int(manifest["selected_pairs"]):
        raise ValueError(f"Partial output has too many records: {partial_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tokenizer = build_tokenizer(language, config["tokenization"])
    started_at = utc_now()
    run_metadata = {
        "schema": "feats-phase3b-run-v2",
        "run_id": config["run_id"],
        "language": language,
        "tokenizer_id": tokenizer.tokenizer_id,
        "status": "running",
        "started_at": started_at,
        "config": config,
        "environment": environment_info(),
        "processed_pairs": processed,
    }
    atomic_json(run_config_path, run_metadata)

    invocation_counts = {"aligned": 0, "skipped_model_length": 0}
    start = perf_counter()
    mode = "a" if processed else "w"
    checkpoint_every = int(config.get("checkpoint_every", 100))
    observed_input = 0
    with partial_path.open(mode, encoding="utf-8") as output_handle:
        for input_index, record in read_input(input_path, limit):
            observed_input += 1
            if str(record["language"]) != language:
                raise ValueError(
                    f"{input_path}:{input_index + 1} language={record['language']!r}, "
                    f"expected {language!r}"
                )
            if input_index < processed:
                if input_index == processed - 1 and str(record["id"]) != last_partial_id:
                    raise ValueError("Partial output does not match the current input order.")
                continue
            aligned = materialize_alignment(
                record,
                input_index=input_index,
                tokenizer=tokenizer,
                aligner=aligner,
                settings=config["aligner"],
            )
            output_handle.write(
                json.dumps(aligned, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
            processed += 1
            invocation_counts[aligned["status"]] += 1
            if processed % checkpoint_every == 0:
                output_handle.flush()
                run_metadata["processed_pairs"] = processed
                run_metadata["updated_at"] = utc_now()
                atomic_json(run_config_path, run_metadata)
                print(
                    f"[{language}] {processed}/{manifest['selected_pairs']} pairs "
                    f"({perf_counter() - start:.1f}s)",
                    flush=True,
                )
        output_handle.flush()
        os.fsync(output_handle.fileno())

    if observed_input != int(manifest["selected_pairs"]):
        raise ValueError(
            f"Input selection changed: expected {manifest['selected_pairs']}, "
            f"observed {observed_input}."
        )
    if processed != int(manifest["selected_pairs"]):
        raise ValueError(
            f"Output incomplete: expected {manifest['selected_pairs']}, processed {processed}."
        )
    os.replace(partial_path, output_path)
    elapsed = perf_counter() - start
    aggregate = summarize_output(output_path)
    summary = {
        "schema": "feats-phase3b-summary-v2",
        "run_id": config["run_id"],
        "language": language,
        "tokenizer_id": tokenizer.tokenizer_id,
        "input_file": relative_input,
        "output_file": output_path.relative_to(output_root).as_posix(),
        **aggregate,
        "new_pairs_this_invocation": sum(invocation_counts.values()),
        "status_counts_this_invocation": invocation_counts,
        "elapsed_seconds_this_invocation": round(elapsed, 3),
        "pairs_per_second_this_invocation": round(
            sum(invocation_counts.values()) / elapsed, 3
        )
        if elapsed
        else None,
        "output_size_bytes": output_path.stat().st_size,
        "output_sha256": sha256(output_path),
    }
    atomic_json(summary_path, summary)
    run_metadata.update(
        {
            "status": "complete",
            "completed_at": utc_now(),
            "processed_pairs": processed,
            "summary_file": summary_path.relative_to(run_root).as_posix(),
        }
    )
    atomic_json(run_config_path, run_metadata)
    print(f"[{language}] complete: {output_path}")
    return output_path


def run(
    config_path: Path,
    requested_languages: list[str] | None,
    resume: bool,
    overwrite: bool,
    device: str | None = None,
) -> list[Path]:
    if resume and overwrite:
        raise ValueError("--resume and --overwrite are mutually exclusive.")
    config = load_config(config_path)
    available = list(language_files(config))
    languages = requested_languages or available
    unknown = set(languages) - set(available)
    if unknown:
        raise ValueError(f"Languages not selected by config: {sorted(unknown)}")
    aligner = init_aligner(config["aligner"], device_override=device)
    return [
        process_language(config, language, aligner, resume=resume, overwrite=overwrite)
        for language in languages
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--language", action="append", dest="languages")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--resume", action="store_true")
    group.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    outputs = run(
        args.config.resolve(),
        requested_languages=args.languages,
        resume=args.resume,
        overwrite=args.overwrite,
        device=args.device,
    )
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
