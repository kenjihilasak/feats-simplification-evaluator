# Plan: Phase 3a re-run on text-repaired pairs

Execution plan. Prerequisite: `phase2b_consolidation/runs/2026-09-29_base_textrepair_v1/` exists and has passed `validate_text_repair.py`. See [`phase2b_consolidation/docs/text_repair_plan.md`](../../phase2b_consolidation/docs/text_repair_plan.md).

## 1. Why

Run `2026-08-20_three_models_phase2b_full_v1` predicted strategies on raw Phase 2b text, and about 29k rows in `target_simple` contained glued sentences or PTB brackets. Sentence-boundary errors mainly bias `MOD` (split sentences look like one) and `COMP`. The IDs did not change, so only the **repaired rows** need new predictions.

## 2. Constraints

- Do not modify or delete the existing run `2026-08-20_three_models_phase2b_full_v1` or the candidate sets `2026-08-26_*` and `2026-08-31_*`.
- Same four models, same pinned revisions, thresholds and prompts (`configs/models/*.json`). Record library versions. If any version differs from the v1 run, the control check in §3.2 decides whether the delta approach is still valid.
- Input text: the repaired `original`/`simple` fields of the base text-repair variant. Never the `*_raw` fields.

## 3. Steps

### 3.1 Delta run

1. New experiment config `configs/experiments/four_models_textrepair_delta_v1.json` with:
   - `input_root: phase2b_consolidation/runs/2026-09-29_base_textrepair_v1/data`;
   - a selection that keeps only rows with `text_repaired == true` (add this filter to the input selection if it does not exist; test it).
2. Run all four models (existing sharded GPU jobs for Qwen/Gemma, encoder job for XLM-R/E5) → `runs/2026-09-30_four_models_textrepair_delta_v1/`. Validate with `validate_run.py`: the expected count equals the number of repaired rows in the base variant.

### 3.2 Control check (reproducibility)

Re-run the four models on a deterministic sample of **1,000 unrepaired rows** (stratified by language). Compare with v1 predictions:
- exact agreement of predicted label sets;
- maximum absolute probability difference.

Required: label-set agreement ≥ 99.5% per model. If this fails, the environment drifted: **STOP** and report, because merging a delta with v1 would mix two inference setups.

### 3.3 Effective predictions

Build `runs/2026-09-30_four_models_textrepair_effective_v1/`: for each model and language, take the v1 prediction for unrepaired rows and the delta prediction for repaired rows. The keys are `canonical_pair_id`, and the file layout is the same as v1.
- Every row gets `prediction_source: "v1" | "textrepair_delta"`.
- Validation: exactly 854,486 rows per model, the same ID set as v1, no duplicates.

### 3.4 Candidate set

Rebuild the gemma-anchored strict set from the effective predictions with the **unchanged** rule (`build_gemma_anchored_gold_candidates.py`, parametrised for the input run) → `gold_candidates/2026-09-30_single_strategy_gemma_anchored_strict_textrepair_v1/`. Validate with `validate_single_strategy_gold_candidates.py`.

### 3.5 Change report

Write `runs/2026-09-30_four_models_textrepair_delta_v1/reports/label_change_report.md` with:
- per model: the share of repaired rows whose label set changed, and the transition matrix (v1 label set → new), by language and corpus;
- candidate set: rows that entered, left, or changed their single strategy; for English, the counts per strategy before and after (especially `MOD`, `COMP`, `EXPL`);
- 20 examples of changed English candidates, with the repaired text.

## 4. Deliverables and handoff

- The delta run, the effective run and the candidate set, each validated.
- The change report.
- Update the status table in [`phase6_degraded_corpus/docs/inputs.md`](../../phase6_degraded_corpus/docs/inputs.md) §3, and add a short section in `phase3a_strategy_detection/README.md` and `gold_candidates/README.md` that names the new active candidate set.
- Commit code, configs, tests and docs only. Do not push. Do not include unrelated pre-existing changes in the working tree.
