# LENS-SALSA and REFEREE compared with Phase 4a human decisions

## Scope and label policy

This report compares LENS-SALSA and REFEREE with the English decisions recorded
in the **Phase 4a review UI** at export time. The review decisions are converted
to binary labels using the following policy:

- **Positive:** `submitted + correct`.
- **Negative:** `submitted + incorrect`, `submitted + uncertain`, and `Later`.
- **Excluded:** all drafts.

The evaluated cohort contains 24 decisions:

| Label | Decision type | Pairs |
|---|---|---:|
| Positive | `correct` | 7 |
| Negative | `incorrect` | 2 |
| Negative | `uncertain` | 0 |
| Negative | `Later` | 15 |
| Excluded | `draft` | 1 |

## Inference validation

- LENS-SALSA: **24/24** valid predictions and no truncation.
- REFEREE: **24/24** valid predictions and no truncation.
- Both sidecars contain exactly the same `canonical_pair_id` set as the
  included human decisions.
- No duplicate or non-finite scores were found.

The metrics retain their native scales. A LENS-SALSA score must not be directly
compared with, subtracted from, or averaged with a REFEREE score.

## Binary ranking results

A higher score is treated as stronger support for the positive label.

| Metric | AUROC | Average precision |
|---|---:|---:|
| LENS-SALSA | 0.798 | 0.609 |
| REFEREE | 0.824 | 0.724 |

In this sample, REFEREE ranks positive decisions above negative decisions
slightly better than LENS-SALSA. These estimates are preliminary: there are
only seven positives and two submitted `incorrect` decisions, while the other
15 negatives are `Later` decisions.

AUROC measures how often a randomly selected positive receives a higher score
than a randomly selected negative. Average precision measures how concentrated
the positive examples are near the top of the ranking. The positive prevalence
is 7/24, so the no-skill average-precision baseline is approximately 0.292.

## How ranking disagreement is calculated

The 24 scores are sorted independently for each metric and converted to a
within-cohort rank from 1 (lowest) to 24 (highest). The percentile is the same
position represented on a scale from 0 to 1.

- A negative decision placed near rank 24 has high disagreement.
- A positive decision placed near rank 1 has high disagreement.
- A disagreement value near 1 means a highly unexpected ranking position.
- It is **not** a probability that the metric is wrong.

The mean ranking disagreement averages the two rank-based disagreement values,
not the two native metric scores. It is used only to prioritize cases for
manual inspection; no absolute good/bad threshold was imposed.

## Largest ranking disagreements

### 1. `Later`, but both metrics rank the pair near the top

**Original:** Monteux is a commune of the Vaucluse département in southern
France, in the area Provence-Alpes-Côte d'Azur.

**Simplification:** Monteux is a place where religious people live in southern
France, located in Provense-Alpes-Côte d'Azur.

- Human label: negative (`Later`).
- Candidate strategy: `EXPL`.
- LENS-SALSA: **75.547**, rank **22/24**, percentile **0.913**.
- REFEREE: **0.849**, rank **22/24**, percentile **0.913**.
- Mean ranking disagreement: **0.913**.

Only two pairs receive a higher score from either metric. The simplification
incorrectly interprets *commune* as a place where religious people live, making
this a particularly useful case for manual metric auditing.

### 2. `incorrect`, but especially LENS-SALSA ranks the pair highly

**Original:** Coal, building materials and general goods were delivered down
the incline and the contents of the village cesspits were hauled back up for
disposal along the lineside.

**Simplification:** Supplies like coal, building materials, and other things
were sent down the incline from the train station to the village.

- Human label: negative (`incorrect`).
- Candidate strategy: `SYN`; human correction: `OMIT`.
- LENS-SALSA: **77.546**, rank **23/24**, percentile **0.957**.
- REFEREE: **0.718**, rank **19/24**, percentile **0.783**.
- Mean ranking disagreement: **0.870**.

The reviewer rejected the candidate strategy and identified an omission.
LENS-SALSA assigns the second-highest score in the cohort, making this case a
priority for investigating sensitivity to content loss.

### 3. `Later`, with a relatively high LENS-SALSA rank

**Original:** Multimedia devices are electronic media devices used to store and
experience multimedia content.

**Simplification:** Multimedia also means the use of electronic media to store
and experience multimedia content.

- Human label: negative (`Later`).
- Candidate strategy: `EXPL`.
- LENS-SALSA: **73.993**, rank **19/24**, percentile **0.783**.
- REFEREE: **0.580**, rank **13/24**, percentile **0.522**.
- Mean ranking disagreement: **0.652**.

LENS-SALSA is more favorable than REFEREE. The change resembles a paraphrase
more than an explanation, which may account for the review decision.

### 4. The metrics disagree with each other

**Original:** On November 27, 2007, Osmond came in third place on the fifth
season of “Dancing with the Stars”.

**Simplification:** In 2007 she came in third place on the 5th season of the US
version of Dancing with the Stars.

- Human label: negative (`Later`).
- Candidate strategy: `COMP`.
- LENS-SALSA: **62.270**, rank **8/24**, percentile **0.304**.
- REFEREE: **0.657**, rank **18/24**, percentile **0.739**.

REFEREE is relatively favorable while LENS-SALSA is relatively unfavorable.
This pair is useful for studying how the metrics react to temporal detail,
referential clarity, and the added claim that this is the US version.

## Interpretation limits

1. Phase 4a primarily judges whether a candidate simplification strategy is
   correct, while LENS-SALSA and REFEREE estimate overall pair quality.
2. The requested policy treats `Later` as negative. A `Later` decision may also
   reflect deferral or an operational review choice, so this policy has a large
   effect on the present results.
3. A cohort of 24 pairs is too small for stable estimates by strategy or corpus.
4. AUROC and average precision remain descriptive until substantially more
   `incorrect` and `uncertain` decisions are available.
5. No classification threshold was selected. Disagreements are rank-based
   review priorities rather than claims that a metric or reviewer is wrong.

## Reproducibility artifacts

The local run directory contains:

- `human_metric_disagreements.csv`: all 24 cases ordered by ranking
  disagreement.
- `binary_evaluation.json`: the policy, summary statistics, and leading
  disagreements.
- `metrics/lens_salsa/predictions.jsonl`: immutable LENS-SALSA sidecar.
- `metrics/referee/predictions.jsonl`: immutable REFEREE sidecar.

Raw review exports and model predictions are intentionally excluded from Git.
This curated report records aggregate results and selected qualitative examples
without publishing reviewer credentials or the model checkpoints.
