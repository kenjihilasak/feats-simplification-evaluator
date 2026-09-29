#!/usr/bin/env bash
#SBATCH --job-name=phase6-mmi-gen
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=phase6_degraded_corpus/logs/mmi_gen_%x_%j.out
#SBATCH --error=phase6_degraded_corpus/logs/mmi_gen_%x_%j.err
# Usage: sbatch --job-name=mmi-C1 jobs/submit_mmi_v2_generate_gpu.sh <config_id> <split>
set -euo pipefail
project_root=/scratch/pjbd103/feats-simplification-evaluator
cd "$project_root"
config_id=$1; split=${2:-dev}
run=phase6_degraded_corpus/runs/mmi_en_v2
export HF_HOME="$project_root/cache/huggingface" HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false VLLM_WORKER_MULTIPROC_METHOD=spawn
.venv-phase6-vllm/bin/python -m phase6_degraded_corpus.src.generation.generate_mmi_v2 \
  --plan "$run/plans/${split}_plan.jsonl" \
  --config phase6_degraded_corpus/configs/experiments/mmi_en_v2_generation.json \
  --config-id "$config_id" \
  --output "$run/generations/${split}/${config_id}.jsonl"
