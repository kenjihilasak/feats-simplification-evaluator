#!/bin/bash
#SBATCH --job-name=feats_p5_metric
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase5_external_metrics/logs/metric_%A_%a.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase5_external_metrics/logs/metric_%A_%a.err
#SBATCH --time=08:00:00
#SBATCH --nodes=1
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --cpus-per-task=8
#SBATCH --array=0-31

set -euo pipefail

PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
METRIC_ALIAS=${1:?Usage: sbatch submit_metric_shards_gpu.sh lens_salsa\|referee [config] [num_shards]}
CONFIG=${2:-phase5_external_metrics/configs/experiments/full_en_v1.json}
NUM_SHARDS=${3:-32}
if [[ "${METRIC_ALIAS}" == "lens_salsa" ]]; then
  PYTHON_BIN=${PROJECT_ROOT}/.venv-phase5-lens/bin/python
elif [[ "${METRIC_ALIAS}" == "referee" ]]; then
  PYTHON_BIN=${PROJECT_ROOT}/.venv-phase5-referee/bin/python
else
  echo "Unsupported metric: ${METRIC_ALIAS}" >&2
  exit 2
fi
if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Missing metric environment: ${PYTHON_BIN}" >&2
  exit 1
fi
if (( SLURM_ARRAY_TASK_ID >= NUM_SHARDS )); then
  echo "Array index exceeds requested shard count." >&2
  exit 2
fi
export HF_HOME=${PROJECT_ROOT}/cache/huggingface
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
cd "${PROJECT_ROOT}"
"${PYTHON_BIN}" phase5_external_metrics/src/run_external_metrics.py \
  --config "${CONFIG}" --metric-alias "${METRIC_ALIAS}" \
  --shard-index "${SLURM_ARRAY_TASK_ID}" --num-shards "${NUM_SHARDS}" --resume
"${PYTHON_BIN}" phase5_external_metrics/src/validate_run.py \
  --config "${CONFIG}" --metric-alias "${METRIC_ALIAS}" \
  --shard-index "${SLURM_ARRAY_TASK_ID}" --num-shards "${NUM_SHARDS}"
