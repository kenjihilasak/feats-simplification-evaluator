#!/usr/bin/env bash
#SBATCH --job-name=phase6-mmi-judge
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=phase6_degraded_corpus/logs/mmi_judge_%j.out
#SBATCH --error=phase6_degraded_corpus/logs/mmi_judge_%j.err
# Usage: sbatch jobs/submit_mmi_v2_judge_gpu.sh <calibrate|judge> <judge_config_id> [scored files...]
set -euo pipefail
project_root=/scratch/pjbd103/feats-simplification-evaluator
cd "$project_root"
mode=$1; judge=$2; shift 2
export HF_HOME="$project_root/cache/huggingface" HF_HUB_OFFLINE=1 VLLM_WORKER_MULTIPROC_METHOD=spawn
.venv-phase6-vllm/bin/python -m phase6_degraded_corpus.src.evaluation.judge_mmi \
  --mode "$mode" --judge-config-id "$judge" \
  --generation-config phase6_degraded_corpus/configs/experiments/mmi_en_v2_generation.json \
  --output-dir phase6_degraded_corpus/runs/mmi_en_v2/judge ${1:+--scored "$@"}
