#!/usr/bin/env bash
#SBATCH --job-name=phase6-mmi-C0
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=phase6_degraded_corpus/logs/mmi_gen_C0_%j.out
#SBATCH --error=phase6_degraded_corpus/logs/mmi_gen_C0_%j.err
# C0 = the frozen v1 pipeline (4-bit NF4, greedy, v1 prompts, adapter-repo tokenizer) on the v2 split.
# Usage: sbatch jobs/submit_mmi_v2_c0_gpu.sh <split> [all|meaning|mod_illoc]
set -euo pipefail
project_root=/scratch/pjbd103/feats-simplification-evaluator
cd "$project_root"
split=${1:-dev}; part=${2:-all}
run=phase6_degraded_corpus/runs/mmi_en_v2
out=$run/generations/$split/C0_raw; mkdir -p "$out"
MODEL_REVISION=a09a35458c702b33eeacc393d103063234e8bc28
TOKENIZER_REVISION=4d795bc6b8ae8a1f2f447d2e83a57a4f8ebd711d
MODEL_PATH=$project_root/cache/huggingface/models--Qwen--Qwen2.5-7B-Instruct/snapshots/$MODEL_REVISION
TOKENIZER_PATH=$project_root/cache/huggingface/models--hannah-khallaf--e2r-strategy-qwen2.5-7b-pairwise-qlora/snapshots/$TOKENIZER_REVISION
export HF_HOME="$project_root/cache/huggingface" HF_HUB_OFFLINE=1 PYTHONUNBUFFERED=1
PY=.venv-phase3/bin/python
if [[ $part != mod_illoc ]]; then rm -f "$out/meaning.jsonl"
$PY -m phase6_degraded_corpus.src.generation.generate_meaning_degradations \
  --plan "$run/c0/$split/meaning_plan.jsonl" --prompt phase6_degraded_corpus/prompts/meaning_severe_v2.json \
  --output "$out/meaning.jsonl" --model-path "$MODEL_PATH" --tokenizer-path "$TOKENIZER_PATH" \
  --tokenizer-revision "$TOKENIZER_REVISION" --revision "$MODEL_REVISION"
fi
if [[ $part != meaning ]]; then
$PY -m phase6_degraded_corpus.src.generation.generate_degradations \
  --manifest "$run/c0/$split/multi_axis_manifest.jsonl" --prompt-dir phase6_degraded_corpus/prompts \
  --output "$out/mod_illoc.jsonl" --model-path "$MODEL_PATH" --tokenizer-path "$TOKENIZER_PATH" \
  --revision "$MODEL_REVISION" --tokenizer-revision "$TOKENIZER_REVISION"
fi
