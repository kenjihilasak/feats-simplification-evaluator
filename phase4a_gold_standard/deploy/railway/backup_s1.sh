#!/usr/bin/env bash
set -euo pipefail
local_root=${1:-phase6_degraded_corpus/runs/annotation_v1/exports}
stamp=$(date -u +%Y%m%dT%H%M%SZ); local_dir="${local_root}/${stamp}"; remote="/tmp/s1-${stamp}"; service=${PHASE4A_RAILWAY_SERVICE:-phase4a-review}
mkdir -p "${local_dir}"
railway ssh --service "${service}" -- python -m phase4a_gold_standard.backend.s1_cli backup --output "${remote}.sqlite3"
railway ssh --service "${service}" -- python -m phase4a_gold_standard.backend.s1_cli export --output "${remote}-annotations.jsonl"
railway service files --service "${service}" download "${remote}.sqlite3" "${local_dir}/s1_validation_v1.sqlite3"
railway service files --service "${service}" download "${remote}-annotations.jsonl" "${local_dir}/annotations.jsonl"
echo "Downloaded S1 backup and export to ${local_dir}"
