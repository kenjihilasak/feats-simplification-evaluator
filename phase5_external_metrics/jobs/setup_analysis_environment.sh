#!/bin/bash
set -euo pipefail

PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
python3.10 -m venv "${PROJECT_ROOT}/.venv-phase5-analysis"
"${PROJECT_ROOT}/.venv-phase5-analysis/bin/pip" install --upgrade pip
"${PROJECT_ROOT}/.venv-phase5-analysis/bin/pip" install -r "${PROJECT_ROOT}/phase5_external_metrics/requirements-analysis.txt"
