#!/usr/bin/env python3
"""Generate resumable, controlled meaning degradations with pinned Qwen."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from phase6_degraded_corpus.src.common.contracts import read_jsonl


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_json(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("response contains no JSON object")
    value = json.loads(cleaned[start:end + 1])
    required = {"distorted_simplification", "changed_clean_span", "replacement_span", "corruption_type", "brief_verification"}
    missing = required - value.keys()
    if missing:
        raise ValueError(f"missing generated fields: {sorted(missing)}")
    return value


def append(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--tokenizer-path", type=Path, required=True)
    parser.add_argument("--tokenizer-revision", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    args = parser.parse_args()

    rows = read_jsonl(args.plan)
    if any(row["generation_status"] != "ready" for row in rows):
        raise ValueError("all plan records must pass clean review before generation")
    prompt = json.loads(args.prompt.read_text(encoding="utf-8"))
    completed = {}
    if args.output.exists():
        completed = {row["canonical_pair_id"]: row for row in read_jsonl(args.output) if row.get("status") == "generated_pending_audit"}

    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer_path, local_files_only=True)
    quantization = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16)
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
        user = prompt["user_template"].format(
            original=row["original"],
            clean_simplification=row["clean_simplification"],
            corruption_type=row["assigned_corruption"],
            target_span=row["target_cue"]["text"],
        )
        messages = [{"role": "system", "content": prompt["system"]}, {"role": "user", "content": user}]
        rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(rendered, return_tensors="pt").to(model.device)
        with torch.inference_mode():
            generated = model.generate(**inputs, do_sample=False, max_new_tokens=args.max_new_tokens)
        decoded = tokenizer.decode(generated[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        try:
            parsed = parse_json(decoded)
            distorted = parsed["distorted_simplification"].strip()
            checks = {
                "nonempty": bool(distorted),
                "different_from_clean": distorted != row["clean_simplification"],
                "type_matches_assignment": parsed["corruption_type"] == row["assigned_corruption"],
                "replacement_present": parsed["replacement_span"] in distorted,
                "changed_span_removed": parsed["changed_clean_span"] not in distorted,
                "length_ratio": round(len(distorted.split()) / max(1, len(row["clean_simplification"].split())), 4),
            }
            status = "generated_pending_audit" if all((checks["nonempty"], checks["different_from_clean"], checks["type_matches_assignment"], checks["replacement_present"], checks["changed_span_removed"])) else "failed_validation"
            error = None
        except Exception as exc:
            parsed, checks, status, error = None, {}, "failed_parse", str(exc)
        record = {
            "schema": "feats-phase6-generated-degradation-v1",
            "canonical_pair_id": pair_id,
            "canonical_original_id": row["canonical_original_id"],
            "original": row["original"],
            "clean_simplification": row["clean_simplification"],
            "predicted_strategy": row["predicted_strategy"],
            "target_axis": row["target_axis"],
            "target_score": row["target_score"],
            "assigned_corruption": row["assigned_corruption"],
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
            "tokenizer_source": "hannah-khallaf/e2r-strategy-qwen2.5-7b-pairwise-qlora",
            "tokenizer_revision": args.tokenizer_revision,
            "inference": {"quantization": "4-bit NF4", "compute_dtype": "bfloat16", "do_sample": False, "max_new_tokens": args.max_new_tokens, "batch_size": 1},
            "original_sha256": sha(row["original"]),
            "clean_simplification_sha256": sha(row["clean_simplification"]),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        append(args.output, record)
        print(f"[{index}/{len(rows)}] {status} {pair_id}", flush=True)


if __name__ == "__main__":
    main()
