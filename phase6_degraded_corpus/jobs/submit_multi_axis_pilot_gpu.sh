#!/bin/bash
#SBATCH --job-name=feats_p6_axes
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase6_degraded_corpus/logs/multi_axis_pilot_%A_%a.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase6_degraded_corpus/logs/multi_axis_pilot_%A_%a.err
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=4
#SBATCH --array=0-5

set -euo pipefail

PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
PYTHON_BIN=${PROJECT_ROOT}/.venv-phase3/bin/python
MODEL_REVISION=a09a35458c702b33eeacc393d103063234e8bc28
TOKENIZER_REVISION=4d795bc6b8ae8a1f2f447d2e83a57a4f8ebd711d
MODEL_PATH=${PROJECT_ROOT}/cache/huggingface/models--Qwen--Qwen2.5-7B-Instruct/snapshots/${MODEL_REVISION}
TOKENIZER_PATH=${PROJECT_ROOT}/cache/huggingface/models--hannah-khallaf--e2r-strategy-qwen2.5-7b-pairwise-qlora/snapshots/${TOKENIZER_REVISION}
RUN_DIR=${PROJECT_ROOT}/phase6_degraded_corpus/runs/multi_axis_en_v1

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Missing ${PYTHON_BIN}" >&2
  exit 1
fi

export PYTHONUNBUFFERED=1
export TOKENIZERS_PARALLELISM=false
export HF_HOME=${PROJECT_ROOT}/cache/huggingface
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

mkdir -p "${PROJECT_ROOT}/phase6_degraded_corpus/logs" "${RUN_DIR}/generation"
cd "${PROJECT_ROOT}"
nvidia-smi
"${PYTHON_BIN}" -m phase6_degraded_corpus.src.generation.generate_degradations \
  --manifest "${RUN_DIR}/assignment/pilot_manifest.jsonl" \
  --prompt-dir phase6_degraded_corpus/prompts \
  --output "${RUN_DIR}/generation/pilot_shard_${SLURM_ARRAY_TASK_ID}.jsonl" \
  --model-path "${MODEL_PATH}" \
  --tokenizer-path "${TOKENIZER_PATH}" \
  --revision "${MODEL_REVISION}" \
  --tokenizer-revision "${TOKENIZER_REVISION}" \
  --num-shards 6 \
  --shard-index "${SLURM_ARRAY_TASK_ID}" \
  --max-new-tokens 256
