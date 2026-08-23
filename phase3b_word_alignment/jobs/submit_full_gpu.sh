#!/bin/bash
#SBATCH --job-name=feats_p3b_v2
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase3b_word_alignment/logs/full_v2_%A_%a.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase3b_word_alignment/logs/full_v2_%A_%a.err
#SBATCH --time=1-00:00:00
#SBATCH --nodes=1
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --array=0-11

set -euo pipefail

PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
PYTHON_BIN=/scratch/pjbd103/miniconda3/envs/SimAlign/bin/python
CONFIG=${1:-phase3b_word_alignment/configs/simalign_xlmr_large_itermax_full_v2.json}
LANGUAGES=(ar ca de en es fr it ja pt-BR ru sl ur)
LANGUAGE=${LANGUAGES[${SLURM_ARRAY_TASK_ID}]}

export PYTHONUNBUFFERED=1
export TOKENIZERS_PARALLELISM=false
export HF_HOME=/users/pjbd103/.cache/huggingface
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
export CAMELTOOLS_DATA=${PROJECT_ROOT}/phase3b_word_alignment/cache/camel_tools
export STANZA_RESOURCES_DIR=${PROJECT_ROOT}/phase3b_word_alignment/cache/stanza

cd "${PROJECT_ROOT}"
nvidia-smi
"${PYTHON_BIN}" phase3b_word_alignment/src/run_word_alignment.py \
  --config "${CONFIG}" \
  --language "${LANGUAGE}" \
  --device cuda \
  --resume
"${PYTHON_BIN}" phase3b_word_alignment/src/validate_run.py \
  --config "${CONFIG}" \
  --language "${LANGUAGE}"
