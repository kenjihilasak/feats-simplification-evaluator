# Phase 3a gold candidates

The active candidate set is
`2026-08-31_single_strategy_gemma_anchored_strict_v1` (**167,238 pairs in
12 languages**). Gemma must predict exactly one strategy and at least one of
E5, Qwen, or XLM-R must predict exactly the same singleton.

Build and independently validate it with:

```bash
.venv-phase3/bin/python \
  phase3a_strategy_detection/src/build_gemma_anchored_gold_candidates.py
```

The candidate directory contains one JSONL per language, integrity manifests,
aggregate reports, and the readable
[`qualitative_review_sample.md`](2026-08-31_single_strategy_gemma_anchored_strict_v1/reports/qualitative_review_sample.md).
These are unreviewed model-consensus candidates, not gold labels; Phase 4a
human annotation and adjudication are still required.
