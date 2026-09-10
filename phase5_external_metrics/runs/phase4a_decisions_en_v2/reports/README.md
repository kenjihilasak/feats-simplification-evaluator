# LENS-SALSA and REFEREE on Phase 4a reviewed pairs

## Evaluation set

This report uses English decisions recorded in the **Phase 4a review UI**.

- **Positive:** `submitted + correct`.
- **Negative:** `submitted + incorrect`, `submitted + uncertain`, or `Later`.
- **Excluded:** drafts.

The current set contains 24 pairs: 7 positive and 17 negative (15 `Later`, 2
`incorrect`, and no `uncertain`).

## Results

| Metric | AUROC | Average precision |
|---|---:|---:|
| LENS-SALSA | 0.798 | 0.609 |
| REFEREE | 0.824 | 0.724 |

REFEREE provides slightly better separation in this small sample. The
no-skill average-precision baseline is 0.292 (7/24 positives). Scores remain on
their native scales and are not directly compared or averaged.

LENS-SALSA ranges from **0 to 100**. REFEREE has **no fixed lower or upper
bound**; in this evaluation its scores range from **-0.569 to 1.103**. For both
metrics, a higher score indicates better estimated simplification quality.

## Leading disagreements

A disagreement occurs when the human review marks a pair as negative but a
metric assigns it a relatively high quality score. `Later` is treated as a
negative decision, following the policy agreed with the reviewers.

1. **Incorrect explanation of “commune” (`Later`; strategy: `EXPL`)**

   - Original: “Monteux is a commune of the Vaucluse département in southern
     France, in the area Provence-Alpes-Côte d’Azur.”
   - Simplification: “Monteux is a place where religious people live in
     southern France, located in Provense-Alpes-Côte d’Azur.”
   - Metrics: LENS-SALSA **75.547** (rank **22/24**) and REFEREE **0.849**
     (rank **22/24**).
   - Disagreement: the simplification introduces an incorrect definition of
     *commune*, but both metrics place the rejected pair near the top of the
     evaluated set.

2. **Definition changed rather than simplified (`Later`; strategy: `EXPL`)**

   - Original: “Multimedia devices are electronic media devices used to store
     and experience multimedia content.”
   - Simplification: “Multimedia also means the use of electronic media to
     store and experience multimedia content.”
   - Metrics: LENS-SALSA **73.993** (rank **19/24**) and REFEREE **0.580**
     (rank **13/24**).
   - Disagreement: the candidate changes a definition of *multimedia devices*
     into a statement about *multimedia*. LENS-SALSA especially assigns high
     quality to a pair rejected by the reviewer.

3. **Information removed and added (`Later`; strategy: `COMP`)**

   - Original: “On November 27, 2007, Osmond came in third place on the fifth
     season of ‘Dancing with the Stars’.”
   - Simplification: “In 2007 she came in third place on the 5th season of the
     US version of Dancing with the Stars.”
   - Metrics: LENS-SALSA **62.270** (rank **8/24**) and REFEREE **0.657**
     (rank **18/24**).
   - Disagreement: the exact date is removed and “US version” is introduced.
     REFEREE ranks this negative pair relatively highly, whereas LENS-SALSA is
     more consistent with the human decision.

4. **Unsupported information added (`Later`; strategy: `EXPL`)**

   - Original: “Bartram was given the death penalty after the war.”
   - Simplification: “Bartram was given the death penalty after the war but
     was later pardoned and the sentence was changed to life in prison.”
   - Metrics: LENS-SALSA **71.050** (rank **17/24**) and REFEREE **0.470**
     (rank **7/24**).
   - Disagreement: the simplification adds information that cannot be verified
     from the original. LENS-SALSA ranks the rejected pair relatively highly;
     REFEREE aligns more closely with the negative review.

Ranks run from 1 (lowest metric score) to 24 (highest). The complete table
linked below provides every evaluated pair, not only these examples.

## Interpretation

These results are preliminary. Phase 4a primarily assesses whether a candidate
simplification strategy is correct, whereas LENS-SALSA and REFEREE estimate
overall pair quality. Under the agreed review policy, `Later` denotes a poor simplification and is
therefore included among the negative decisions.

The [complete ranked table of all 24 evaluated pairs](human_metric_disagreements.csv)
includes the texts, human labels, strategies, metric scores, percentiles, and
ranking-disagreement values. The table is ordered from highest to lowest mean
ranking disagreement; not every row is necessarily a strong disagreement.
