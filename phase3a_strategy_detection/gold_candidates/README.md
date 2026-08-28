# Phase 3a gold candidates

This group contains reproducible candidate datasets derived from Phase 3a
model predictions. Generated data files are kept outside Git history; each
candidate run retains its configuration, manifest, summary and aggregate
reports in the repository.

The first selection uses label-wise majority voting across Qwen, E5 and XLM-R.
A pair is retained when exactly one of the six strategy labels receives at
least two votes. These records are **unreviewed model-consensus candidates**,
not gold labels. Human annotation and adjudication are still required.

Every retained record has a quality tier. The exact-singleton tiers identify
cases where at least two models predict only the winning strategy. The broader
label-majority-only tier satisfies label-wise majority voting but may contain
additional strategies predicted by individual models; it therefore has lower
priority for human review.

The current full multilingual results are documented in the
[2026-08-26 single-strategy majority-vote report](2026-08-26_single_strategy_majority_vote_v1/reports/summary.md).
