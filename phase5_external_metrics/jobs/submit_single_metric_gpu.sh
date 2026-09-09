#!/bin/bash
#SBATCH --job-name=feats_p5_single
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase5_external_metrics/logs/single_%j.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase5_external_metrics/logs/single_%j.err
#SBATCH --time=08:00:00
#SBATCH --nodes=1
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --cpus-per-task=8

set -euo pipefail

PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
METRIC_ALIAS=${1:?Usage: sbatch submit_single_metric_gpu.sh lens_salsa\|referee config}
CONFIG=${2:?Usage: sbatch submit_single_metric_gpu.sh lens_salsa\|referee config}
if [[ "${METRIC_ALIAS}" == "lens_salsa" ]]; then
  PYTHON_BIN=${PROJECT_ROOT}/.venv-phase5-lens/bin/python
  MODEL_CONFIG=phase5_external_metrics/configs/models/lens_salsa_pilot.json
elif [[ "${METRIC_ALIAS}" == "referee" ]]; then
  PYTHON_BIN=${PROJECT_ROOT}/.venv-phase5-referee/bin/python
  MODEL_CONFIG=phase5_external_metrics/configs/models/referee.json
else
  echo "Unsupported metric: ${METRIC_ALIAS}" >&2
  exit 2
fi

export HF_HOME=${PROJECT_ROOT}/cache/huggingface
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
cd "${PROJECT_ROOT}"
nvidia-smi
"${PYTHON_BIN}" phase5_external_metrics/src/verify_official_examples.py \
  --model-config "${MODEL_CONFIG}" --cache-root cache/huggingface
"${PYTHON_BIN}" phase5_external_metrics/src/run_external_metrics.py \
  --config "${CONFIG}" --metric-alias "${METRIC_ALIAS}" --resume
"${PYTHON_BIN}" phase5_external_metrics/src/validate_run.py \
  --config "${CONFIG}" --metric-alias "${METRIC_ALIAS}"
