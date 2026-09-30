#!/usr/bin/env bash
#SBATCH --job-name=axis-v1-train
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=24:00:00
#SBATCH --output=phase7_feats_training/logs/%x-%A_%a.out
#SBATCH --error=phase7_feats_training/logs/%x-%A_%a.err
#SBATCH --array=0-35
set -euo pipefail
cd "$(dirname "$0")/../.."
axes=(MEANING MOD ILLOC)
models=(xlm_roberta_large deberta_v3_base)
lrs=(1e-5 2e-5)
seeds=(17 29 43)
index=${SLURM_ARRAY_TASK_ID:?submit as an array}
seed=${seeds[$((index % 3))]}
index=$((index / 3))
lr=${lrs[$((index % 2))]}
index=$((index / 2))
model=${models[$((index % 2))]}
axis=${axes[$((index / 2))]}
TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 python phase7_feats_training/src/train_axis_model.py \
  --model-config "phase7_feats_training/configs/models/${model}.json" \
  --dataset phase7_feats_training/runs/axis_validation_v1/data/dataset.jsonl \
  --output-dir "phase7_feats_training/runs/axis_validation_v1/training/${axis}/${model}/lr_${lr}/seed_${seed}" \
  --axis "$axis" --learning-rate "$lr" --seed "$seed"
