#!/bin/bash

set -euo pipefail

PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
BASE_PYTHON=/scratch/pjbd103/miniconda3/envs/SimAlign/bin/python
VENV=${PROJECT_ROOT}/.venv-phase4a

if [[ ! -x "${BASE_PYTHON}" ]]; then
  echo "Missing SimAlign Python environment: ${BASE_PYTHON}" >&2
  exit 1
fi

cd "${PROJECT_ROOT}"
"${BASE_PYTHON}" -m venv --system-site-packages "${VENV}"
"${VENV}/bin/python" -m pip install -r phase4a_gold_standard/requirements-runtime.txt
"${VENV}/bin/python" -m pip install -r phase4a_gold_standard/requirements-dev.txt
"${VENV}/bin/python" -c "import fastapi, stanza, uvicorn; print('Phase 4a environment ready')"
