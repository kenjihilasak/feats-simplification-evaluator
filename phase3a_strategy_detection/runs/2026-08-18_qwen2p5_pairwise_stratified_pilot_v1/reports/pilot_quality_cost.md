# Phase 3 stratified pilot: quality and cost

This historical run evaluates only Qwen2.5-7B on Phase 2 occurrence IDs.
It does not validate all three checkpoints on canonical Phase 2b input.

## Coverage

- Pairs: 855
- Files/corpora: 29
- Languages: 12
- Sampling: 25 deterministic random pairs plus 5 longest pairs per file,
  with overlaps removed.

This is a diagnostic sample, not an unbiased corpus estimate: every source
has similar weight and long pairs are intentionally oversampled.

## Automatic prediction profile

- Mean strategies per pair: 2.432
- Zero-strategy pairs: 3.39%
- Pairs with at least two strategies: 71.70%
- Most frequent strategy: SYN (65.96%)
- Least frequent strategy: EXPL (12.87%)

## Comparison with existing upstream labels

- Labelled pilot pairs: 117
- Exact match: 0.308
- Micro F1: 0.816
- Macro F1: 0.779
- Hamming loss: 0.175
- Mean upstream strategies: 2.564
- Mean predicted strategies: 3.154

These labels come from the upstream iDEM/Saaq dataset.csv. Their provenance
is not documented locally: they may be human, LLM-generated, or classifier
predictions. The scores below are descriptive comparisons, not gold evaluation.

## Short quality review

- Strongest per-label F1: MOD=0.964, SYN=0.963.
- Weakest per-label F1: SYNT=0.462, COMP=0.714.
- The model predicts 0.590 more strategies per labelled pair
  than the upstream labels. SYNT and COMP account for many mismatches, but
  these cannot be called false positives without verified reference labels.
- Mean strategy count ranges from 1.23
  for ur to 3.24
  for de. This may partly reflect corpus differences,
  but it is too large to assume equal calibration across languages.
- Truncated pairs: 0/855; maximum prompt length:
  1746 tokens. Truncation does not explain the disagreement.

Manual reading confirms meaningful mismatches, but their direction cannot be
decided from unverified upstream labels alone. Therefore, the released
thresholds are adequate for pipeline testing, but the full corpus should not be
processed until a small language-balanced manual review and a comparison with
the encoder checkpoints are completed.

## Runtime and projected cost

- GPU: NVIDIA L40S
- End-to-end runner time: 871.78 seconds
- Model preparation: 74.68 seconds
- Model load: 328.50 seconds
- Preparation plus load overhead: 403.18 seconds
- Pilot inference: 467.18 seconds
- Inference seconds per pair: 0.5464
- Projected single-GPU time for 854,486 pairs: 129.69 hours
- Idealized 2-GPU inference time: 64.85 hours
- Idealized 4-GPU inference time: 32.42 hours
- Idealized 8-GPU inference time: 16.21 hours

The projection assumes this pilot's deliberately long-text-heavy mixture and
the same GPU type. The later full-run sharding decision should use this as
an engineering estimate, not a guaranteed runtime. Multi-GPU figures assume
perfect balancing and exclude repeated model startup for each shard.

## Detailed files

- strategy_summary_language.csv
- strategy_summary_language_source.csv
- strategy_summary_language_source_corpus.csv
- strategy_count_distribution.csv
- upstream_label_comparison.csv and .json
- upstream_label_comparison_by_language.csv
- prediction_diagnostics.json
- [Qualitative examples](qualitative_examples.md)
