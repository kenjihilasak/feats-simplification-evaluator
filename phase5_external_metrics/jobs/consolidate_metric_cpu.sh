#!/bin/bash
#SBATCH --job-name=feats_p5_join
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase5_external_metrics/logs/consolidate_%j.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase5_external_metrics/logs/consolidate_%j.err
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --partition=cpu
#SBATCH --mem=16G
#SBATCH --cpus-per-task=2

set -euo pipefail
PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
METRIC_ALIAS=${1:?Usage: sbatch consolidate_metric_cpu.sh lens_salsa\|referee [config] [num_shards]}
CONFIG=${2:-phase5_external_metrics/configs/experiments/full_en_v1.json}
NUM_SHARDS=${3:-32}
PYTHON_BIN=${PROJECT_ROOT}/.venv-phase5-lens/bin/python
cd "${PROJECT_ROOT}"
"${PYTHON_BIN}" phase5_external_metrics/src/consolidate_shards.py \
  --config "${CONFIG}" --metric-alias "${METRIC_ALIAS}" --num-shards "${NUM_SHARDS}"
"${PYTHON_BIN}" phase5_external_metrics/src/validate_run.py \
  --config "${CONFIG}" --metric-alias "${METRIC_ALIAS}"
