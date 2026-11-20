#!/usr/bin/env bash
# Sentence-level SARI on SimpEval 2022 (LENS implementation), copied next to the other
# SimpEval 2022 baselines that the Phase 7 evaluation joins.
set -euo pipefail
PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
cd "$PROJECT_ROOT"
export NLTK_DATA="$PROJECT_ROOT/cache/nltk_data"
[ -d "$NLTK_DATA/tokenizers/punkt_tab" ] || .venv-phase5-lens/bin/python -c "import nltk; nltk.download('punkt_tab', download_dir='$NLTK_DATA', quiet=True)"
out=phase5_external_metrics/runs/sari_simpeval_2022/simpeval_2022_sari.jsonl
.venv-phase5-lens/bin/python phase5_external_metrics/src/score_sari_simpeval.py \
  --lens-repo phase6_degraded_corpus/runs/mmi_en_v2/pools/evaluation_sources/lens_heineman --output "$out"
cp "$out" phase7_feats_training/runs/axis_validation_v1/baselines/predictions/simpeval_2022_sari.jsonl
