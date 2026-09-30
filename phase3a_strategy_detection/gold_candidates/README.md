# Phase 3a gold candidates

The active candidate set is
`2026-09-30_single_strategy_gemma_anchored_strict_textrepair_v1` (**168,382
pairs in 12 languages**), built from the validated text-repaired effective
predictions. The previous raw-text set
`2026-08-31_single_strategy_gemma_anchored_strict_v1` is retained unchanged.
Gemma must predict exactly one strategy and at least one of
E5, Qwen, or XLM-R must predict exactly the same singleton.

Build and independently validate it with:

```bash
.venv-phase3/bin/python \
  phase3a_strategy_detection/src/build_gemma_anchored_gold_candidates.py
```

The candidate directory contains one JSONL per language, integrity manifests,
aggregate reports, and the readable
[`summary.md`](2026-09-30_single_strategy_gemma_anchored_strict_textrepair_v1/reports/summary.md).
These are unreviewed model-consensus candidates, not gold labels; Phase 4a
human annotation and adjudication are still required.
