#!/usr/bin/env bash
#SBATCH --job-name=phase6-mmi-v3
#SBATCH --partition=gpu
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=phase6_degraded_corpus/logs/mmi_v3_%x_%j.out
#SBATCH --error=phase6_degraded_corpus/logs/mmi_v3_%x_%j.err
# Usage: sbatch jobs/submit_mmi_v3_generate_gpu.sh MOD|ILLOC
set -euo pipefail
project_root=/scratch/pjbd103/feats-simplification-evaluator
cd "$project_root"
axis=${1:?usage: submit_mmi_v3_generate_gpu.sh MOD|ILLOC}
case "$axis" in
  MOD) config_id=MOD_C2; plan=mod_review_plan.jsonl; output=mod_c2.jsonl ;;
  ILLOC) config_id=ILLOC_C1; plan=illoc_review_plan.jsonl; output=illoc_c1.jsonl ;;
  *) echo "axis must be MOD or ILLOC" >&2; exit 2 ;;
esac
run=phase6_degraded_corpus/runs/mmi_en_v3
export HF_HOME="$project_root/cache/huggingface" HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false VLLM_WORKER_MULTIPROC_METHOD=spawn
.venv-phase6-vllm/bin/python -m phase6_degraded_corpus.src.generation.generate_mmi_v2 \
  --plan "$run/plans/$plan" \
  --config phase6_degraded_corpus/configs/experiments/mmi_en_v3_generation.json \
  --config-id "$config_id" \
  --output "$run/generations/$output"
