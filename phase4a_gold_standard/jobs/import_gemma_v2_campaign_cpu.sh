#!/bin/bash
#SBATCH --job-name=feats_p4a_v2_import
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase4a_gold_standard/logs/v2_import_%j.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase4a_gold_standard/logs/v2_import_%j.err
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --partition=nodes
#SBATCH --mem=8G
#SBATCH --cpus-per-task=2

set -euo pipefail

PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
PYTHON_BIN=${PROJECT_ROOT}/.venv-phase4a/bin/python
MATERIALIZED_ROOT=${PROJECT_ROOT}/phase4a_gold_standard/runs/materialized/2026-08-31_stanza_ud_gemma_anchored_strict_v2
DATABASE=${PROJECT_ROOT}/phase4a_gold_standard/runtime/gemma_anchored_strict_v2.sqlite3
LANGUAGES=(ar ca de en es fr it ja pt-BR ru sl ur)

export PHASE4A_CAMPAIGN_ID=gemma-anchored-strict-v2
export PHASE4A_SESSION_COOKIE=phase4a_v2_session
export PHASE4A_CSRF_COOKIE=phase4a_v2_csrf
cd "${PROJECT_ROOT}"

for language in "${LANGUAGES[@]}"; do
  payload=${MATERIALIZED_ROOT}/${language}/payloads/${language}/annotation_tasks.jsonl
  test -s "${payload}"
  "${PYTHON_BIN}" -m phase4a_gold_standard.backend \
    --database "${DATABASE}" import-tasks "${payload}"
done

"${PYTHON_BIN}" -m phase4a_gold_standard.backend \
  --database "${DATABASE}" progress
