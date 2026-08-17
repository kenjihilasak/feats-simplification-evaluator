#!/bin/bash
#SBATCH --job-name=feats_package
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase2_cleaning/logs/package_%j.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase2_cleaning/logs/package_%j.err
#SBATCH --time=2:00:00
#SBATCH --nodes=1
#SBATCH --partition=nodes
#SBATCH --mem=8G
#SBATCH --cpus-per-task=1

set -euo pipefail

source /scratch/pjbd103/miniconda3/etc/profile.d/conda.sh
conda activate base

PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
RUN_ROOT=${1:?run root is required}
OUTPUT_DIR=${2:?output directory is required}
VERSION=${3:?version is required}
ARCHIVE_DATE=${4:?archive date is required}

cd "${PROJECT_ROOT}"
python phase2_cleaning/src/package_cleaned.py \
  --run-root "${RUN_ROOT}" \
  --output-dir "${OUTPUT_DIR}" \
  --version "${VERSION}" \
  --archive-date "${ARCHIVE_DATE}"
