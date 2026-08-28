#!/usr/bin/env bash
set -euo pipefail

local_dir=${1:-phase4a_gold_standard/backups}
stamp=$(date -u +%Y%m%dT%H%M%SZ)
remote_prefix="/backups/phase4a-${stamp}"

mkdir -p "${local_dir}"
railway ssh -- mkdir -p /data/backups
railway ssh -- python -m phase4a_gold_standard.backend backup \
  --output "/data${remote_prefix}.sqlite3"
railway ssh -- python -m phase4a_gold_standard.backend export \
  --format jsonl \
  --output "/data${remote_prefix}-annotations.jsonl"
railway ssh -- python -m phase4a_gold_standard.backend report \
  --output "/data${remote_prefix}-quality-report.json"

railway volume files download "${remote_prefix}.sqlite3" \
  "${local_dir}/phase4a-${stamp}.sqlite3"
railway volume files download "${remote_prefix}-annotations.jsonl" \
  "${local_dir}/phase4a-${stamp}-annotations.jsonl"
railway volume files download "${remote_prefix}-quality-report.json" \
  "${local_dir}/phase4a-${stamp}-quality-report.json"

echo "Downloaded backup set to ${local_dir}"
