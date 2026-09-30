# Plan: full MMI v2 corpus generation (MEANING, MOD, ILLOC)

Execution plan. Experiment id: **`mmi_en_v2_full`**. English only.

## 0. Context

The pipeline-selection experiment `mmi_en_v2` is closed ([results](../reports/current/mmi_v2_model_comparison.md)). This plan generates the complete synthetic training corpus with the selected configurations, which are documented in [`../methodology/`](../methodology/README.md):

| Axis | Config id | Model | Human valid (heldout) |
|---|---|---|---|
| MEANING | `C1` | Qwen2.5-7B-Instruct bf16, planner v2.1 (rule-based number/date/negation) | 88% |
| MOD | `C2` | Gemma-3-12B-it bf16 | 95% |
| ILLOC | `C1` | Qwen2.5-7B-Instruct bf16; operations question, directive **and hedged** (decision 2026-09-30: hedged = ILLOC) | 90% (question + directive) |

Everything needed already exists:
- planner [`plan_mmi_operations.py`](../../src/planning/plan_mmi_operations.py);
- generator [`generate_mmi_v2.py`](../../src/generation/generate_mmi_v2.py);
- checks [`score_mmi_candidates.py`](../../src/evaluation/score_mmi_candidates.py);
- configs `configs/experiments/mmi_en_v2_{pools,generation}.json`;
- venv `.venv-phase6-vllm` (vLLM 0.10.0, transformers 4.55.4);
- Slurm job `jobs/submit_mmi_v2_generate_gpu.sh`.

This plan **reuses them unchanged**: no prompt, planner or check changes. If a change looks necessary, **STOP** and report instead of changing it.

## 1. Hard constraints

1. Do not modify `runs/mmi_en_v2/` (the selection experiment). All outputs go under `runs/mmi_en_v2_full/` (Git-ignored).
2. The input contract is [`../inputs.md`](../inputs.md): the text-repaired `target_simple` Phase 2b variant; reserved evaluation originals excluded (exact and near duplicates); skip rows with `repaired_duplicate_of`.
3. **Pairs audited by humans are not used for training.** Exclude every `canonical_original_id` in `runs/mmi_en_v2/splits/heldout.jsonl` and `heldout_meaning_v21.jsonl`, and record them in `excluded_audited_originals.txt`. They stay available as a human-verified validation set. `dev` pairs **are** included: they were only used for pipeline selection.
4. One pair → one `target_axis`; one original → one axis and one split.
5. Reproducibility as in `mmi_en_v2`: `stable_key` seeds, pinned model and checker revisions, prompt sha256, and library versions in every row.
6. Stop at every **STOP**.

## 2. Axis allocation (rebalanced)

The `mmi_en_v2` pools filled MEANING before ILLOC, which gave MEANING about 17k pairs and ILLOC about 2.6k. Almost every MEANING-eligible pair is also ILLOC-eligible (about 17k of about 17.1k). Re-allocate **all** eligible pairs (pool rows plus `dev`, minus the exclusions of §1.3) with this rule, per source:

1. **MOD** gets every MOD-eligible pair (the scarcest axis; about 3.9k).
2. The remaining pairs eligible for **both** MEANING and ILLOC are split to **equalize** the final MEANING and ILLOC counts. Assignment is by `stable_key`; pairs eligible for only one axis go there first.
3. **ILLOC operations** are balanced within each source: ⅓ question, ⅓ directive, ⅓ hedged.

Expected counts (before generation losses): MOD about 3.9k; MEANING and ILLOC about 9.9k each. Vikidia contributes only its `dev` pairs (about 94): all its other pairs are in the audited heldout.

New module `src/selection/allocate_mmi_full.py`, which writes `runs/mmi_en_v2_full/allocation/{axis}_{source}.jsonl` and `allocation_report.json` (counts per axis × source × operation, and the exclusions). **Test:** determinism; no original in two axes; heldout originals absent; the balancing rule on a synthetic example.

## 3. Planning and generation

1. Plan with `plan_mmi_operations.py` (current code = v2.1) → `runs/mmi_en_v2_full/plans/plan.jsonl`. Rows with `plan_status != ready` are dropped and counted.
2. Split the plan into shards of about 2,000 rows (`plan_shard_XX.jsonl`), grouped by the axis's generator model.
3. Generate with `generate_mmi_v2.py`: config `C1` for MEANING and ILLOC shards, `C2` for MOD shards. Use a Slurm array (one GPU per shard) with a job script `jobs/submit_mmi_full_generate_gpu.sh`, which is a copy of the existing one with shard arguments. Resumable: skip shards whose output already exists and validates.
4. Score with `score_mmi_candidates.py` (GPU; same pools config, so the same τ, δ and checker revisions).
5. **Selection:** keep the selected candidate (the first sample passing every check). Pairs with no passing sample are **dropped**. Record the drop reason (failed checks of the first sample).

Rough cost: generation is about 2 GPU-minutes per 1,000 pairs; scoring is the slower step.

## 4. Quality gate (human spot-check)

MEANING, MOD, `assertion_to_question` and `assertion_to_directive` already passed the heldout human audit with the same planner, generator and checks, so they are not re-audited.

1. Build one blinded review containing only **40 selected `assertion_to_hedged` outputs** that have not previously been human-audited. Draw with `stable_key` and shuffle. The file is `docs/reports/current/mmi_full_spot_check.md`.
2. Materialize the provisional corpus immediately, withholding every `assertion_to_hedged` pair.
3. Score the review when completed (`Unsure` counts as valid). If valid ≥ 85%, include all automatically selected hedged pairs and regenerate the corpus and reports. If it is below 85%, keep all hedged pairs excluded without prompt or checker retuning.

## 5. Materialization

Materialization is staged around the hedged-only gate:
1. For each selected pair, write two rows: `{text: clean_simplification, axis: target_axis, score: 1}` and `{text: degraded, axis: target_axis, score: 0}`, plus `original`, the provenance and `operation`. **No labels for the other axes.**
2. **Split:** 90/10 train/validation by a stable hash of `canonical_original_id`; both rows of a pair go to the same split.
3. Keep `gemma_strategy_count`, `phase3a_predicted_codes` and `strict_single_strategy_candidate` so that a single-strategy-only filter can be applied later. Do not filter now.
4. Guard: the materializer raises on any row with `usage == "reserved_evaluation"` or an original in `excluded_audited_originals.txt`.
5. Output: `runs/mmi_en_v2_full/corpus/{train,validation}.jsonl` and `corpus_report.json`, with counts per axis × source × operation × split, drop rates by reason, and the SHA-256 of every input.

## 6. Deliverables

- `docs/reports/current/mmi_full_corpus_report.md`, a short report:
  - allocation counts;
  - generation yield and drop reasons per axis × source × operation;
  - the spot-check results and gate decision;
  - final corpus counts;
  - 3 examples per operation.
- Update `docs/README.md` (link the report) and `docs/methodology/illocution.md` ("Still open" → the hedged audit result).
- Tests for §2 and §5 (unittest, `phase6_degraded_corpus/tests/`).
- Local commit of code, configs, jobs, tests and docs only. **No push.**

## 7. Order and STOP points

1. Allocation + tests → allocation report.
2. Plan, shard, generate, score, select.
3. Build the 40-case hedged-only spot-check and materialize without hedged.
4. Score the hedged review when available; include hedged only if valid ≥ 85%, then regenerate reports.

## 8. Out of scope

- FLUENCY, OMIT, SYN and EXPL.
- Changes to prompts, planner or checks.
- Gemini and Llama.
- The known entity-swap follow-up (require the surrounding predicate to be in the Original).
- Non-English data.
