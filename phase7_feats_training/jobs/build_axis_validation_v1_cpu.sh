#!/usr/bin/env bash
#SBATCH --job-name=axis-v1-build
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=phase7_feats_training/logs/%x-%j.out
#SBATCH --error=phase7_feats_training/logs/%x-%j.err
set -euo pipefail
cd "$(dirname "$0")/../.."
python phase7_feats_training/src/build_axis_dataset.py \
  --config phase7_feats_training/configs/experiments/axis_validation_v1.json \
  --output-root phase7_feats_training/runs/axis_validation_v1/data
