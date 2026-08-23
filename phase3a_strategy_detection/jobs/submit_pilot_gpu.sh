#!/bin/bash
#SBATCH --job-name=feats_p3a_pilot
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase3a_strategy_detection/logs/pilot_%j.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase3a_strategy_detection/logs/pilot_%j.err
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --mem=96G
#SBATCH --cpus-per-task=8

set -euo pipefail

PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
PYTHON_BIN=${PROJECT_ROOT}/.venv-phase3/bin/python
CONFIG=${1:-phase3a_strategy_detection/configs/qwen2p5_pairwise_stratified_pilot_v1.json}

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Missing ${PYTHON_BIN}. Run phase3a_strategy_detection/jobs/setup_environment.sh first." >&2
  exit 1
fi

export PYTHONUNBUFFERED=1
export TOKENIZERS_PARALLELISM=false
export HF_HOME=${PROJECT_ROOT}/cache/huggingface
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

cd "${PROJECT_ROOT}"
nvidia-smi
"${PYTHON_BIN}" phase3a_strategy_detection/src/run_strategy_detection.py \
  --config "${CONFIG}"
"${PYTHON_BIN}" phase3a_strategy_detection/src/validate_run.py \
  --config "${CONFIG}"
"${PYTHON_BIN}" phase3a_strategy_detection/src/summarize_pilot.py \
  --config "${CONFIG}"
