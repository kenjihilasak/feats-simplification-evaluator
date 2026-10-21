#!/usr/bin/env bash
#SBATCH --job-name=feats-s1-gemini
#SBATCH --partition=nodes
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch/pjbd103/feats-simplification-evaluator/phase6_degraded_corpus/logs/s1_gemini_%j.out
#SBATCH --error=/scratch/pjbd103/feats-simplification-evaluator/phase6_degraded_corpus/logs/s1_gemini_%j.err
set -euo pipefail
project=/scratch/pjbd103/feats-simplification-evaluator
secret=/scratch/pjbd103/.secrets/gemini_api_key
[[ -s "${secret}" ]] || { echo "Missing Gemini key file" >&2; exit 2; }
[[ "$(stat -c %a "${secret}")" == "600" ]] || { echo "Gemini key must have mode 600" >&2; exit 2; }
cd "${project}"
export GEMINI_API_KEY_FILE="${secret}"
.venv-phase4a/bin/python -m phase6_degraded_corpus.src.annotation.prefill_with_llm \
  --input phase6_degraded_corpus/runs/annotation_v1/s1_items.jsonl \
  --input phase6_degraded_corpus/runs/annotation_v1/s1_controls.jsonl \
  --output phase6_degraded_corpus/runs/annotation_v1/s1_gemini_3p8_flash.jsonl \
  --delay 15
