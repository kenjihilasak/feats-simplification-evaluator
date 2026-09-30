#!/usr/bin/env bash
#SBATCH --job-name=phase6-mmi-score
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=phase6_degraded_corpus/logs/mmi_full_score_%A_%a.out
#SBATCH --error=phase6_degraded_corpus/logs/mmi_full_score_%A_%a.err
# Usage: sbatch --array=0-N phase6_degraded_corpus/jobs/submit_mmi_full_score_gpu.sh
set -euo pipefail
project_root=/scratch/pjbd103/feats-simplification-evaluator
cd "$project_root"
run=phase6_degraded_corpus/runs/mmi_en_v2_full
manifest="$run/shards/shard_manifest.json"
index=${SLURM_ARRAY_TASK_ID:?submit as a Slurm array}
plan=$(.venv-phase6-vllm/bin/python -c 'import json,sys; print(json.load(open(sys.argv[1]))[int(sys.argv[2])]["plan"])' "$manifest" "$index")
generation=$(.venv-phase6-vllm/bin/python -c 'import json,sys; print(json.load(open(sys.argv[1]))[int(sys.argv[2])]["output"])' "$manifest" "$index")
name=$(basename "$generation")
output="$run/scored/$name"
mkdir -p "$run/scored" phase6_degraded_corpus/logs
if [[ -s "$output" ]] && [[ $(wc -l < "$output") -eq $(wc -l < "$plan") ]]; then
  echo "existing scored shard has expected row count: $output"
  exit 0
fi
export HF_HOME="$project_root/cache/huggingface" HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false
.venv-phase6-vllm/bin/python -m phase6_degraded_corpus.src.evaluation.score_mmi_candidates \
  --generations "$generation" \
  --plan "$plan" \
  --pools-config phase6_degraded_corpus/configs/experiments/mmi_en_v2_pools.json \
  --output "$output" \
  --device cuda
[[ $(wc -l < "$output") -eq $(wc -l < "$plan") ]]
