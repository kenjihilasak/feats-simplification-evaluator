#!/bin/bash
#SBATCH --job-name=p3a_textrepair_report
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase3a_strategy_detection/logs/textrepair_report_%j.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase3a_strategy_detection/logs/textrepair_report_%j.err
#SBATCH --time=03:00:00
#SBATCH --partition=nodes
#SBATCH --mem=64G
#SBATCH --cpus-per-task=2
set -euo pipefail
ROOT=/scratch/pjbd103/feats-simplification-evaluator
cd "$ROOT"
.venv-phase3/bin/python phase3a_strategy_detection/src/report_textrepair_changes.py \
 --input-root phase2b_consolidation/runs/2026-09-29_base_textrepair_v1/data \
 --v1-root phase3a_strategy_detection/runs/2026-08-20_three_models_phase2b_full_v1 \
 --delta-root phase3a_strategy_detection/runs/2026-09-30_four_models_textrepair_delta_v1 \
 --old-candidates phase3a_strategy_detection/gold_candidates/2026-08-31_single_strategy_gemma_anchored_strict_v1 \
 --new-candidates phase3a_strategy_detection/gold_candidates/2026-09-30_single_strategy_gemma_anchored_strict_textrepair_v1 \
 --output phase3a_strategy_detection/runs/2026-09-30_four_models_textrepair_delta_v1/reports/label_change_report.md
