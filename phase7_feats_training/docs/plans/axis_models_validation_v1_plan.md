# Plan: Phase 7a — do models trained on the synthetic corpus agree with humans?

Execution plan. Experiment id: **`axis_validation_v1`**. English only.

## 0. Why this phase exists

Phase 6 produced a synthetic corpus for MEANING, MOD and ILLOC: 18,538 pairs, each giving a clean simplification (score 1) and one degradation (score 0). Every check so far verified that the **degradations are correct**. None verified that **a model trained on them scores real simplifications the way humans do**. That is the only test of whether the weak-supervision approach works, and it decides whether the remaining axes (FLUENCY, OMIT, SYN, EXPL) are worth building the same way.

This is the first experiment of `phase7_feats_training/`, as foreseen in [`internal_docs/FEATS_AXIS_MODELS_PLAN.md`](../../../internal_docs/FEATS_AXIS_MODELS_PLAN.md): one model per axis, split by original, evaluated on held-out human judgments. It is a **validation** experiment, not the final FEATS model.

## 1. Questions and pre-registered success criteria

Fix these before looking at any test result.

| # | Question | Pass criterion |
|---|---|---|
| Q1 | Does the **MEANING** model track human meaning-preservation ratings? | Segment-level Spearman with human meaning ratings is **> 0** with a 95% grouped-bootstrap CI excluding 0, **and** **non-inferior** to the strongest simple baseline (§5), on both Simplicity-DA and Human-Likert: the lower bound of the 95% paired-bootstrap CI of (model − baseline) Spearman must be **> −0.05** (pre-registered margin). |
| Q2 | Does it add anything over the tool used to build its data? | MEANING model vs the NLI baseline (the same checker used to select degradations): the difference in Spearman is reported with a paired bootstrap CI. **Beating** NLI is the strong result; matching it is the weak result. |
| Q3 | Do MOD and ILLOC models learn their axis rather than a shortcut? | On the human-audited heldout degradations (§4.3), pairwise accuracy (clean > degraded) is ≥ 0.85, **and** it is ≥ 10 points above the best shortcut baseline (length ratio, acceptability). |

**Reading the outcome:**
- Q1 and Q2 positive → build the remaining axes with the same method (the FOSE plan).
- Q1 negative → **STOP** and report before any more corpus work.
- MOD and ILLOC have **no human rating data** for their construct (see §4). Q3 is the only evidence possible now; say so explicitly in the report.

## 1b. Amendments after the first leakage STOP (2026-09-30)

1. **Leakage fixed upstream.** The Phase 6 exclusion of audited originals was id-based, so 5 training originals matched heldout items by text. Phase 6 now expands the exclusions by strong key + Jaccard ≥ 0.8 (`phase6_degraded_corpus/src/selection/expand_audited_exclusions.py`, report `runs/mmi_en_v2_full/allocation/audited_text_match_report.json`). The corpus was rematerialized: **18,533 pairs**. The unchanged gate now passes (0 exact, 0 near). The previous corpus is kept in `corpus_pre_text_exclusion/`.
2. **Conflicting review H026** (MEANING v2.1, both Valid and Invalid ticked) is **excluded** from every human-labelled evaluation, and the report says so. No label is guessed.
3. **Checkpoints must be staged before any offline job:** `microsoft/deberta-v3-base` (project cache `cache/huggingface/`), the NLI and CoLA checkers (`cache/huggingface/hub/`, revisions in `phase6_degraded_corpus/configs/experiments/mmi_en_v2_pools.json`) and `xlm-roberta-large`. Resolve each to a pinned snapshot path in `configs/models/*.json`. The job fails if a snapshot is missing.
4. **LENS-SALSA / REFEREE adapter:** both are used **reference-free**, exactly as in Phase 5. Map each evaluation item to the Phase 5 input schema with `original` → source and the rated output → simplification, and no references, even where the evaluation set provides them. Pinned revisions as in Phase 5. Freeze this adapter, with a unit test on 3 items per set, **before** any training.

## 2. Hard constraints

1. **No leakage:** before training, verify that no training or validation original matches any evaluation original (strong key + near duplicates, Jaccard ≥ 0.8, as in Phase 6 `inputs.md`). Write `leakage_check.json`; fail on any hit.
2. The test sets are used **once**, at the end. All model and hyperparameter choices are made on the synthetic validation split only.
3. Never modify Phase 6 outputs. Read `runs/mmi_en_v2_full/corpus/{train,validation}.jsonl` (per-axis files if the FOSE plan has already created `by_axis/`).
4. Reproducibility: pinned model revisions, 3 seeds per configuration, configs and the data manifest (SHA-256 of every input) saved with every run.
5. Outputs under `phase7_feats_training/runs/axis_validation_v1/` (Git-ignored). Code, configs, tests and docs are committed. Stop at every **STOP**.

## 3. Models

One model per axis: MEANING, MOD, ILLOC.

- **Input:** `original </s> simplification` (no audience field yet).
- **Architecture:** cross-encoder with a scalar head.

| Backbone | Why |
|---|---|
| `xlm-roberta-large` (cached in `~/.cache/huggingface`) | Multilingual, as the internal plan recommends for future languages. |
| `microsoft/deberta-v3-base` (cached) | Strong, cheap English encoder; a second point of comparison. |

**Training:**
- Loss = BCE on the 0/1 label + a **pairwise margin ranking loss** between the clean and the degraded text of the same pair (margin 0.5, weight 1.0). The pairwise term ties the model to the controlled contrast, not to absolute features.
- Batches keep both rows of a pair together.
- AdamW, learning rate {1e-5, 2e-5}, 3 epochs, early stopping on validation pairwise accuracy.
- 3 seeds per configuration.
- **Selection:** pick the best configuration per axis on synthetic validation pairwise accuracy. Report every configuration.

## 4. Evaluation data

The frozen sources are under `phase6_degraded_corpus/runs/mmi_en_v2/pools/evaluation_sources/`; their commits are recorded in the manifest.

| Set | What humans rated | Used for | Aggregation |
|---|---|---|---|
| **Simplicity-DA** (600 outputs, 302 originals) | meaning, fluency, simplicity (z-scores) | **MEANING** (meaning z-score) | One score per output. |
| **Human-Likert (QuestEval)** (6,210 ratings per aspect) | meaning, fluency, simplicity (Likert) | **MEANING** (meaning) | Mean rating per (sentence_id, system). |
| **SimpEval-2022** (360 outputs) | overall quality | Secondary only | Report correlations **without** a pass criterion: overall ≠ any single axis. |
| **Human-audited heldout degradations** (Phase 6: `mmi_v2_heldout_review.md`, `mmi_v21_meaning_heldout_review.md`, with their keys) | Valid / Invalid for one axis | **Q3** and a human-verified check for MEANING | Only human-Valid (or Unsure) degradations; for each, is score(clean) > score(degraded)? |
| **AssetAnn** | operation labels (synonym, split, move, deletions, insertions) | Not in this plan | Reserved for the SYN / OMIT / EXPL / MOD analyses of a later experiment. |

The heldout pairs were excluded from the Phase 6 training corpus, so they are original-disjoint from training. Still check them in the leakage test.

## 5. Baselines (all scored on the same items)

| Baseline | For |
|---|---|
| NLI bidirectional entailment (mean of P(entail) in both directions), same DeBERTa-NLI checker as Phase 6 | MEANING (the key comparison, Q2) |
| LENS-SALSA and REFEREE, from Phase 5 code (`phase5_external_metrics/src/`); score the evaluation items with the pinned revisions | All; they are overall metrics, so they are context only for axis models |
| Length ratio (simplified / original), in both directions | Shortcut check, all axes |
| CoLA acceptability of the simplification | Shortcut check, all axes |
| Untrained backbone with a random head | Sanity floor |

## 6. Metrics and statistics

- **Human rating sets:**
  - segment-level Spearman and Kendall τ;
  - for Simplicity-DA, also system-level Pearson (mean per system);
  - 95% CIs from a bootstrap resampling **originals** (10,000 reps);
  - model vs baseline: a paired bootstrap of the difference.
- **Pairwise sets (synthetic validation, heldout degradations):**
  - accuracy of score(clean) > score(degraded);
  - broken down by source (WikiAutoEN / ASSET / Vikidia) and by operation (MEANING type, ILLOC operation).
- Mean ± std over the 3 seeds for everything; the headline uses the seed-averaged prediction.

## 7. Additional diagnostics (reported, not gates)

1. **Shortcut probes on the synthetic validation split:** pairwise accuracy of the length and acceptability baselines per axis and operation. MOD degradations always have one sentence fewer; flag any baseline ≥ 0.9.
2. **Invariance tests** (small, built automatically from 200 clean validation pairs): meaning-preserving edits that should **not** lower the score:
   - adding "also";
   - contracting "is not" → "isn't";
   - swapping the order of two coordinated adjectives.

   Report the mean score change per axis model.
3. **Error analysis:** the 20 items with the largest disagreement with human ratings for MEANING, with the text, in the report.

## 8. Deliverables

- `phase7_feats_training/` skeleton, following the internal plan:
  - `README.md`;
  - `configs/{models,axes,experiments}/`;
  - `src/{contracts,build_axis_dataset,train_axis_model,predict_axis,evaluate}.py`;
  - `tests/`, `jobs/`.
- The dataset contract from the internal plan (one row per example × axis, `label_source: synthetic | human`).
- Evaluation loaders for Simplicity-DA, Human-Likert, SimpEval-2022 and the heldout reviews, with unit tests for aggregation and key joining.
- The leakage check.
- Report `phase7_feats_training/docs/reports/axis_validation_v1.md`:
  - the answers to Q1–Q3 against the pre-registered criteria;
  - all tables;
  - the diagnostics;
  - a one-paragraph recommendation (continue the FOSE axes as planned / change the method).
- Local commit. **No push.**

## 9. Order and STOP points

1. Skeleton, dataset builder, evaluation loaders, leakage check, tests.
2. Baselines on all evaluation sets. The baselines are fixed before any model is trained.
3. Train MEANING (2 backbones × 2 learning rates × 3 seeds); choose on synthetic validation.
4. Evaluate MEANING on the test sets. If Q1 fails: **STOP**, write the report, recommend.
5. Train and evaluate MOD and ILLOC, then the diagnostics, report and commit.

## 10. Out of scope

- FLUENCY, OMIT, SYN and EXPL models (their corpus is not built yet).
- Human-rating fine-tuning and the REFEREE-style curriculum (a later experiment, once Q1 passes).
- Multi-task models.
- Calibration to FEATS scales.
- Non-English data.

**Open item for the team, not blocking:** Nouran's existing per-axis models, splits and scales (internal plan, "Information required from Nouran"). If they become available, add them as a baseline column.
