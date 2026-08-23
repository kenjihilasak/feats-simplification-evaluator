from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "src" / "run_word_alignment.py"
SPEC = importlib.util.spec_from_file_location("run_word_alignment", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FakeModelTokenizer:
    def tokenize(self, token: str) -> list[str]:
        return [token]


class FakeEmbedLoader:
    tokenizer = FakeModelTokenizer()


class FakeAligner:
    embed_loader = FakeEmbedLoader()

    def get_word_aligns(self, source: list[str], target: list[str]):
        assert source == ["A", "test", "."]
        assert target == ["A", "simple", "test", "."]
        return {"itermax": {(0, 0), (1, 2), (2, 3)}}


class FakeTokenizer:
    tokenizer_id = "spacy:en:blank"

    def tokenize(self, text: str):
        if text == "A test.":
            tokens = ["A", "test", "."]
            offsets = [[0, 1], [2, 6], [6, 7]]
        else:
            tokens = ["A", "simple", "test", "."]
            offsets = [[0, 1], [2, 8], [9, 13], [13, 14]]
        return MODULE.TokenizationResult(
            tokens=tokens,
            offsets=offsets,
            orthographic_tokens=list(tokens),
            orthographic_offsets=[list(offset) for offset in offsets],
            parent_indices=list(range(len(tokens))),
        )


def input_record() -> dict[str, str]:
    return {
        "id": "pair:en:1",
        "canonical_pair_id": "pair:en:1",
        "language": "en",
        "original": "A test.",
        "simple": "A simple test.",
    }


def test_materialize_alignment_contract() -> None:
    result = MODULE.materialize_alignment(
        input_record(),
        input_index=7,
        tokenizer=FakeTokenizer(),
        aligner=FakeAligner(),
        settings={"max_subwords_per_side": 510, "heuristic": "itermax"},
    )
    assert result["schema"] == MODULE.OUTPUT_SCHEMA
    assert result["input_schema"] == MODULE.INPUT_SCHEMA
    assert result["tokenizer_id"] == "spacy:en:blank"
    assert result["alignment"] == [[0, 0], [1, 2], [2, 3]]
    assert result["alignment_pharaoh"] == "0-0 1-2 2-3"
    assert result["unaligned_original_indices"] == []
    assert result["unaligned_simple_indices"] == [1]
    assert result["original_token_offsets"] == [[0, 1], [2, 6], [6, 7]]
    assert result["original_token_parent_indices"] == [0, 1, 2]
    assert result["original_token_offsets_exact"] is True


def test_model_length_is_explicitly_skipped() -> None:
    result = MODULE.materialize_alignment(
        input_record(),
        input_index=0,
        tokenizer=FakeTokenizer(),
        aligner=FakeAligner(),
        settings={"max_subwords_per_side": 2, "heuristic": "itermax"},
    )
    assert result["status"] == "skipped_model_length"
    assert result["alignment"] == []
    assert result["unaligned_original_indices"] == [0, 1, 2]


def test_recover_partial_truncates_interrupted_line(tmp_path: Path) -> None:
    partial = tmp_path / "output.jsonl.partial"
    first = {"schema": MODULE.OUTPUT_SCHEMA, "id": "one"}
    partial.write_bytes((json.dumps(first) + "\n" + '{"schema":').encode())
    count, last_id = MODULE.recover_partial(partial)
    assert (count, last_id) == (1, "one")
    assert partial.read_text() == json.dumps(first) + "\n"


def test_sanitize_links_deduplicates_sorts_and_bounds() -> None:
    assert MODULE.sanitize_links({(1, 0), (0, 1), (1, 0), (9, 9)}, 2, 2) == [
        [0, 1],
        [1, 0],
    ]


def test_surface_preserving_atb_ranges_split_exact_clitics() -> None:
    assert MODULE.surface_preserving_atb_ranges("ولم", ["و+", "لم"]) == [
        (0, 1),
        (1, 3),
    ]
    assert MODULE.surface_preserving_atb_ranges("عني", ["عن", "+ني"]) == [
        (0, 2),
        (2, 3),
    ]


def test_surface_preserving_atb_ranges_never_emits_normalized_stem() -> None:
    ranges = MODULE.surface_preserving_atb_ranges("ورحلاتنا", ["و+", "رحل"])
    assert ["ورحلاتنا"[start:end] for start, end in ranges] == ["و", "رحلاتنا"]
    assert MODULE.surface_preserving_atb_ranges("كتاب", ["X+", "كتاب"]) == [(0, 4)]


def test_tokenizer_ids_are_explicit() -> None:
    tokenization = {
        "default": {"backend": "spacy_blank"},
        "spacy_language_map": {"pt-BR": "pt"},
        "languages": {
            "ar": {
                "backend": "camel_atb_surface",
                "model": "calima-msa-r13",
                "scheme": "atbtok",
            },
            "ja": {"backend": "spacy_sudachi", "split_mode": "A"},
            "sl": {"backend": "stanza", "package": "ssj"},
            "ur": {"backend": "stanza", "package": "udtb"},
        },
    }
    assert MODULE.tokenizer_id_for("ar", tokenization).endswith("surface-preserving")
    assert MODULE.tokenizer_id_for("ja", tokenization) == "spacy:ja:sudachi:A"
    assert MODULE.tokenizer_id_for("sl", tokenization) == "stanza:sl:ssj"
    assert MODULE.tokenizer_id_for("ur", tokenization) == "stanza:ur:udtb"
    assert MODULE.tokenizer_id_for("pt-BR", tokenization) == "spacy:pt:blank"
