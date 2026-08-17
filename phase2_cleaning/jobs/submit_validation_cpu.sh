#!/bin/bash
#SBATCH --job-name=feats_validate
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase2_cleaning/logs/validation_%j.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase2_cleaning/logs/validation_%j.err
#SBATCH --time=4:00:00
#SBATCH --nodes=1
#SBATCH --partition=nodes
#SBATCH --mem=16G
#SBATCH --cpus-per-task=1

set -euo pipefail

source /scratch/pjbd103/miniconda3/etc/profile.d/conda.sh
conda activate base

export PYTHONUNBUFFERED=1
PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
CONFIG=${1:-phase2_cleaning/configs/complexity_smp01_labse062_095_full_flat_v2.json}

cd "${PROJECT_ROOT}"
python phase2_cleaning/src/validate_run.py --config "${CONFIG}"
