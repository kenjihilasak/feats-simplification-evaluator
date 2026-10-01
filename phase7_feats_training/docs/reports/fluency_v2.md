# FLUENCY recipe v2 (graded): results

**Experiment:** `fluency_v2` · **Date:** 1 October 2026 · Plan: FOSE plan §9 (`phase6_degraded_corpus/docs/plans/fluency_omit_syn_expl_plan.md`) · Comparison: [`meaning_v2.md`](meaning_v2.md)

## Decision

**Negative result.** A DeBERTa-v3-base scorer trained on graded synthetic fluency errors correlates well with human fluency ratings (Spearman 0.71 on Simplicity-DA, 0.57 on Human-Likert). It is **significantly worse than the CoLA acceptability classifier** on both sets, so Q1 and Q2 fail. Unlike MEANING, graded data gives **no significant gain** over binary data here.

**Recommendation:** for FLUENCY, use the CoLA acceptability model as the scorer for now, or as the starting point of any trained model. Do not train on the current rule-based errors alone.

## Data and setup

- **Groups:** 7,813 (WikiAutoEN + ASSET; Vikidia excluded).
- **Levels:**
  - 1.0: clean, Original copy, `also`-trim;
  - 0.67: one minor error (dropped article, swapped preposition);
  - 0.33: one serious error (agreement, word order) or two minor;
  - 0.0: three or more errors.
- **Level validation:** blind human review of 60 cases, 87–100% agreement per level.
- **Negatives:** not selected with CoLA (the baseline). Only meaning-preservation was checked (NLI).
- **Shortcut diagnostic:** length 0.65 (no shortcut). Acceptability explains 0.92 of within-group order, which is expected for this axis.
- **Arms:** graded (A) and binary (clean vs one single-error variant, the FOSE v1 design). DeBERTa-v3-base, 2 learning rates × 3 seeds, selection on synthetic validation only.
- **Synthetic validation Spearman:** 0.935 (graded). It is not saturated.
- **Evaluation:** test sets read once; 10,000-repetition bootstrap grouped by original.

## Results (Spearman with human fluency ratings, 95% CI)

| Scorer | Simplicity-DA (n = 600) | Human-Likert (n = 277) | Simplicity-DA system-level r |
|---|---|---|---|
| **CoLA acceptability** | **0.758** [0.719, 0.792] | **0.693** [0.625, 0.748] | **0.97** |
| FLUENCY scorer, graded (A) | 0.710 [0.668, 0.747] | 0.565 [0.489, 0.631] | 0.95 |
| FLUENCY scorer, binary | 0.695 [0.651, 0.733] | 0.556 [0.466, 0.635] | 0.96 |
| LENS-SALSA | 0.688 | 0.681 | 0.88 |
| REFEREE | 0.557 | 0.482 | 0.94 |
| NLI entailment | 0.323 | 0.319 | 0.27 |

| Paired difference | Simplicity-DA | Human-Likert |
|---|---|---|
| A − CoLA | −0.048 [−0.090, −0.006] | −0.127 [−0.205, −0.053] |
| A − binary | +0.015 [−0.010, +0.042] | +0.010 [−0.038, +0.057] |

**Other results:**
- Heldout (40 FLUENCY cases judged valid in the FOSE v1 review): both arms rank clean above degraded in 100% of pairs.
- SimpEval-2022 (overall quality, context only): −0.31.

## Why it fails where MEANING succeeded

1. **CoLA is a much stronger baseline than NLI was.** It is trained on real human acceptability judgments, and acceptability is very close to the construct of fluency. On meaning, NLI reached 0.65 and graded data overtook it. On fluency, CoLA already reaches 0.76.
2. **Our errors are narrow.** The four rule types (agreement, dropped article, preposition swap, adjacent word swap) do not cover the disfluencies of real system outputs: repetitions, garbled or truncated phrases, unnatural word choice, broken coordination. The scorer learns our four errors well (100% on the heldout) but generalizes less well than CoLA.
3. **Grading cannot add what the errors lack.** For MEANING, grading added a new *kind* of negative (partial loss). Here it only adds *more of the same* errors, so it cannot fix the coverage gap.

## Possible next steps (not run)

- **Start from CoLA:** fine-tune the CoLA classifier itself on the graded data, testing whether the data adds anything on top of a strong prior.
- **Wider error types:** model-generated disfluencies (repetition, truncation, LLM-paraphrased awkward wording), or errors sampled from real system outputs outside the evaluation sets.
- Same evaluation protocol, with CoLA as the baseline to beat.
