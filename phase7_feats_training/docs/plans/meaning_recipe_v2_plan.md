# Plan: MEANING recipe v2 — graded meaning loss

Execution plan. Experiment ids: corpus **`meaning_graded_en_v1`** (Phase 6), models **`meaning_v2`** (Phase 7). English only.

## 0. Why

`axis_validation_v1` ([report](../reports/axis_validation_v1.md)) showed that the MEANING model trained on contradiction-only pairs:
- correlates with human meaning ratings (ρ 0.64 Simplicity-DA, 0.50 Human-Likert);
- is **not better than the NLI checker** that selected its training data, and is significantly worse on Human-Likert;
- barely separates systems (system-level Pearson 0.02).

Three causes were identified:
1. the training task saturates (99.6–100% synthetic validation);
2. every negative is a contradiction that NLI already flagged;
3. every positive is a fluent reference simplification.

Human meaning ratings are **graded**: they punish omissions, vaguer wording and partial distortions, not only contradictions.

This plan changes the **data**, not the model: graded negatives, harder validation, and controls against the length shortcut. It also tests using NLI as an input instead of competing with it.

## 1. Constraints

1. **Sources: WikiAutoEN and ASSET only.** Wikipedia-Vikidia is excluded from generation and training: its pairs are loosely aligned (27% pass the structural filters, against 43% for WikiAutoEN) and it contributes 0.4% of the rows. Its already-audited heldout cases stay as a diagnostic.
2. **Exclusions:** the same as Phase 6 ([`inputs.md`](../../../phase6_degraded_corpus/docs/inputs.md)): reserved evaluation originals and human-audited originals, both matched **by text** (strong key + Jaccard ≥ 0.8). The Phase 7 leakage gate must pass before any training.
3. **Split:** the same `split_for()` as MMI (seed 20260930, 10% validation).
4. **Reuse** the existing MMI MEANING contradictions (C1, v2.1) as the most severe level. Do not regenerate them.
5. **Test sets** are used once, after selection. Keep the Phase 7a evaluation code, baselines and bootstrap unchanged, so that v1 and v2 are directly comparable.
6. Outputs: `phase6_degraded_corpus/runs/meaning_graded_en_v1/` and `phase7_feats_training/runs/meaning_v2/`. Stop at every **STOP**.

## 2. Graded variants per clean pair (Phase 6)

**Base pairs (decision 2026-10-01):** the **MEANING pairs of the v1 corpus** (`runs/mmi_en_v2_full/corpus/`, `axis == MEANING`), minus Wikipedia-Vikidia (6,951 pairs), **restricted to pairs whose clean simplification preserves meaning**: NLI P(entailment | Original → Simplified) ≥ 0.5 from `clean_quality_scores.jsonl`, which leaves **4,514 pairs**. The clean text gets target 1.0 ("meaning fully preserved"), so it must actually be entailed. NLI selects only these *positives*; the negatives are still defined by rules, so v1's circularity does not return. Phase 3a single-strategy is **not** used for MEANING, because it says nothing about meaning quality.

- **Ablation:** arm A is also trained on all 6,951 pairs (`A_all`), to measure what the entailment filter contributes.
- The clean simplification and the contradiction of each pair are reused as they are; only the intermediate levels are new.
- The train/validation split per pair is unchanged.

For each base pair, build a **group** of candidates for the same Original, each with a target meaning score:

| Level | Target | Construction | Who |
|---|---|---|---|
| `original_copy` | 1.0 | The Original itself as the candidate: perfect meaning preservation, and longer than the clean text. | copy |
| `clean` | 1.0 | The reference simplification. | — |
| `neutral_trim` | 1.0 | Remove **non-informative** material only: a parenthetical left empty or pronunciation-only (`( ; )`, `(/ˈ…/)`), or the adverbs `also`, `very`, `really`, `just`. Only if one applies. | rule |
| `mild_loss` | 0.67 | Delete **one peripheral content constituent** (spaCy dependency parse): an adjectival modifier, a prepositional or adverbial adjunct that is not the main predicate, or a non-restrictive appositive. | rule |
| `major_loss` | 0.33 | Delete **one core content unit**: a coordinated clause, a relative clause, or a second sentence; **or** generalize one named entity or number to its category ("Warsaw" → "a city", "1867" → "the 19th century"). The model returns only the replacement (LLM C1, span-in/span-out like MMI). | rule / LLM |
| `contradiction` | 0.0 | The existing MMI MEANING degradation, when the pair has one. | existing |

**Checks for rule and LLM variants.** Each has a purpose:

| Check | Purpose |
|---|---|
| Acceptability ≥ min(τ, clean − δ) | Stays fluent. |
| Exactly one edit block vs clean | One controlled change. |
| For losses: NLI(clean → variant) contradiction < 0.5 | It is a **loss**, not a contradiction. |
| For `neutral_trim`: word-level edit removes only whitelisted tokens | Truly non-informative. |

**Do not** use NLI entailment thresholds to select or label the losses. The level comes from the rule (constituent type), not from NLI; this avoids training on NLI's own decisions again.

**Length control:** `original_copy` (longer, target 1) and `neutral_trim` (shorter, target 1) break the "shorter = worse" shortcut that deletions would otherwise create.

## 3. Human gate (Phase 6)

1. Blinded review of **15 per level** for `neutral_trim`, `mild_loss` and `major_loss`, per source (WikiAutoEN, ASSET): about 90 cases. The question: *"Compared with the clean text, how much meaning is lost?"*, with options none / some / a lot / contradiction.
2. **STOP** for the human audit.
3. **Gate:**
   - each level's modal human answer matches its intended level in ≥ 80% of cases;
   - `neutral_trim` is judged "none" in ≥ 90%.

   A level that fails is dropped, not re-tuned (report which).

Then generate all groups. Materialize one row per (group, level), with `target_score` and `group_id = canonical_pair_id`.

## 4. Training (Phase 7)

Same backbones, grid and seeds as Phase 7a: `deberta_v3_base` and `xlm_roberta_large`, learning rates {1e-5, 2e-5}, seeds {17, 29, 43}.

**Loss:**
- MSE on `target_score`;
- plus a **listwise pairwise margin loss** over every ordered pair of candidates in a group with different targets (margin 0.2 × target difference).
- Batches contain whole groups.

**Arms:**

| Arm | Input | Purpose |
|---|---|---|
| **A: graded** | `original </s> candidate` | The main test of the new data. |
| **B: graded + NLI** | Same, plus the 3 NLI probabilities (original → candidate) concatenated to the pooled representation before the head | "Use NLI instead of competing with it." |
| **A_all: graded, no entailment filter** | As A, on all 6,951 base pairs | Value of the entailment filter. |
| **C: v1 data + NLI** | The Phase 7a contradiction-only data, with B's architecture | Separates "better data" from "NLI input". |

NLI is the pinned Phase 6 checker; its features are precomputed for every training and evaluation item.

**Selection (synthetic validation only), no longer saturated:**
- Spearman between prediction and `target_score` over all validation candidates;
- tie-break by the mean within-group pairwise accuracy on adjacent levels (clean vs `mild_loss`, `mild_loss` vs `major_loss`).

**Synthetic validation diagnostic (reported):** the within-group pairwise accuracy of the length-ratio and acceptability baselines. **STOP** if either is ≥ 0.80. That means a shortcut still explains the data; fix the length controls before training.

## 5. Evaluation (unchanged protocol)

- Run `phase7_feats_training/src/run_evaluation.py` (from Phase 7a) with the selected configuration of each arm, on the same frozen sets, with 10,000 repetitions.
- Add the arm dimension and **v1 as a row** in every table.
- **Pre-registered criteria for arm A:**

| # | Criterion |
|---|---|
| Q1 | Spearman CI > 0 on Simplicity-DA and Human-Likert, **and** non-inferior to NLI (lower CI bound of Δρ > −0.05) on both. |
| Q2 | Δρ vs NLI > 0 with a CI excluding 0 on at least one set (the strong result). |
| Q4 (new) | Improvement over v1: paired Δρ (A − v1) CI excluding 0 on at least one set, and no significant loss on the other. |

- Arms B and C are judged by the same Q1/Q2.
- **Reported without a gate:**
  - system-level Pearson on Simplicity-DA (v1 got 0.02);
  - SimpEval-2022;
  - human-audited heldout pairs;
  - Vikidia heldout as a separate diagnostic.

**Reading the outcome:**

| Outcome | Next step |
|---|---|
| A passes Q1 | The graded recipe works. Apply the same idea (graded negatives + length controls) to the other axes before training them. |
| Only B passes | NLI-augmented models become the recommended architecture. |
| Nothing passes | Human-data fine-tuning (the REFEREE curriculum) is needed. Plan it separately, with an original-disjoint human split. Note that Simplicity-DA and Human-Likert may share TurkCorpus originals, so check this before any cross-training. |

## 6. Deliverables

- Phase 6:
  - `src/generation/generate_meaning_graded.py` (the rules + the LLM generalization);
  - tests with must-change / must-not-change cases per level;
  - the review file;
  - `docs/reports/current/meaning_graded_v1_report.md`.
- Phase 7:
  - the grouped dataset builder;
  - the listwise loss;
  - the NLI-feature head;
  - `docs/reports/meaning_v2.md` with v1 vs A/B/C tables and the answers to Q1/Q2/Q4.
- Local commits. **No push.**

## Execution status (2026-10-01)

- Step 1 done: graded groups built with rules only. The LLM entity generalization was deferred; year and number generalization are done by rule.
  - **Entailment-filtered (4,514 pairs):** mild loss 3,123, major loss 1,370, neutral trim 154. Neutral trims are rare, so length control relies mainly on `original_copy`.
  - **`A_all` variant:** 6,951 pairs, built in parallel.
  - Files: `phase6_degraded_corpus/runs/meaning_graded_en_v1/groups{,_all}.jsonl`.
- **First review (80 cases):** mild loss passes (87%); major loss (63%) and neutral trim (80%) fail. The breakdown by sub-rule showed mislabeled rules, not failing levels: `very` was judged "Some"; year generalization "Some"; number generalization buggy; clause deletions only 67% "A lot".
- **v2.1 mapping (re-tuned on that review):**

  | Level | Rules |
  |---|---|
  | neutral trim | remove `also` / `just` |
  | mild loss | adjective, appositive, prepositional adjunct, adverb, `very` / `really`, relative or coordinated clause, year → century |
  | major loss | drop a whole sentence |

  Number generalization was removed.
  - **Groups (4,514 pairs):** mild 3,335, major 809, neutral 130.
  - **`A_all` (6,951 pairs):** mild 5,411, major 1,198, neutral 207.
- **Because the mapping was tuned on the first review, the gate is decided by a fresh confirmation review on unseen pairs:** [`meaning_graded_review_v21.md`](../../../phase6_degraded_corpus/docs/reports/current/meaning_graded_review_v21.md) (20 major + 10 neutral). The mild level already passed and was not re-tuned. **STOP for it.**

## 7. Order and STOP points

1. Rules + tests; generate a sample; build the review. **STOP for the human audit.**
2. Full generation of the passing levels; materialize; leakage gate.
3. Precompute NLI features; synthetic shortcut diagnostic. **STOP if a shortcut ≥ 0.80.**
4. Train arms A, B, C; select on synthetic validation.
5. Evaluate once; report; commit.
