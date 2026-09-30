#!/bin/bash
#SBATCH --job-name=feats_p3a_gemma_merge
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase3a_strategy_detection/logs/full_gemma_consolidate_%j.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase3a_strategy_detection/logs/full_gemma_consolidate_%j.err
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --partition=nodes
#SBATCH --mem=32G
#SBATCH --cpus-per-task=2

set -euo pipefail

PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
PYTHON_BIN=${PROJECT_ROOT}/.venv-phase3/bin/python
CONFIG=phase3a_strategy_detection/configs/experiments/gemma3_phase2b_full_v1.json
MODEL_ALIAS=gemma3_12b_pairwise_qlora
NUM_SHARDS=128

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Missing ${PYTHON_BIN}. Run setup_environment.sh first." >&2
  exit 1
fi

export PYTHONUNBUFFERED=1
cd "${PROJECT_ROOT}"
"${PYTHON_BIN}" phase3a_strategy_detection/src/consolidate_shards.py \
  --config "${CONFIG}" \
  --model-alias "${MODEL_ALIAS}" \
  --num-shards "${NUM_SHARDS}"
"${PYTHON_BIN}" phase3a_strategy_detection/src/validate_run.py \
  --config "${CONFIG}" \
  --model-alias "${MODEL_ALIAS}"
