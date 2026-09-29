#!/usr/bin/env bash
#SBATCH --job-name=phase6-mmi-checkers
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --output=phase6_degraded_corpus/logs/mmi_checkers_%j.out
#SBATCH --error=phase6_degraded_corpus/logs/mmi_checkers_%j.err

set -euo pipefail
project_root=/scratch/pjbd103/feats-simplification-evaluator
cd "$project_root"
source .venv-phase3/bin/activate
export HF_HOME="$project_root/cache/huggingface"
python -m phase6_degraded_corpus.src.selection.score_mmi_clean_inputs \
  --config phase6_degraded_corpus/configs/experiments/mmi_en_v2_pools.json \
  --device cuda
