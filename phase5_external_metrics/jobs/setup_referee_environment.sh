#!/bin/bash
set -euo pipefail

PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
python3.10 -m venv "${PROJECT_ROOT}/.venv-phase5-referee"
"${PROJECT_ROOT}/.venv-phase5-referee/bin/pip" install --upgrade pip
"${PROJECT_ROOT}/.venv-phase5-referee/bin/pip" install -r "${PROJECT_ROOT}/phase5_external_metrics/requirements-referee.txt"
mkdir -p "${PROJECT_ROOT}/cache/referee"
echo "Place the official REFEREE pretrained.bin at ${PROJECT_ROOT}/cache/referee/pretrained.bin"
echo "Then set checkpoint_sha256 in configs/models/referee.json. Do not redistribute it."
