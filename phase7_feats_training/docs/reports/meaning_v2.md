# MEANING recipe v2 (graded meaning loss): results

**Experiment:** `meaning_v2` · **Date:** 1 October 2026 · Plan: [`meaning_recipe_v2_plan.md`](../plans/meaning_recipe_v2_plan.md) · Previous: [`axis_validation_v1.md`](axis_validation_v1.md)

## Decision

**Graded training data fixes most of v1's failure.** Arm A (graded, entailment-filtered):
- **beats the NLI checker** on Simplicity-DA (+0.093, CI [+0.047, +0.142]);
- **beats v1** on both human sets;
- raises system-level correlation from **0.02 to 0.97**.

**Q1 still fails formally:** on Human-Likert, A is close to NLI (Δ −0.032) but the CI [−0.123, +0.055] crosses the pre-registered −0.05 margin. With n = 277 the test can't establish non-inferiority there. Q2 and Q4 pass.

The NLI input head (B) adds nothing on top of the graded data, and on v1 data (C) it doesn't fix v1. **The data was the problem, not the architecture.** The entailment filter on base pairs makes little difference (A vs A_all).

## Results (Spearman with human meaning ratings; 95% CI by original-grouped bootstrap, 10,000 repetitions)

| Scorer | Simplicity-DA (n = 600) | Human-Likert (n = 277) | Simplicity-DA system-level r |
|---|---|---|---|
| **A: graded** | **0.743** | 0.598 | **0.97** |
| A_all: graded, no entailment filter | 0.738 | 0.591 | 0.98 |
| B: graded + NLI head | 0.726 | 0.594 | 0.95 |
| C: v1 data + NLI head | 0.660 | 0.507 | 0.11 |
| v1 model (Phase 7a) | 0.635 | 0.508 | 0.02 |
| NLI bidirectional entailment | 0.650 | 0.629 | 0.60 |
| LENS-SALSA | 0.569 | 0.624 | 0.88 |

**Arm A, paired differences:**

| Comparison | Simplicity-DA | Human-Likert |
|---|---|---|
| A − NLI | **+0.093** [+0.047, +0.142] ✅ beats | −0.032 [−0.123, +0.055] ⚠️ inconclusive |
| A − v1 | **+0.108** [+0.066, +0.152] ✅ | **+0.089** [+0.021, +0.160] ✅ |

| Criterion | A | A_all | B | C |
|---|---|---|---|---|
| Q1 (CI > 0 and non-inferior to NLI on both sets) | ❌ (Human-Likert CI) | ❌ | ❌ | ❌ |
| Q2 (beats NLI on ≥ 1 set) | ✅ | ✅ | ✅ | ❌ |
| Q4 (beats v1 on ≥ 1 set, worse on none) | ✅ | ✅ | ✅ | ✅ (barely) |

**Other results:**
- **Human-audited heldout degradations:** A ranks the clean simplification above the degradation in 99% of pairs.
- **SimpEval-2022 (overall quality, no criterion):** all models stay at about −0.2, against 0.37–0.43 for LENS and REFEREE. A meaning model rewards keeping content, while overall quality rewards good simplification, which often drops content. The axes differ by construction, so a meaning model shouldn't be used as an overall metric.
- **Synthetic validation:** no longer saturated (Spearman 0.86–0.88). The shortcut diagnostic passed: length explains 0.63 of the within-group comparisons, acceptability 0.51, NLI 0.76.

## What changed vs v1

- **Data:**
  - **Groups per pair:** Original copy (1.0), clean (1.0), `also`-trim (1.0), mild loss (0.67), major loss (0.33, whole-sentence drop) and contradiction (0).
  - **Base pairs:** the 4,514 v1 MEANING pairs whose clean simplification the Original entails; Vikidia excluded.
  - **Levels:** set by two blinded human reviews (the first set the mapping; the second, on unseen pairs, confirmed it).
- **Loss:** MSE + a within-group ranking loss.

## Deviations

- **DeBERTa-v3-base only** (24 runs = 4 arms × 2 learning rates × 3 seeds); XLM-R was not run, to save compute. DeBERTa won the v1 selection.
- **Graded levels built by rules only:** no LLM entity generalization; number generalization removed after the review.
- **v1 score on Human-Likert:** 0.508 here vs 0.502 in the v1 report. The rows are joined by evaluation id; the conclusions don't change.

## Recommendation

1. **Adopt recipe A (graded) as the MEANING training recipe.** It is the best scorer on Simplicity-DA (sentence and system level) and statistically indistinguishable from NLI on Human-Likert. Drop the NLI head (no gain) and the entailment filter question (no measurable effect; keep the filter because the labels are more correct).
2. **Q1 on Human-Likert is underpowered, not refuted.** Don't lower the margin after the fact. If a firmer claim is needed, use more meaning-rated data in a later round.
3. **Apply the same principle to the other axes before training them:** graded negatives, length controls, and a shortcut diagnostic gate. Their v1-style binary rule-based degradations would probably saturate the same way.

## Artifacts

- **Code:**
  - `phase6_degraded_corpus/src/generation/generate_meaning_graded.py`;
  - `phase6_degraded_corpus/src/reporting/build_meaning_graded_review.py`;
  - `phase7_feats_training/src/meaning_v2.py`;
  - jobs `train_meaning_v2_gpu.sh` and `evaluate_meaning_v2_gpu.sh`.
- **Data:**
  - `phase6_degraded_corpus/runs/meaning_graded_en_v1/`;
  - `phase7_feats_training/runs/meaning_v2/` (shortcut diagnostic, training runs, `evaluation/results.json`).
