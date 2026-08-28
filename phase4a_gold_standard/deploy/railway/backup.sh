#!/usr/bin/env bash
set -euo pipefail

local_dir=${1:-phase4a_gold_standard/backups}
stamp=$(date -u +%Y%m%dT%H%M%SZ)
remote_prefix="/tmp/phase4a-${stamp}"
service=${PHASE4A_RAILWAY_SERVICE:-phase4a-review}

mkdir -p "${local_dir}"
railway ssh -- python -m phase4a_gold_standard.backend backup \
  --output "${remote_prefix}.sqlite3"
railway ssh -- python -m phase4a_gold_standard.backend export \
  --format jsonl \
  --output "${remote_prefix}-annotations.jsonl"
railway ssh -- python -m phase4a_gold_standard.backend report \
  --output "${remote_prefix}-quality-report.json"

railway service files --service "${service}" download "${remote_prefix}.sqlite3" \
  "${local_dir}/phase4a-${stamp}.sqlite3"
railway service files --service "${service}" download "${remote_prefix}-annotations.jsonl" \
  "${local_dir}/phase4a-${stamp}-annotations.jsonl"
railway service files --service "${service}" download "${remote_prefix}-quality-report.json" \
  "${local_dir}/phase4a-${stamp}-quality-report.json"

echo "Downloaded backup set to ${local_dir}"
