#!/usr/bin/env bash
#SBATCH --job-name=meaning-v2-eval
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=06:00:00
#SBATCH --output=phase7_feats_training/logs/%x-%j.out
#SBATCH --error=phase7_feats_training/logs/%x-%j.err
set -euo pipefail
cd /scratch/pjbd103/feats-simplification-evaluator
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv-phase6-vllm/bin/python phase7_feats_training/src/meaning_v2.py evaluate
