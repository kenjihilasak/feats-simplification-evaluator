#!/usr/bin/env bash
#SBATCH --job-name=phase6-mmi-full
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=phase6_degraded_corpus/logs/mmi_full_%A_%a.out
#SBATCH --error=phase6_degraded_corpus/logs/mmi_full_%A_%a.err
# Usage: sbatch --array=0-N phase6_degraded_corpus/jobs/submit_mmi_full_generate_gpu.sh
set -euo pipefail
project_root=/scratch/pjbd103/feats-simplification-evaluator
cd "$project_root"
run=phase6_degraded_corpus/runs/mmi_en_v2_full
manifest="$run/shards/shard_manifest.json"
index=${SLURM_ARRAY_TASK_ID:?submit as a Slurm array}
config_id=$(.venv-phase6-vllm/bin/python -c 'import json,sys; print(json.load(open(sys.argv[1]))[int(sys.argv[2])]["config_id"])' "$manifest" "$index")
plan=$(.venv-phase6-vllm/bin/python -c 'import json,sys; print(json.load(open(sys.argv[1]))[int(sys.argv[2])]["plan"])' "$manifest" "$index")
output=$(.venv-phase6-vllm/bin/python -c 'import json,sys; print(json.load(open(sys.argv[1]))[int(sys.argv[2])]["output"])' "$manifest" "$index")
mkdir -p "$(dirname "$output")" phase6_degraded_corpus/logs
if .venv-phase6-vllm/bin/python -m phase6_degraded_corpus.src.generation.prepare_mmi_full_shards validate --plan "$plan" --output "$output"; then
  echo "validated existing output: $output"
  exit 0
fi
export HF_HOME="$project_root/cache/huggingface" HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false VLLM_WORKER_MULTIPROC_METHOD=spawn
.venv-phase6-vllm/bin/python -m phase6_degraded_corpus.src.generation.generate_mmi_v2 \
  --plan "$plan" \
  --config phase6_degraded_corpus/configs/experiments/mmi_en_v2_generation.json \
  --config-id "$config_id" \
  --output "$output"
.venv-phase6-vllm/bin/python -m phase6_degraded_corpus.src.generation.prepare_mmi_full_shards validate --plan "$plan" --output "$output"
