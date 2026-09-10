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

Ranks run from 1 (lowest metric score) to 24 (highest). A negative pair ranked
near 24, or a positive pair ranked near 1, is prioritized as a disagreement.
The disagreement value is a ranking aid, not an error probability.

1. **Monteux (`Later`, negative):** the simplification incorrectly describes a
   *commune* as a place where religious people live. Both metrics nevertheless
   assign high scores: LENS-SALSA **75.547** and REFEREE **0.849**. The
   candidate strategy recorded by the strategy model was `EXPL`.
2. **Multimedia devices (`Later`, negative):** the change resembles a
   paraphrase rather than an explanation. It receives LENS-SALSA **73.993**
   and REFEREE **0.580**; the candidate strategy was `EXPL`.

## Interpretation

These results are preliminary. Phase 4a primarily assesses whether a candidate
simplification strategy is correct, whereas LENS-SALSA and REFEREE estimate
overall pair quality. In addition, `Later` accounts for 15 of the 17 negatives
and may include deferred rather than definitively poor cases. More submitted
`incorrect` and `uncertain` decisions—and ideally explicit human quality
ratings—are needed for a reliable metric comparison.

The [complete ranked table of all 24 evaluated pairs](human_metric_disagreements.csv)
includes the texts, human labels, strategies, metric scores, percentiles, and
ranking-disagreement values. The table is ordered from highest to lowest mean
ranking disagreement; not every row is necessarily a strong disagreement.
