#!/bin/bash
set -euo pipefail

PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
BASE_PYTHON=/scratch/pjbd103/miniconda3/envs/uncertainty-benchmark/bin/python
VENV_ROOT=${PROJECT_ROOT}/.venv-phase3

if [[ ! -x "${VENV_ROOT}/bin/python" ]]; then
  "${BASE_PYTHON}" -m venv --system-site-packages "${VENV_ROOT}"
fi

"${VENV_ROOT}/bin/python" -m pip install --no-deps \
  -r "${PROJECT_ROOT}/phase3_strategy_detection/requirements-runtime.txt"

"${VENV_ROOT}/bin/python" -c \
  'import bitsandbytes, peft; print("bitsandbytes", bitsandbytes.__version__); print("peft", peft.__version__)'
