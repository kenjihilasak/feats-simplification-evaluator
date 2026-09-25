#!/bin/bash
#SBATCH --job-name=feats_p6_retry2
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase6_degraded_corpus/logs/multi_axis_retry_v2_%j.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase6_degraded_corpus/logs/multi_axis_retry_v2_%j.err
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=4

set -euo pipefail

PROJECT_ROOT=/scratch/pjbd103/feats-simplification-evaluator
PYTHON_BIN=${PROJECT_ROOT}/.venv-phase3/bin/python
MODEL_REVISION=a09a35458c702b33eeacc393d103063234e8bc28
TOKENIZER_REVISION=4d795bc6b8ae8a1f2f447d2e83a57a4f8ebd711d
MODEL_PATH=${PROJECT_ROOT}/cache/huggingface/models--Qwen--Qwen2.5-7B-Instruct/snapshots/${MODEL_REVISION}
TOKENIZER_PATH=${PROJECT_ROOT}/cache/huggingface/models--hannah-khallaf--e2r-strategy-qwen2.5-7b-pairwise-qlora/snapshots/${TOKENIZER_REVISION}
RUN_DIR=${PROJECT_ROOT}/phase6_degraded_corpus/runs/multi_axis_en_v1

export PYTHONUNBUFFERED=1
export TOKENIZERS_PARALLELISM=false
export HF_HOME=${PROJECT_ROOT}/cache/huggingface
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

mkdir -p "${PROJECT_ROOT}/phase6_degraded_corpus/logs" "${RUN_DIR}/generation"
cd "${PROJECT_ROOT}"
"${PYTHON_BIN}" -m phase6_degraded_corpus.src.generation.generate_degradations \
  --manifest "${RUN_DIR}/generation/retry_failed_parse_manifest.jsonl" \
  --prompt-dir phase6_degraded_corpus/prompts/retry_v2 \
  --output "${RUN_DIR}/generation/retry_failed_parse_v2.jsonl" \
  --model-path "${MODEL_PATH}" \
  --tokenizer-path "${TOKENIZER_PATH}" \
  --revision "${MODEL_REVISION}" \
  --tokenizer-revision "${TOKENIZER_REVISION}" \
  --max-new-tokens 512
