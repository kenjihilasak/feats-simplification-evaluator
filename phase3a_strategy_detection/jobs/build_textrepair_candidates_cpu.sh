#!/bin/bash
#SBATCH --job-name=p3a_textrepair_candidates
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase3a_strategy_detection/logs/textrepair_candidates_%j.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase3a_strategy_detection/logs/textrepair_candidates_%j.err
#SBATCH --time=04:00:00
#SBATCH --partition=nodes
#SBATCH --mem=64G
#SBATCH --cpus-per-task=2
set -euo pipefail
ROOT=/scratch/pjbd103/feats-simplification-evaluator
CFG=phase3a_strategy_detection/configs/gold_candidates/single_strategy_gemma_anchored_strict_textrepair_v1.json
cd "$ROOT"
.venv-phase3/bin/python phase3a_strategy_detection/src/prepare_textrepair_candidate_config.py --effective-root phase3a_strategy_detection/runs/2026-09-30_four_models_textrepair_effective_v1 --output "$CFG"
.venv-phase3/bin/python phase3a_strategy_detection/src/build_gemma_anchored_gold_candidates.py --config "$CFG"
