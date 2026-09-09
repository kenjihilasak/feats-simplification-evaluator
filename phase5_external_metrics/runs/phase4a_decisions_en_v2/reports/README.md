# LENS-SALSA and REFEREE on Phase 4a reviewed pairs

## Evaluation set

This report uses English decisions recorded in the **Phase 4a review UI**.

- **Positive:** `submitted + correct`.
- **Negative:** `submitted + incorrect`, `submitted + uncertain`, or `Later`.
- **Excluded:** drafts.

The current set contains 24 pairs: 7 positive and 17 negative (15 `Later`, 2
`incorrect`, and no `uncertain`). LENS-SALSA and REFEREE produced valid scores
for all 24 pairs, with no duplicates, non-finite values, or truncation.

## Results

| Metric | AUROC | Average precision |
|---|---:|---:|
| LENS-SALSA | 0.798 | 0.609 |
| REFEREE | 0.824 | 0.724 |

REFEREE provides slightly better separation in this small sample. The
no-skill average-precision baseline is 0.292 (7/24 positives). Scores remain on
their native scales and are not directly compared or averaged.

## Leading disagreements

Ranks run from 1 (lowest metric score) to 24 (highest). A negative pair ranked
near 24, or a positive pair ranked near 1, is prioritized as a disagreement.
The disagreement value is a ranking aid, not an error probability.

1. **Monteux (`Later`, negative):** the simplification incorrectly describes a
   *commune* as a place where religious people live. Both metrics nevertheless
   rank it **22/24** (mean rank disagreement: **0.913**).
2. **Coal and building materials (`incorrect`, negative):** the reviewer
   corrected `SYN` to `OMIT`. LENS-SALSA ranks it **23/24** and REFEREE
   **19/24** (mean rank disagreement: **0.870**), suggesting weak sensitivity
   to the omitted content.
3. **Multimedia devices (`Later`, negative):** the change resembles a
   paraphrase rather than an explanation. LENS-SALSA ranks it **19/24**, while
   REFEREE ranks it **13/24** (mean rank disagreement: **0.652**).

## Interpretation

These results are preliminary. Phase 4a primarily assesses whether a candidate
simplification strategy is correct, whereas LENS-SALSA and REFEREE estimate
overall pair quality. In addition, `Later` accounts for 15 of the 17 negatives
and may include deferred rather than definitively poor cases. More submitted
`incorrect` and `uncertain` decisions—and ideally explicit human quality
ratings—are needed for a reliable metric comparison.

Detailed local artifacts are available in the corresponding ignored run
directory as `human_metric_disagreements.csv` and `binary_evaluation.json`.
