# FEATS synthetic training data: status update


**Scope:** English. **Date:** 1 October 2026. **Audience:** the FEATS team. A short glossary is at the end.

Detailed reports: [MEANING v2](../../phase7_feats_training/docs/reports/meaning_v2.md), [FLUENCY v2](../../phase7_feats_training/docs/reports/fluency_v2.md), [axis validation v1](../../phase7_feats_training/docs/reports/axis_validation_v1.md), [MMI model comparison](../../phase6_degraded_corpus/docs/reports/current/mmi_v2_model_comparison.md).

## What we have

- **A clean English source corpus.** 36% of WikiAuto simplifications had two sentences glued together without a space (`actor.Haugen`). The data-consolidation step (Phase 2b) now repairs this. The strategy labels predicted by our classifiers (Phase 3a) were re-computed on the repaired text.
- **A protected evaluation set.** 419 sentences from the human-rated benchmarks (Simplicity-DA, Human-Likert, AssetAnn, SimpEval-2022 and the ASSET test set) are frozen and excluded from all training data. Exclusion matches the text itself, not IDs, so slightly different copies of the same sentence are excluded too.
- **A human-checked synthetic corpus for three FEATS axes:** MEANING (meaning preservation), MOD (modulation, i.e. how information is structured) and ILLOC (illocution, i.e. the speech act: statement, question, instruction). It contains 18,533 pairs of a good simplification and a deliberately degraded version. In blind human reviews, 88–95% of the degraded versions per axis are valid.
- **A validated MEANING scorer.** On one human benchmark it agrees with human meaning ratings better than the NLI baseline (see glossary). It also ranks simplification systems almost exactly as humans do (correlation 0.97).
- **A tested FLUENCY approach, with a negative result.** A scorer trained on 7,813 graded groups of synthetic grammar errors tracks human fluency ratings (Spearman 0.71) but does not beat the CoLA acceptability classifier (0.76), which stays our best fluency scorer.

## How we got here

1. **The first pilot failed.** A large language model (LLM: Qwen2.5-7B) was asked to degrade each axis. Only about 16% of a random sample was valid. The main failures were copies of the input, edits on the wrong axis, several edits at once, and poor source sentences.
2. **We repaired the data:** fixed the glued sentences, froze the evaluation sentences, and added quality gates on the input pairs (grammatical acceptability, and no contradiction with the original according to NLI).
3. **We rebuilt the generation.** The model now edits only one marked span, or the change is applied by a fixed rule (numbers, dates, negation). Its output is forced to a fixed format, four candidates are sampled, and strict automatic checks select one. A blind comparison chose Qwen2.5-7B for MEANING and ILLOC and Gemma-3-12B for MOD.
4. **We validated against humans before scaling up.** We first trained a scorer on the synthetic data and tested it against human ratings, with success criteria fixed in advance. The first MEANING scorer did no better than the NLI tool that had selected its own training data.
5. **We introduced graded degradations.** Replacing "good vs. bad" labels with severity levels fixed MEANING. We then applied the same recipe to FLUENCY.

## Changes we propose to the method

- **One scorer per axis**, as recommended in the E2R paper (TACL). Each scorer sees a given pair only once, so the same pair can be reused to train different axes.
- **Graded instead of binary negatives.** Each source pair produces several versions with target scores between 1 and 0. Binary data that only contains contradictions is too easy: the scorer learns little beyond what the filter that built it already knew.
- **Automatic quality tools are baselines, not labelers.** NLI (for MEANING) and CoLA acceptability (for FLUENCY) are what our scorers must beat, so they must not decide which negative examples we keep.
- **Strategy labels only where they matter.** We require a single detected simplification strategy only for OMIT (omission), SYN (synonymy) and EXPL (explanation), because there the degradation undoes that strategy. For MOD we select pairs where the simplification split a long sentence.
- **ILLOC by injection.** Real changes of speech act are almost absent from the data (16 of 73,586 pairs), so we inject them: a statement becomes a question, an instruction or a hedged claim. We count hedging ("might", "probably") as ILLOC, not MEANING.
- **Wikipedia-Vikidia is excluded** from new synthetic data, because its original and simplified sentences are only loosely aligned.

## Key experiment: MEANING, binary vs graded

Spearman correlation (rank agreement, from −1 to 1) between each scorer and human meaning ratings:

| Scorer | Simplicity-DA (600 outputs) | Human-Likert (277 outputs) | System level (Simplicity-DA) |
|---|---|---|---|
| **Graded MEANING scorer (v2)** | **0.743** | 0.598 | **0.97** |
| Binary MEANING scorer (v1) | 0.635 | 0.508 | 0.02 |
| NLI entailment (baseline) | 0.650 | 0.629 | 0.60 |
| LENS-SALSA (published metric) | 0.569 | 0.624 | 0.88 |

The graded scorer beats NLI on Simplicity-DA (+0.09; the 95% confidence interval excludes zero) and beats the binary scorer on both benchmarks. On Human-Likert it is statistically tied with NLI. With only 277 items the uncertainty is too large to prove it is "not worse", so that pre-set criterion remains open.

Giving the scorer the NLI probabilities as extra input added nothing. The problem was the training data, not the model.

## The graded recipe

Each good simplification becomes a group of versions of the same sentence, each with a target score:

| Score | Versions |
|---|---|
| 1.0 | the good simplification; the original sentence itself; a harmless trim (e.g. removing "also") |
| 0.67 | a mild meaning loss, or one minor grammar error |
| 0.33 | a major meaning loss, or one serious grammar error |
| 0.0 | a contradiction, or several grammar errors |

- **How versions are built:** by rules.
- **How levels are checked:** two blind human reviews confirm that each rule lands at the intended level. The first sets the mapping; the second, on unseen sentences, confirms it.
- **Length control:** versions that are longer but still perfect (the original sentence) stop the scorer from learning "shorter means worse".
- **Shortcut check:** before training, we verify that no trivial signal such as length explains the scores.

## Which axes can be validated against human judgments

| Axis | Human ratings available | Can we validate a scorer? |
|---|---|---|
| MEANING | Simplicity-DA, Human-Likert | Yes |
| FLUENCY | Simplicity-DA, Human-Likert (fluency ratings) | Yes |
| MOD | None (AssetAnn only marks split/move operations) | Needs a small annotation |
| OMIT, SYN, EXPL | None (AssetAnn operation labels only) | Needs a small annotation |
| ILLOC | None; real system outputs almost never change the speech act | Not with natural data |

SimpEval-2022 rates overall quality only. We report it as context, but it does not validate any single axis.

## Status by axis

| Axis | Status | Notes |
|---|---|---|
| MEANING | Validated | Graded recipe adopted. Beats NLI on Simplicity-DA; tied on Human-Likert. |
| FLUENCY | Use CoLA for now | The trained scorer reaches 0.71 (Simplicity-DA) and 0.57 (Human-Likert), but CoLA reaches 0.76 and 0.69, significantly better on both. Graded data gave no gain over binary here, because our four rule-based error types are too narrow compared with real system errors. |
| MOD | Corpus only | The scorer learned a shortcut: sentence count alone explains 100% of the human-checked pairs. |
| ILLOC | Corpus only | Same problem: "has a question mark or is longer" explains 100% of the human-checked pairs. |
| SYN, OMIT, EXPL | Rules need fixes | Blind review: 81%, 78% and 50% valid, against an 85% target. The EXPL rule was removing added facts rather than explanations. |

## Next steps

- **FLUENCY:** use CoLA as the fluency scorer for now. To improve on it, fine-tune CoLA itself on our graded data and add wider error types (repetitions, truncations, awkward wording).
- **SYN, OMIT, EXPL:** tighten the rules, re-review them on unseen sentences, then build graded groups. The rule changes are: restore one word only; restored text must carry content; remove only explanatory insertions such as definitions, glosses and "known as".
- **MOD and ILLOC:** add examples that break the shortcuts: MOD degradations that keep the same number of sentences, and ILLOC degradations without a question mark that are not longer.
- **Decision for the team:** annotate a small human test set (about 100–150 items per axis) for MOD and for OMIT, SYN and EXPL. Without it, these scorers cannot be shown to measure their axis.
- **Later:** fine-tuning on human data, and the same pipeline for French and other languages.

**Lesson so far:** synthetic degradations help only when negatives are graded, cover the kinds of errors humans actually judge, and the scorer is tested on human ratings it never saw. For MEANING this beat the existing tool; for FLUENCY the existing tool (CoLA) is still better.

## Glossary

| Term | Meaning |
|---|---|
| **FEATS axes** | MEANING (meaning preservation), FLUENCY (grammaticality), MOD (modulation: information structure), ILLOC (illocution: speech act), OMIT (omission), SYN (synonymy), EXPL (explanation). |
| **NLI** | Natural Language Inference: a model that decides whether one sentence *entails*, *contradicts* or is *neutral* to another. We use a DeBERTa-v3-large NLI model as a meaning checker and baseline. |
| **CoLA** | Corpus of Linguistic Acceptability. We use a RoBERTa-large classifier trained on it to score how grammatical a sentence is (our fluency checker and baseline). |
| **LLM** | Large language model (here Qwen2.5-7B-Instruct and Gemma-3-12B-it). |
| **Spearman correlation** | Agreement between two rankings, from −1 to 1. 1 means the scorer orders outputs exactly as humans do. |
| **System-level correlation** | Correlation computed on each system's average score, i.e. does the scorer rank simplification *systems* as humans do. |
| **95% confidence interval** | Range of plausible values for a result. If it excludes zero, the difference is unlikely to be chance. |
| **Simplicity-DA, Human-Likert** | Public datasets of system simplifications rated by humans for meaning, fluency and simplicity. |
| **SimpEval-2022** | Public dataset of simplifications rated for overall quality. |
| **ASSET / AssetAnn** | ASSET: a benchmark of human simplifications. AssetAnn: ASSET annotated with the editing operations used (split, move, synonym…). |
| **WikiAuto, Wikipedia-Vikidia** | Parallel corpora of Wikipedia sentences and their simplified versions (Simple Wikipedia; Vikidia, a children's encyclopedia). |
| **LENS-SALSA, REFEREE** | Published learned metrics for simplification quality, used here as external baselines. |
| **Blind review** | Human review where the reviewer does not know which system or level produced each case. |
| **Shortcut** | A trivial signal (length, sentence count, a question mark) that predicts the label without understanding the axis. |
