#!/usr/bin/env bash
#SBATCH --job-name=axis-v1-eval
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --output=phase7_feats_training/logs/%x-%j.out
#SBATCH --error=phase7_feats_training/logs/%x-%j.err
# Usage: sbatch jobs/evaluate_axis_v1_gpu.sh MOD ILLOC
set -euo pipefail
cd /scratch/pjbd103/feats-simplification-evaluator/phase7_feats_training/src
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ../../.venv-phase6-vllm/bin/python run_evaluation.py --run-root ../runs/axis_validation_v1 --axes "$@" --reps 10000
