# Axis validation v1 — stopped before training

**Experiment:** `axis_validation_v1`
**Date:** 30 September 2026
**Status:** **STOP — pre-training leakage gate failed**

## Decision

No baseline was scored and no model was trained or evaluated. The plan requires the pre-training leakage check to fail on any exact or near-duplicate match and says to stop at every STOP point. The audit found one exact match and four further near-duplicate matches between the Phase 6 full synthetic corpus and the human-audited heldout reviews.

Consequently Q1–Q3 are **not evaluated**. It would be invalid to answer them using a model trained on the current corpus.

## Pre-training audit

The contract conversion examined 37,076 rows (18,538 controlled pairs/originals):

| Check | Result |
|---|---:|
| Unit tests | 6/6 passed |
| Training originals | 18,538 |
| Evaluation originals | 664 |
| Exact strong-key matches | 1 |
| Near duplicates at word Jaccard ≥ 0.8 | 4 |
| Leakage gate | **FAIL** |

The exact original appears in two MEANING review campaigns (H116 in v2 and H047 in v2.1): “The Firebird (; ) is a ballet and orchestral concert work by the Russian composer Igor Stravinsky.”

The additional matches are:

| Training original (abbreviated) | Heldout set | Jaccard |
|---|---|---:|
| “However, admirals have always needed additional facilities, including a meeting room…” | v2 | 0.968 |
| “In ancient times, the sea was the birthplace of two ancient civilizations…” | MEANING v2.1 | 0.824 |
| “It is normally abbreviated with the dollar sign… ‘BZ$’…” | v2 | 0.889 |
| “The Democratic Party is one of the two major contemporary political parties…” | v2 | 0.895 |

The full machine-readable evidence is in the ignored run artifact `phase7_feats_training/runs/axis_validation_v1/data/leakage_check.json`.

One independent source-quality issue was found: MEANING v2.1 case H026 has both `Valid` and `Invalid` checked. The loader records it as `Conflicting` and excludes it from human-valid/Unsure scoring rather than guessing the intended label. Phase 6 inputs were not modified.

## Plan evaluation

The plan is strong: it pre-registers construct-matched criteria, separates synthetic selection from one-time human testing, and uses grouped/paired bootstrap inference. The paired objective and original-level split fit the controlled contrasts.

Four issues need correction before execution resumes:

1. The claimed heldout exclusion is false for the materialized `mmi_en_v2_full` corpus. Rebuild it after excluding the union of all audited canonical originals and all strong-key/Jaccard matches, then rerun this unchanged gate.
2. Only `xlm-roberta-large` was locally cached. DeBERTa-v3-base, the NLI checker, and CoLA must be staged at their pinned revisions before offline jobs run.
3. LENS-SALSA and REFEREE are named without a frozen adapter from these evaluation schemas to Phase 5 inputs, including treatment of unavailable references. Freeze that adapter before training.
4. “Not significantly worse” needs a pre-registered non-inferiority margin. A paired CI containing zero does not establish non-inferiority.

## Q1–Q3

| Question | Result | Reason |
|---|---|---|
| Q1: MEANING vs human ratings | Not evaluated | Pre-training leakage STOP |
| Q2: MEANING vs NLI | Not evaluated | Pre-training leakage STOP |
| Q3: MOD/ILLOC heldout ranking | Not evaluated | Q1/training not reached |

MOD and ILLOC still have no construct-matched human rating data; after repair, their human-audited degradation ranking remains the only evidence available here.

## Recommendation

Do **not** continue FOSE-axis corpus work or train `axis_validation_v1` yet. Repair and rematerialize Phase 6 using the frozen review originals, resolve or formally exclude the conflicting review, stage every pinned checkpoint, and rerun the pre-training gate. If the rebuilt corpus passes with zero hits, resume at fixed baseline scoring; do not weaken this audit.
