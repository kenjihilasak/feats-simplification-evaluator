#!/bin/bash
#SBATCH --job-name=feats_p4a_stanza_models
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase4a_gold_standard/logs/stanza_models_%j.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase4a_gold_standard/logs/stanza_models_%j.err
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --mem=16G
#SBATCH --cpus-per-task=2

set -euo pipefail

PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
PYTHON_BIN=${PROJECT_ROOT}/.venv-phase4a/bin/python
CONFIG=${1:-phase4a_gold_standard/configs/stanza_ud_syntax_v1.json}

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Missing ${PYTHON_BIN}; run phase4a_gold_standard/jobs/setup_environment.sh" >&2
  exit 1
fi

export PYTHONUNBUFFERED=1
cd "${PROJECT_ROOT}"
"${PYTHON_BIN}" phase4a_gold_standard/src/download_stanza_models.py --config "${CONFIG}"
