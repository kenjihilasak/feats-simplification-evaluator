#!/bin/bash
#SBATCH --job-name=feats_cleaning
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase2_cleaning/logs/cleaning_%j.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase2_cleaning/logs/cleaning_%j.err
#SBATCH --time=2-00:00:00
#SBATCH --nodes=1
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --mem=96G
#SBATCH --cpus-per-task=8

set -euo pipefail

source /scratch/pjbd103/miniconda3/etc/profile.d/conda.sh
conda activate uncertainty-benchmark

export PYTHONUNBUFFERED=1
PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
CONFIG=${1:-phase2_cleaning/configs/complexity_smp01_labse062_095_full_flat_v2.json}

cd "${PROJECT_ROOT}"
python phase2_cleaning/src/run_cleaning.py --config "${CONFIG}" --stage all

