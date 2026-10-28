#!/usr/bin/env python3
"""Generate MMI v2 candidates (plan §3–§5) with vLLM and JSON-schema-constrained decoding.

Each planned row gets `n` candidates. The model only returns the edit; this script builds
the degraded sentence itself (span splice for MEANING, sentence-pair replacement for MOD,
direct text for ILLOC). Rule-based MEANING rows (number/date) are copied from the plan
unchanged, so every config shares them. Checks and selection happen later, in
`score_mmi_candidates.py`, identically for every config.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, stable_key, write_jsonl
from phase6_degraded_corpus.src.planning.plan_mmi_operations import fix_articles, splice

# Per axis, the newest prompt file a prompt directory has wins (v4 ILLOC makes a direct act indirect).
PROMPT_FILES = {"MEANING": ("meaning_span_v2.json",), "MOD": ("mod_same_count_v4.json", "mod_same_count_v3.json"),
                "ILLOC": ("illoc_indirect_v4.json", "illoc_inject_v3.json")}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_messages(row: dict, prompt: dict) -> list[dict]:
    """System + few-shot turns for the row's operation + the actual request."""
    axis = row["target_axis"]
    shots: list[tuple[str, str]] = []
    if axis == "MEANING":
        kind = row["meaning_type"]
        guidance = prompt["type_guidance"][kind]
        for original, simple, span, replacement, rationale in prompt["examples"][kind]:
            user = prompt["user_template"].format(
                original=original, clean_simplification=simple, meaning_type=kind, span=span, type_guidance=guidance
            )
            shots.append((user, json.dumps({"replacement": replacement, "rationale": rationale})))
        request = prompt["user_template"].format(
            original=row["original"], clean_simplification=row["clean_simplification"],
            meaning_type=kind, span=row["target_span"]["text"], type_guidance=guidance,
        )
    elif axis == "MOD":
        op = row["operation"]
        guidance = prompt["operation_guidance"][op]
        for clean, degraded in prompt["examples"][op]:
            # Plain Unicode: with \\u escapes in the shots the model escapes too, and Cyrillic outruns max_tokens.
            shots.append((prompt["user_template"].format(clean_simplification=clean, operation=op, operation_guidance=guidance),
                          json.dumps({"degraded": degraded}, ensure_ascii=False)))
        target = row.get("target_sentence_index")
        text = row["sentences"][target] if target is not None else row["clean_simplification"]
        request = prompt["user_template"].format(clean_simplification=text, operation=op, operation_guidance=guidance)
    else:
        op = row["operation"]
        guidance = prompt["operation_guidance"][op]
        for sentence, degraded in prompt["examples"][op]:
            shots.append((
                prompt["user_template"].format(clean_simplification=sentence, operation=op, operation_guidance=guidance),
                json.dumps({"degraded": degraded}, ensure_ascii=False),
            ))
        target = row.get("target_sentence_index")
        text = row["sentences"][target] if target is not None else row["clean_simplification"]
        request = prompt["user_template"].format(clean_simplification=text, operation=op, operation_guidance=guidance)
    messages = [{"role": "system", "content": prompt["system"]}]
    for user, assistant in shots:
        messages += [{"role": "user", "content": user}, {"role": "assistant", "content": assistant}]
    messages.append({"role": "user", "content": request})
    return messages


def merge_system(messages: list[dict]) -> list[dict]:
    """Gemma 3 has no system role: prepend the system text to the first user turn."""
    if messages[0]["role"] != "system":
        return messages
    system, rest = messages[0]["content"], [dict(m) for m in messages[1:]]
    rest[0]["content"] = f"{system}\n\n{rest[0]['content']}"
    return rest


def degraded_from(row: dict, parsed: dict | None) -> str | None:
    if parsed is None:
        return None
    axis = row["target_axis"]
    if axis == "MEANING":
        span = row["target_span"]
        return fix_articles(splice(row["clean_simplification"], span["start"], span["end"], parsed["replacement"].strip()))
    if axis in {"MOD", "ILLOC"}:
        target = row.get("target_sentence_index")
        if target is None:
            return parsed["degraded"].strip()
        sentences = list(row["sentences"])
        sentences[target] = parsed["degraded"].strip()
        return " ".join(sentences)
    return parsed["degraded"].strip()


def parse(text: str, required: list[str]) -> dict | None:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end < start:
            return None
        try:
            value = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    if not isinstance(value, dict) or any(not isinstance(value.get(key), str) for key in required):
        return None
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--config-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    experiment = json.loads(args.config.read_text(encoding="utf-8"))
    cfg = experiment["configs"][args.config_id]
    seed = experiment["seed"]
    prompt_dir = Path(experiment["prompt_dir"])
    prompts = {}
    for axis, names in PROMPT_FILES.items():  # language prompt sets cover only the axes they generate
        name = next((n for n in names if (prompt_dir / n).exists()), None)
        if name:
            prompts[axis] = json.loads((prompt_dir / name).read_text(encoding="utf-8"))
    rows = [row for row in read_jsonl(args.plan) if row.get("plan_status") == "ready"]
    if args.limit:
        rows = rows[: args.limit]

    from vllm import LLM, SamplingParams
    from vllm.sampling_params import GuidedDecodingParams
    import vllm
    import transformers

    llm = LLM(
        model=cfg["model_path"], tokenizer=cfg.get("tokenizer_path", cfg["model_path"]),
        dtype="bfloat16", seed=seed, max_model_len=cfg.get("max_model_len", 4096),
        gpu_memory_utilization=0.85, enforce_eager=False,
    )
    tokenizer = llm.get_tokenizer()
    llm_rows = [row for row in rows if row.get("generator_kind") == "llm"]
    rendered, params = [], []
    for row in llm_rows:
        prompt = prompts[row["target_axis"]]
        messages = build_messages(row, prompt)
        if cfg.get("merge_system"):
            messages = merge_system(messages)
        rendered.append(tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True))
        params.append(SamplingParams(
            n=cfg["n"], temperature=cfg["temperature"], top_p=cfg.get("top_p", 1.0),
            max_tokens=cfg.get("max_tokens", 160),
            seed=int(stable_key(seed, f'{args.config_id}:{row["canonical_pair_id"]}')[:8], 16),
            guided_decoding=GuidedDecodingParams(json=prompt["schema"]),
        ))
    outputs = llm.generate(rendered, params) if rendered else []
    by_id = {row["canonical_pair_id"]: out for row, out in zip(llm_rows, outputs)}

    provenance = {
        "config_id": args.config_id, "model": cfg["model_id"], "model_revision": cfg["model_revision"],
        "tokenizer": cfg.get("tokenizer_id", cfg["model_id"]),
        "decoding": {k: cfg.get(k) for k in ("n", "temperature", "top_p", "max_tokens")},
        "guided_json": True, "seed": seed,
        "versions": {"vllm": vllm.__version__, "transformers": transformers.__version__, "python": platform.python_version()},
    }
    records = []
    for row in rows:
        prompt = prompts[row["target_axis"]]
        required = list(prompt["schema"]["required"])
        if row.get("generator_kind") == "rule":
            candidates = [{"raw": None, "parsed": row["rule_output"], "degraded": row["rule_output"]["degraded"], "generator": "rule"}]
        else:
            out = by_id[row["canonical_pair_id"]]
            candidates = []
            for completion in out.outputs:
                parsed = parse(completion.text, required)
                candidates.append({"raw": completion.text, "parsed": parsed, "degraded": degraded_from(row, parsed), "generator": "llm"})
        records.append({
            "schema": "feats-phase6-mmi-generation-v2",
            **{k: row[k] for k in (
                "canonical_pair_id", "canonical_original_id", "corpus", "target_axis", "operation",
                "original", "clean_simplification", "clean_acceptability", "clean_nli_probabilities", "clean_entailment", "split", "language",
            ) if k in row},
            "meaning_type": row.get("meaning_type"), "generator_kind": row.get("generator_kind"),
            "target_span": row.get("target_span"), "merge_index": row.get("merge_index"), "sentences": row.get("sentences"),
            "target_sentence_index": row.get("target_sentence_index"),
            "candidates": candidates,
            "prompt_id": prompt["prompt_id"], "prompt_sha256": sha(json.dumps(prompt, sort_keys=True)),
            **provenance,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        })
    write_jsonl(args.output, records)
    print(json.dumps({"config_id": args.config_id, "rows": len(records), "llm_rows": len(llm_rows)}, indent=2))


if __name__ == "__main__":
    main()
