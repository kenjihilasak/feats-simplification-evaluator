#!/bin/bash
#SBATCH --job-name=feats_p4a_syntax
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase4a_gold_standard/logs/syntax_%A_%a.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase4a_gold_standard/logs/syntax_%A_%a.err
#SBATCH --time=2-00:00:00
#SBATCH --nodes=1
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --array=0-11%4

set -euo pipefail

PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
PYTHON_BIN=${PROJECT_ROOT}/.venv-phase4a/bin/python
CONFIG=${1:-phase4a_gold_standard/configs/stanza_ud_syntax_gemma_anchored_strict_v2.json}
POOL_ROOT=${PROJECT_ROOT}/phase4a_gold_standard/data/2026-08-31_gemma_anchored_strict_v2
LANGUAGES=(ar ca de en es fr it ja pt-BR ru sl ur)
LANGUAGE=${LANGUAGES[${SLURM_ARRAY_TASK_ID}]}
SHARD_BASE=${PROJECT_ROOT}/phase4a_gold_standard/runs/stanza_shards/${LANGUAGE}
SYNTAX_ROOT=${SHARD_BASE}/2026-08-31_stanza_ud_gemma_anchored_strict_v2
MATERIALIZED_ROOT=${PROJECT_ROOT}/phase4a_gold_standard/runs/materialized/2026-08-31_stanza_ud_gemma_anchored_strict_v2/${LANGUAGE}

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Missing ${PYTHON_BIN}; run phase4a_gold_standard/jobs/setup_environment.sh" >&2
  exit 1
fi

export PYTHONUNBUFFERED=1
cd "${PROJECT_ROOT}"
nvidia-smi
"${PYTHON_BIN}" phase4a_gold_standard/src/build_stanza_syntax_sidecars.py build   --config "${CONFIG}"   --language "${LANGUAGE}"   --output-root "${SHARD_BASE}"   --fail-on-parse-error
"${PYTHON_BIN}" phase4a_gold_standard/src/build_stanza_syntax_sidecars.py materialize   --payload-root "${POOL_ROOT}"   --syntax-root "${SYNTAX_ROOT}"   --output-root "${MATERIALIZED_ROOT}"
