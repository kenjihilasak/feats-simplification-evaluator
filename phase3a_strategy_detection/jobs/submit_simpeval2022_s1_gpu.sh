#!/bin/bash
#SBATCH --job-name=feats_p3a_simpeval
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase3a_strategy_detection/logs/simpeval2022_s1_%j.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase3a_strategy_detection/logs/simpeval2022_s1_%j.err
#SBATCH --time=03:00:00
#SBATCH --nodes=1
#SBATCH --partition=gpu
#SBATCH --gres=gpu:l40s:1
#SBATCH --mem=96G
#SBATCH --cpus-per-task=8
# Phase 3a strategy detection on the 180 SimpEval-2022 pairs (60 originals x best human, GPT-3-few-shot, Muss),
# all four models in sequence on one GPU. Input: build_simpeval_s1_items.py prepare. Afterwards (CPU):
#   PYTHONPATH=$PWD .venv-phase6-vllm/bin/python -m phase6_degraded_corpus.src.annotation.build_simpeval_s1_items build

set -euo pipefail

PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
PYTHON_BIN=${PROJECT_ROOT}/.venv-phase3/bin/python
CONFIG=${1:-phase3a_strategy_detection/configs/experiments/simpeval2022_s1_v1.json}
MODELS=(xlmr_large_focal multilingual_e5_large_bce qwen2p5_7b_pairwise_qlora gemma3_12b_pairwise_qlora)

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
for MODEL_ALIAS in "${MODELS[@]}"; do
  echo "[$(date -Is)] ${MODEL_ALIAS}"
  "${PYTHON_BIN}" phase3a_strategy_detection/src/run_strategy_detection.py \
    --config "${CONFIG}" \
    --model-alias "${MODEL_ALIAS}"
  "${PYTHON_BIN}" phase3a_strategy_detection/src/validate_run.py \
    --config "${CONFIG}" \
    --model-alias "${MODEL_ALIAS}"
done
echo "[$(date -Is)] done"
