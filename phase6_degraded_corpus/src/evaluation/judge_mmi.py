#!/usr/bin/env python3
"""Cross-family LLM judge for MMI degradations (plan §6.2), with calibration.

`--mode calibrate` judges the frozen MEANING pilot outputs, whose validity is known from the
human audit (v1 output valid iff accepted as `qwen_v1`; retry valid iff `qwen_v2_retry`).
`--mode judge` judges the selected (or first) candidate of every row of a scored file.
Greedy decoding with a JSON schema. The judge never sees which config produced the text.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, write_jsonl
from phase6_degraded_corpus.src.generation.generate_mmi_v2 import merge_system, parse

SCHEMA = {
    "type": "object",
    "properties": {
        "target_axis_changed": {"type": "boolean"},
        "single_change": {"type": "boolean"},
        "other_axes_preserved": {"type": "boolean"},
        "valid": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": ["target_axis_changed", "single_change", "other_axes_preserved", "valid", "reason"],
}
SYSTEM = ("You audit controlled negative examples for a text-simplification dataset. Be strict. "
          "Answer only with the requested JSON object.")
AXIS_RULES = {
    "MEANING": ("The degraded text must contain exactly ONE factual change that makes it CONTRADICT the Original "
                "(a wrong number, date, entity, event, property, relation, or a flipped negation). It must stay fluent, "
                "and everything else must be unchanged. Paraphrase, omission, or a weaker-but-still-true statement is NOT valid."),
    "MOD": ("The degraded text must merge exactly TWO adjacent sentences of the Simplified text into ONE sentence "
            "(conjunction, relative clause or participle). No fact may be added, removed or changed, word choice must stay "
            "the same apart from joining words and pronouns, and the result must be grammatical."),
    "ILLOC": ("The degraded text must change ONLY the communicative force of the Simplified sentence (statement -> question, "
              "statement -> instruction to the reader, or statement -> hedged/uncertain claim) while keeping the same "
              "proposition and all facts. Any factual change, omission or extra content makes it invalid."),
}
USER = ("Axis: {axis}\nRule: {rule}\n\nOriginal: {original}\nSimplified: {clean}\nDegraded: {degraded}\n\n"
        "Check: did the degraded text make the required change (target_axis_changed)? Is it exactly one change "
        "(single_change)? Are facts, fluency and everything else preserved (other_axes_preserved)? "
        "valid = all three are true.")


def calibration_items(pilot_dir: Path) -> list[dict]:
    audit = {r["canonical_pair_id"]: r["accepted_source"] for r in read_jsonl(pilot_dir / "degradation/generation_audit.jsonl")}
    items = []
    for name, source in (("generated_50.jsonl", "qwen_v1"), ("retry_v2.jsonl", "qwen_v2_retry")):
        for row in read_jsonl(pilot_dir / "degradation" / name):
            degraded = (row.get("generation") or {}).get("distorted_simplification")
            if not degraded or row["canonical_pair_id"] not in audit:
                continue
            items.append({
                "item_id": f'{row["canonical_pair_id"]}:{source}', "axis": "MEANING",
                "original": row["original"], "clean": row["clean_simplification"], "degraded": degraded,
                "human_valid": audit[row["canonical_pair_id"]] == source,
            })
    return items


def scored_items(rows: list[dict]) -> list[dict]:
    items = []
    for row in rows:
        idx = row["selected_index"] if row.get("selected_index") is not None else 0
        cand = row["candidates"][idx] if row["candidates"] else None
        if not cand or not cand.get("degraded"):
            continue
        items.append({"item_id": row["canonical_pair_id"], "axis": row["target_axis"], "original": row["original"],
                      "clean": row["clean_simplification"], "degraded": cand["degraded"], "automatic_valid": row["yield"]})
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("calibrate", "judge"), required=True)
    parser.add_argument("--judge-config-id", required=True, help="config id in the generation config used as judge")
    parser.add_argument("--generation-config", type=Path, required=True)
    parser.add_argument("--pilot-dir", type=Path, default=Path("phase6_degraded_corpus/runs/meaning_en_pilot_v1"))
    parser.add_argument("--scored", type=Path, nargs="*", default=[])
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.generation_config.read_text())["configs"][args.judge_config_id]

    batches = {"calibration": calibration_items(args.pilot_dir)} if args.mode == "calibrate" else {
        path.stem: scored_items(read_jsonl(path)) for path in args.scored}

    from vllm import LLM, SamplingParams
    from vllm.sampling_params import GuidedDecodingParams

    llm = LLM(model=cfg["model_path"], dtype="bfloat16", max_model_len=4096, gpu_memory_utilization=0.85)
    tok = llm.get_tokenizer()
    params = SamplingParams(temperature=0.0, max_tokens=200, guided_decoding=GuidedDecodingParams(json=SCHEMA))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {"judge": cfg["model_id"], "judge_revision": cfg["model_revision"]}
    for name, items in batches.items():
        prompts = []
        for it in items:
            messages = [{"role": "system", "content": SYSTEM},
                        {"role": "user", "content": USER.format(axis=it["axis"], rule=AXIS_RULES[it["axis"]], original=it["original"],
                                                                clean=it["clean"], degraded=it["degraded"])}]
            if cfg.get("merge_system"):
                messages = merge_system(messages)
            prompts.append(tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True))
        outputs = llm.generate(prompts, params)
        for it, out in zip(items, outputs):
            verdict = parse(out.outputs[0].text, []) or {}
            it["judge"] = verdict
            it["judge_valid"] = bool(verdict.get("valid"))
        write_jsonl(args.output_dir / f"{name}.{args.judge_config_id}.jsonl", items)
        reference = "human_valid" if args.mode == "calibrate" else "automatic_valid"
        agree = sum(it["judge_valid"] == it[reference] for it in items)
        summary[name] = {"n": len(items), f"agreement_with_{reference}": agree / max(1, len(items)),
                         "judge_valid_rate": sum(it["judge_valid"] for it in items) / max(1, len(items))}
    (args.output_dir / f"summary.{args.mode}.{args.judge_config_id}.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
