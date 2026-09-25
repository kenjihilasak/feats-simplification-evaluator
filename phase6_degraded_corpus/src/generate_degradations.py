#!/usr/bin/env python3
"""Generate resumable Phase 6 degradations for any configured target axis."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

from contracts import read_jsonl

REQUIRED_GENERATION_FIELDS = {
    "degraded_simplification",
    "changed_span",
    "replacement_span",
    "operation_type",
    "brief_verification",
}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_generation(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("response contains no JSON object")
    value = json.loads(cleaned[start : end + 1])
    value = {str(key).strip(): item for key, item in value.items()}
    missing = REQUIRED_GENERATION_FIELDS - value.keys()
    if missing:
        raise ValueError(f"missing generated fields: {sorted(missing)}")
    if not all(isinstance(value[key], str) for key in REQUIRED_GENERATION_FIELDS):
        raise ValueError("all generated fields must be strings")
    return value


def automatic_checks(row: dict, generation: dict) -> dict:
    degraded = generation["degraded_simplification"].strip()
    replacement = generation["replacement_span"].strip()
    changed = generation["changed_span"].strip()
    ratio = len(degraded.split()) / max(1, len(row["clean_simplification"].split()))
    return {
        "nonempty": bool(degraded),
        "different_from_clean": degraded != row["clean_simplification"],
        "operation_matches_assignment": generation["operation_type"] == row["assigned_operation"],
        "changed_span_declared": bool(changed),
        "replacement_present_or_deletion": not replacement or replacement in degraded,
        "finite_length_ratio": math.isfinite(ratio),
        "length_ratio": round(ratio, 4),
    }


def _append(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def _load_completed(path: Path) -> set[str]:
    if not path.exists():
        return set()
    rows = read_jsonl(path)
    ids = [row["canonical_pair_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate canonical_pair_id in resumable output")
    return set(ids)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--prompt-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--tokenizer-path", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--tokenizer-revision", required=True)
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    args = parser.parse_args()
    if not args.model_path.exists():
        raise FileNotFoundError(f"model checkpoint not found: {args.model_path}")
    if not args.tokenizer_path.exists():
        raise FileNotFoundError(f"tokenizer checkpoint not found: {args.tokenizer_path}")
    if args.num_shards < 1 or not 0 <= args.shard_index < args.num_shards:
        raise ValueError("invalid shard configuration")

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    all_rows = read_jsonl(args.manifest)
    ids = [row["canonical_pair_id"] for row in all_rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate canonical_pair_id in generation manifest")
    rows = [
        row for row in all_rows
        if int(sha(row["canonical_pair_id"]), 16) % args.num_shards == args.shard_index
    ]
    prompts = {}
    for axis in {row["target_axis"] for row in rows}:
        path = args.prompt_dir / f"{axis.lower()}_degradation_v1.json"
        if not path.exists():
            raise FileNotFoundError(f"prompt not found for {axis}: {path}")
        prompts[axis] = json.loads(path.read_text(encoding="utf-8"))
    completed = _load_completed(args.output)

    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer_path, local_files_only=True)
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        local_files_only=True,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        quantization_config=quantization,
    )
    model.eval()
    for index, row in enumerate(rows, 1):
        pair_id = row["canonical_pair_id"]
        if pair_id in completed:
            print(f"[{index}/{len(rows)}] skip {pair_id}", flush=True)
            continue
        prompt = prompts[row["target_axis"]]
        user = prompt["user_template"].format(
            original=row["original"],
            clean_simplification=row["clean_simplification"],
            assigned_operation=row["assigned_operation"],
            target_cue=row["target_cue"]["text"],
        )
        messages = [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": user},
        ]
        rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(rendered, return_tensors="pt").to(model.device)
        try:
            with torch.inference_mode():
                generated = model.generate(
                    **inputs,
                    do_sample=False,
                    max_new_tokens=args.max_new_tokens,
                )
        except torch.cuda.OutOfMemoryError as exc:
            raise RuntimeError(f"CUDA OOM while generating {pair_id}") from exc
        decoded = tokenizer.decode(
            generated[0, inputs["input_ids"].shape[1] :], skip_special_tokens=True
        ).strip()
        try:
            parsed = parse_generation(decoded)
            checks = automatic_checks(row, parsed)
            required = [value for key, value in checks.items() if key != "length_ratio"]
            status = "generated_pending_audit" if all(required) else "failed_validation"
            error = None
        except Exception as exc:
            parsed, checks, status, error = None, {}, "failed_parse", str(exc)
        record = {
            "schema": "feats-phase6-generated-degradation-v2",
            "canonical_pair_id": pair_id,
            "canonical_original_id": row["canonical_original_id"],
            "original": row["original"],
            "clean_simplification": row["clean_simplification"],
            "source_strategy": row["source_strategy"],
            "target_axis": row["target_axis"],
            "clean_score": 1.0,
            "degraded_score": 0.0,
            "assigned_operation": row["assigned_operation"],
            "target_cue": row["target_cue"],
            "generation": parsed,
            "raw_response": decoded,
            "automatic_checks": checks,
            "status": status,
            "error": error,
            "prompt_id": prompt["prompt_id"],
            "prompt_sha256": sha(json.dumps(prompt, ensure_ascii=False, sort_keys=True)),
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "model_revision": args.revision,
            "tokenizer_revision": args.tokenizer_revision,
            "inference": {
                "quantization": "4-bit NF4",
                "compute_dtype": "bfloat16",
                "do_sample": False,
                "max_new_tokens": args.max_new_tokens,
                "batch_size": 1,
                "num_shards": args.num_shards,
                "shard_index": args.shard_index,
            },
            "original_sha256": sha(row["original"]),
            "clean_simplification_sha256": sha(row["clean_simplification"]),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        _append(args.output, record)
        print(f"[{index}/{len(rows)}] {status} {pair_id}", flush=True)


if __name__ == "__main__":
    main()

