#!/usr/bin/env bash
#SBATCH --job-name=phase6-mmi-v3-score
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=phase6_degraded_corpus/logs/mmi_v3_score_%j.out
#SBATCH --error=phase6_degraded_corpus/logs/mmi_v3_score_%j.err
# Usage (from the project root): sbatch phase6_degraded_corpus/jobs/submit_mmi_v3_score_gpu.sh
set -euo pipefail
project_root=/scratch/pjbd103/feats-simplification-evaluator
cd "$project_root"
run=phase6_degraded_corpus/runs/mmi_en_v3
mkdir -p "$run/scored"
export HF_HOME="$project_root/cache/huggingface" HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false
for pair in "mod_c2:mod_review_plan" "illoc_c1:illoc_review_plan"; do
  name=${pair%%:*}; plan=${pair##*:}
  .venv-phase6-vllm/bin/python -m phase6_degraded_corpus.src.evaluation.score_mmi_candidates \
    --generations "$run/generations/$name.jsonl" --plan "$run/plans/$plan.jsonl" \
    --pools-config phase6_degraded_corpus/configs/experiments/mmi_en_v3_pools.json \
    --output "$run/scored/$name.jsonl" --device cuda
done
