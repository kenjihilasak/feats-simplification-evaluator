#!/bin/bash
#SBATCH --job-name=feats_p3a_3models
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase3a_strategy_detection/logs/three_models_%A_%a.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase3a_strategy_detection/logs/three_models_%A_%a.err
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --mem=96G
#SBATCH --cpus-per-task=8
#SBATCH --array=0-2

set -euo pipefail

PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
PYTHON_BIN=${PROJECT_ROOT}/.venv-phase3/bin/python
CONFIG=${1:-phase3a_strategy_detection/configs/experiments/three_models_phase2b_pilot_v1.json}
MODELS=(xlmr_large_focal multilingual_e5_large_bce qwen2p5_7b_pairwise_qlora)
MODEL_ALIAS=${MODELS[${SLURM_ARRAY_TASK_ID}]}

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Missing ${PYTHON_BIN}. Run setup_environment.sh first." >&2
  exit 1
fi

export PYTHONUNBUFFERED=1
export TOKENIZERS_PARALLELISM=false
export HF_HOME=${PROJECT_ROOT}/cache/huggingface
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

cd "${PROJECT_ROOT}"
nvidia-smi
"${PYTHON_BIN}" phase3a_strategy_detection/src/run_strategy_detection.py \
  --config "${CONFIG}" \
  --model-alias "${MODEL_ALIAS}"
"${PYTHON_BIN}" phase3a_strategy_detection/src/validate_run.py \
  --config "${CONFIG}" \
  --model-alias "${MODEL_ALIAS}"
