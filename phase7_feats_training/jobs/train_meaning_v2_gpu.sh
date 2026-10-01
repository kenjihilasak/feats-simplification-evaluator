#!/usr/bin/env bash
#SBATCH --job-name=meaning-v2
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=40G
#SBATCH --time=06:00:00
#SBATCH --output=phase7_feats_training/logs/%x-%A_%a.out
#SBATCH --error=phase7_feats_training/logs/%x-%A_%a.err
#SBATCH --array=0-23
# 4 arms x 2 learning rates x 3 seeds, DeBERTa-v3-base (MEANING recipe v2).
set -euo pipefail
cd /scratch/pjbd103/feats-simplification-evaluator
arms=(A A_all B C); lrs=(1e-5 2e-5); seeds=(17 29 43)
i=${SLURM_ARRAY_TASK_ID:?}
seed=${seeds[$((i % 3))]}; i=$((i / 3)); lr=${lrs[$((i % 2))]}; arm=${arms[$((i / 2))]}
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv-phase6-vllm/bin/python phase7_feats_training/src/meaning_v2.py train \
  --arm "$arm" --lr "$lr" --seed "$seed"
