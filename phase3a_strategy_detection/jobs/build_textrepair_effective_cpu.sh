#!/bin/bash
#SBATCH --job-name=p3a_textrepair_effective
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase3a_strategy_detection/logs/textrepair_effective_%j.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase3a_strategy_detection/logs/textrepair_effective_%j.err
#SBATCH --time=03:00:00
#SBATCH --partition=nodes
#SBATCH --mem=64G
#SBATCH --cpus-per-task=2
set -euo pipefail
ROOT=/scratch/pjbd103/feats-simplification-evaluator
CFG=phase3a_strategy_detection/configs/experiments/four_models_textrepair_effective_v1.json
cd "$ROOT"
.venv-phase3/bin/python phase3a_strategy_detection/src/build_textrepair_effective.py \
 --input-root phase2b_consolidation/runs/2026-09-29_base_textrepair_v1/data \
 --v1-root phase3a_strategy_detection/runs/2026-08-20_three_models_phase2b_full_v1 \
 --delta-root phase3a_strategy_detection/runs/2026-09-30_four_models_textrepair_delta_v1 \
 --output-root phase3a_strategy_detection/runs/2026-09-30_four_models_textrepair_effective_v1 \
 --experiment-config "$CFG"
for model in xlmr_large_focal multilingual_e5_large_bce qwen2p5_7b_pairwise_qlora gemma3_12b_pairwise_qlora; do
 .venv-phase3/bin/python phase3a_strategy_detection/src/validate_run.py --config "$CFG" --model-alias "$model"
done
