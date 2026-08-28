from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

from data_contracts import (
    PAYLOAD_SCHEMA,
    SYNTAX_CONFIG_SCHEMA,
    SYNTAX_SCHEMA,
    payload_hash,
    with_payload_hash,
)


SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from build_stanza_syntax_sidecars import (  # noqa: E402
    build,
    materialize,
    syntax_record,
)


class FakePipeline:
    def __init__(self, fail: bool = False):
        self.fail = fail

    def __call__(self, sentences: list[list[str]]) -> SimpleNamespace:
        if self.fail:
            raise RuntimeError("synthetic parser failure")
        parsed = []
        for values in sentences:
            words = [
                SimpleNamespace(
                    id=index + 1,
                    text=text,
                    lemma=text.lower(),
                    upos="PUNCT" if text == "." else "NOUN",
                    xpos="X",
                    feats="Number=Sing" if text != "." else None,
                    head=0 if index == 0 else 1,
                    deprel="root" if index == 0 else "punct",
                )
                for index, text in enumerate(values)
            ]
            parsed.append(SimpleNamespace(words=words))
        return SimpleNamespace(sentences=parsed)


def tokens(text: str) -> list[dict[str, object]]:
    values = []
    position = 0
    for index, token in enumerate(text.replace("\n", " ").split(" ")):
        start = text.index(token, position)
        end = start + len(token)
        position = end
        values.append(
            {
                "index": index,
                "text": token,
                "start": start,
                "end": end,
                "orthographic_parent_index": index,
                "parse_status": "not_parsed",
            }
        )
    return values


def payload() -> dict[str, object]:
    source = "One .\nTwo ."
    target = "Short ."
    value = {
        "schema": PAYLOAD_SCHEMA,
        "task_id": "review:en:syn:test",
        "review_task_id": "review:en:syn:test",
        "canonical_pair_id": "pair:en:test",
        "language": "en",
        "sources": ["fixture"],
        "source_text": source,
        "target_text": target,
        "candidate_strategy": "SYN",
        "source_tokens": tokens(source),
        "target_tokens": tokens(target),
        "simalign_links": [],
        "public_metadata": {},
        "model_votes": {"e5": "yes", "qwen": "yes", "xlmr": "no"},
        "queue_rank": 0,
    }
    return with_payload_hash(value)


def metadata() -> dict[str, object]:
    return {
        "engine": "stanza",
        "stanza_version": "1.10.1",
        "resources_version": "1.10.0",
        "language": "en",
        "packages": {
            "tokenize": "combined",
            "lemma": "combined_nocharlm",
            "pos": "combined_charlm",
            "depparse": "combined_charlm",
        },
        "model_md5": {},
        "tokenize_pretokenized": True,
        "processors": ["tokenize", "pos", "lemma", "depparse"],
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def test_global_heads_and_multisentence_contract() -> None:
    record = syntax_record(
        payload(),
        FakePipeline(),
        metadata(),
        split_sentences=True,
    )
    assert record["status"] == "parsed"
    source = record["source_tokens"]
    assert [token["index"] for token in source] == [0, 1, 2, 3]
    assert [token["sentence_id"] for token in source] == [0, 0, 1, 1]
    assert [token["sentence_token_index"] for token in source] == [0, 1, 0, 1]
    assert [token["head_index"] for token in source] == [None, 0, None, 2]
    assert source[0]["feats"] == {"Number": "Sing"}
    assert all(token["parse_status"] == "parsed" for token in source)


def test_parse_failure_has_strict_one_to_one_fallback() -> None:
    base = payload()
    record = syntax_record(
        base,
        FakePipeline(fail=True),
        metadata(),
        split_sentences=True,
    )
    assert record["status"] == "fallback"
    assert set(record["errors"]) == {"source", "target"}
    assert len(record["source_tokens"]) == len(base["source_tokens"])
    assert all(
        token["parse_status"] == "fallback"
        for token in record["source_tokens"]
    )
    assert [
        (token["text"], token["start"], token["end"])
        for token in record["source_tokens"]
    ] == [
        (token["text"], token["start"], token["end"])
        for token in base["source_tokens"]
    ]


def test_build_and_materialize_recomputes_payload_hash(tmp_path: Path) -> None:
    pool_root = tmp_path / "pool"
    input_path = pool_root / "payloads" / "en" / "annotation_tasks.jsonl"
    input_path.parent.mkdir(parents=True)
    input_path.write_text(
        json.dumps(payload(), ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_json(
        pool_root / "pool_manifest.json",
        {
            "schema": "feats-phase4a-annotation-pool-manifest-v1",
            "files": [
                {
                    "language": "en",
                    "payload_file": "payloads/en/annotation_tasks.jsonl",
                }
            ],
        },
    )
    config_path = tmp_path / "syntax.json"
    write_json(
        config_path,
        {
            "schema": SYNTAX_CONFIG_SCHEMA,
            "syntax_id": "fixture",
            "payload_root": str(pool_root),
            "output_root": str(tmp_path / "syntax"),
            "model_dir": str(tmp_path / "models"),
            "stanza_version": "1.10.1",
            "resources_version": "1.10.0",
            "split_sentences": True,
            "languages": {
                "en": {
                    "stanza_language": "en",
                    "packages": metadata()["packages"],
                    "model_md5": {},
                }
            },
        },
    )

    syntax_result = build(
        config_path,
        pipeline_factory=lambda _metadata, **_kwargs: FakePipeline(),
    )
    assert syntax_result["parsed_tasks"] == 1
    syntax_root = tmp_path / "syntax" / "fixture"
    materialized_root = tmp_path / "materialized"
    result = materialize(pool_root, syntax_root, materialized_root)
    assert result["tasks"] == 1
    output_path = (
        materialized_root / "payloads" / "en" / "annotation_tasks.jsonl"
    )
    merged = json.loads(output_path.read_text())
    assert merged["source_tokens"][2]["sentence_id"] == 1
    assert merged["source_tokens"][3]["head_index"] == 2
    assert merged["public_metadata"]["syntax"]["schema"] == SYNTAX_SCHEMA
    assert merged["payload_hash"] == payload_hash(merged)
