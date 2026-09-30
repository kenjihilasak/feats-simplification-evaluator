#!/bin/bash
#SBATCH --job-name=p3a_textrepair_control
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase3a_strategy_detection/logs/textrepair_control_%j.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase3a_strategy_detection/logs/textrepair_control_%j.err
#SBATCH --time=01:00:00
#SBATCH --partition=nodes
#SBATCH --mem=32G
#SBATCH --cpus-per-task=2
set -euo pipefail
ROOT=/scratch/pjbd103/feats-simplification-evaluator
cd "$ROOT"
.venv-phase3/bin/python phase3a_strategy_detection/src/compare_textrepair_control.py \
 --v1-root phase3a_strategy_detection/runs/2026-08-20_three_models_phase2b_full_v1 \
 --control-root phase3a_strategy_detection/runs/2026-09-30_four_models_textrepair_control_v1 \
 --output phase3a_strategy_detection/runs/2026-09-30_four_models_textrepair_control_v1/reports/control_comparison.json
