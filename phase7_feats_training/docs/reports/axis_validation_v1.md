# Axis validation v1: MEANING result

**Experiment:** `axis_validation_v1` · **Date:** 30 September 2026
**Status:** **STOP after Q1 (plan §9.4).** Q1 fails its pre-registered criterion. MOD and ILLOC were not trained.

## Decision

The MEANING model trained on the Phase 6 synthetic corpus **tracks human meaning ratings well** (Spearman 0.64 on Simplicity-DA, 0.50 on Human-Likert). It **does not improve on**, and on Human-Likert is significantly **worse than**, the NLI checker that was used to build its own training data. Q1 therefore fails (non-inferiority margin −0.05), and Q2 is negative. The synthetic corpus, as built, teaches the model roughly *what the NLI checker already knows*.

## Setup (as pre-registered, with the §1b amendments)

- **Training data:** 18,533 MMI pairs after the text-based exclusion of audited originals. The leakage gate passed: 0 exact and 0 near-duplicate matches with the 664 evaluation originals.
- **Grid:** 2 backbones × 2 learning rates × 3 seeds, with BCE + margin-ranking loss.
- **Selection:** on synthetic validation only. Chosen configuration: `deberta_v3_base / lr 2e-5`, mean validation pairwise accuracy 0.9995.
- **Evaluation:** test sets read once; predictions averaged over the 3 seeds. Spearman with 95% bootstrap CIs grouped by original (10,000 repetitions); paired bootstrap for differences.
- **Deviations from the plan:**
  - DeBERTa was trained without gradient checkpointing (a reentrant-checkpoint crash);
  - bf16 was used instead of fp16;
  - the conflicting review H026 was excluded.

## Q1 and Q2: MEANING vs human meaning ratings

| Scorer | Simplicity-DA ρ [95% CI] (n = 600) | Human-Likert ρ [95% CI] (n = 277) |
|---|---|---|
| **MEANING model** | **0.635** [0.586, 0.680] | **0.502** [0.411, 0.580] |
| NLI bidirectional entailment | 0.650 [0.601, 0.696] | 0.629 [0.543, 0.704] |
| LENS-SALSA (reference-free) | 0.569 [0.506, 0.629] | 0.624 [0.528, 0.702] |
| CoLA acceptability | 0.540 [0.480, 0.593] | 0.541 [0.444, 0.629] |
| REFEREE | 0.421 [0.344, 0.493] | 0.407 [0.285, 0.525] |
| Length ratio | 0.359 [0.284, 0.427] | 0.266 [0.154, 0.380] |

| Criterion | Simplicity-DA | Human-Likert |
|---|---|---|
| Model ρ CI excludes 0 | ✅ | ✅ |
| Non-inferior to the strongest baseline (NLI): lower CI bound of Δρ > −0.05 | ❌ Δ = −0.015 [−0.071, +0.043] | ❌ Δ = −0.127 [−0.229, −0.029] |
| **Q1** | **fail** (narrowly) | **fail** |
| Q2: model − NLI | tie | NLI significantly better |

**Context (not a criterion):**
- **Simplicity-DA, system level:** the model's Pearson is only **0.02**, against 0.60 for NLI and 0.88–0.89 for LENS-SALSA and REFEREE. The model ranks sentences reasonably but does not separate systems.
- **SimpEval-2022 (overall quality):** the model's ρ is −0.21, against 0.43 for REFEREE. This is expected to differ (overall ≠ meaning), but the negative sign is a warning.

## Human-audited heldout degradations (MEANING)

The model ranks the clean simplification above the human-validated degradation in **103/103 pairs (100%)**, against 97% for NLI, 68% for acceptability and 7% for the length ratio. It detects the controlled contradictions perfectly, which is exactly what it was trained on.

## Why it fails: diagnosis

1. **The training task is saturated.** Synthetic validation pairwise accuracy is 99.6–100% for every configuration, so model selection had no signal.
2. **The training contrasts are the NLI's own decisions.** Every MEANING degradation was *selected* by the NLI checker (contradiction ≥ 0.5). The model learns "contradiction vs no contradiction", a subset of what NLI measures. Human meaning ratings also reflect **graded** loss: omitted content, vaguer paraphrases, partial distortions. These never appear as negatives in the corpus.
3. **Only one kind of positive.** All positives are fluent reference simplifications. The model never sees mediocre system outputs, which dominate Simplicity-DA and Human-Likert; this probably explains the near-zero system-level correlation.

## Recommendation

Do **not** scale the same recipe to more axes before changing it. For MEANING, in order of expected value:

1. **Graded negatives:** add meaning-*loss* degradations (deletion of a content clause, generalisation "Warsaw" → "a city", vaguer paraphrases) with intermediate target scores, not only contradictions.
2. **Harder synthetic validation:** it must not saturate. Use graded negatives and pairs with small edits, so that model selection has signal.
3. **Use NLI instead of competing with it:** NLI is already a strong meaning baseline. Train a model whose input includes NLI features, or train on NLI-*uncertain* pairs.
4. **REFEREE-style curriculum** (internal plan): after synthetic pre-training, fine-tune on a small amount of human meaning data. Keep an original-disjoint human test set; Simplicity-DA vs Human-Likert cross-evaluation is possible.

**Implication for FOSE (FLUENCY/OMIT/SYN/EXPL):** building their pools and the human review can continue. **Do not train FOSE models** until the recipe is revised; the same saturation will probably appear there (the FOSE rules even guarantee a length or acceptability signal).

**MOD/ILLOC:** not trained, per the STOP. Their Q3 remains open.

## Artifacts

- **Code:** `src/run_evaluation.py` (selection, prediction, Q1–Q3); training fixes in `src/train_axis_model.py` and `jobs/train_axis_validation_v1_gpu.sh`.
- **Results:** `runs/axis_validation_v1/evaluation/MEANING/results.json` and the scored items per set (Git-ignored).


## Addendum (2026-10-01): MOD and ILLOC (Q3)

Trained afterwards on the same corpus (DeBERTa-v3-base only, 2 learning rates × 3 seeds). Synthetic validation pairwise accuracy is **100%** for every run on both axes: saturated, as MEANING v1 was.

| Axis | Model on human-audited pairs | Best single shortcut | Pre-registered Q3 | Reading |
|---|---|---|---|---|
| MOD (n = 88) | 100% | **sentence count: 100%** (99.5% on synthetic) | ❌ fail (margin 0) | Indistinguishable from "more sentences = better". |
| ILLOC (n = 54, question + directive) | 100% | inverse length: 80% (`?` alone 33%) | ✅ pass | **Hollow:** the combined trivial rule "degraded ends with `?` or is longer" also scores **54/54 (100%)**. |

Context only (construct mismatch): MOD vs human meaning ratings ρ = −0.19 (Simplicity-DA); ILLOC ρ = 0.54 (Simplicity-DA). The ILLOC model largely acts as a generic "unchanged sentence" detector.

**Conclusion:** neither axis shows evidence that the model learned the construct rather than a surface cue. Binary injection data cannot separate the two, and there is no human-rated data for these axes. **Next:**
1. Build controls that break the cues: MOD negatives with the *same* sentence count (clauses reordered so the information order is worse, or misattached), and positives with fewer sentences; ILLOC negatives without `?` and not longer (e.g. a question rewritten as a statement-shaped request), and positives that are longer (neutral additions).
2. Build a small human-rated MOD test set (annotation spec pending). ILLOC stays unverifiable with natural data.
