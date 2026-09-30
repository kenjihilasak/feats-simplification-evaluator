# Phase 4a — Gold-standard human validation

Phase 4a turns the strict Gemma-anchored single-strategy candidates from Phase 3a into
a human-validated multilingual evaluation set. It is a standalone component:
the historical HTML under `/scratch/pjbd103/Align-and-Shine-dev` informed the
visual layout only. Phase 4a does not import its code, assets, or runtime
packages.

## Status

- Primary pool built and validated: **167,238** tasks in 12 languages.
- One clean canonical CSV and one spreadsheet-safe CSV are available per
  language.
- Phase 3b v2 SimAlign links join all 167,238 candidates.
- Stanza UD syntax enrichment, materialization, private review server, audit
  trail, deterministic exports, and reports are implemented.
- Human review has not started, so this pool is a **gold candidate**, not yet a
  gold standard.
- Four reviewers will each receive a different language. The exact four
  account-to-language assignments remain deployment configuration; the
  priority order is `en, es, it, ru, ar`.
- Sparse-language expansion, especially for Arabic, remains a separate
  supplemental pool and never changes the 167,238-task primary denominator.

## Inputs

| Input | Role |
|---|---|
| Phase 3a `2026-08-31_single_strategy_gemma_anchored_strict_v1` | Gemma singleton confirmed by an exact singleton from at least one of E5, Qwen, or XLM-R |
| Phase 3b `2026-08-23_simalign_xlmr_large_itermax_full_v2` | Exact tokens, offsets, orthographic parents, and SimAlign links |
| Stanza 1.10.1 / resources 1.10.0 | Pretokenized UD lemma, POS, features, heads, and dependency relations |

## Primary pool

| Language | Tasks |
|---|---:|
| ar | 20 |
| ca | 149 |
| de | 48 |
| en | 66,768 |
| es | 375 |
| fr | 35,404 |
| it | 26,771 |
| ja | 20,181 |
| pt-BR | 250 |
| ru | 17,050 |
| sl | 18 |
| ur | 204 |
| **Total** | **167,238** |

Generated files are local and intentionally excluded from Git:

```text
phase4a_gold_standard/data/2026-08-31_gemma_anchored_strict_v2/
├── data/<language>/annotation_pool.csv
├── data/<language>/annotation_pool.spreadsheet_safe.csv
├── payloads/<language>/annotation_tasks.jsonl
├── POOL_MANIFEST.csv
├── pool_manifest.json
└── reports/{summary.json,validation.json}
```

The canonical CSV preserves exact text and has these human-oriented fields:
`review_task_id`, `queue_rank`, `canonical_pair_id`, `language`,
`sources`, `corpora`, `original`, `simplification`, strategy code and
label, the lowercase E5/Qwen/XLM-R exact-singleton confirmation columns, Gemma as the required anchor, `majority_votes`,
`quality_tier`, and `pool_type`. The spreadsheet-safe copy neutralizes
formula prefixes for office software; use the canonical CSV for computation.

Build or revalidate the full pool:

```bash
.venv-phase4a/bin/python phase4a_gold_standard/src/prepare_gemma_anchored_pool.py \
  --config phase4a_gold_standard/configs/annotation_pool_gemma_anchored_strict_v2.json

.venv-phase4a/bin/python phase4a_gold_standard/src/prepare_gemma_anchored_pool.py \
  --validate-only phase4a_gold_standard/data/2026-08-31_gemma_anchored_strict_v2
```

## Syntax for complex languages

All languages use Stanza UD in strict pretokenized mode so Phase 3b token
indices remain unchanged. There is no English-model fallback.

| Language | Stanza treebank/package |
|---|---|
| ar | PADT / `padt_nocharlm` |
| ca | AnCora / `ancora_nocharlm` |
| de, en, es, fr, it | `combined_nocharlm` |
| ja | GSD / `gsd_nocharlm` |
| pt-BR | Portuguese Bosque / `bosque_nocharlm` |
| ru | SynTagRus / `syntagrus_nocharlm` |
| sl | SSJ / `ssj_nocharlm` |
| ur | UDTB / `udtb_nocharlm` |

Set up the environment, download pinned models, and submit one GPU job per
language:

```bash
phase4a_gold_standard/jobs/setup_environment.sh
sbatch phase4a_gold_standard/jobs/submit_download_stanza_cpu.sh
# Submit after the model-download job succeeds:
sbatch phase4a_gold_standard/jobs/submit_stanza_syntax_gpu.sh
```

Each syntax job fails on parser/token-contract errors and then materializes an
import-ready JSONL for only its language under
`runs/materialized/2026-08-31_stanza_ud_gemma_anchored_strict_v2/<language>/payloads/`.

## Private review UI

The reviewer sees the corpus source, candidate strategy, dependency trees,
tokens, and SimAlign links. Model votes remain hidden while the judgment is
being made and are revealed only after a successful submit.

The queue supports multi-select source and model filters. Sources use OR
semantics; all selected models must support the candidate strategy. Claims made
with model filters are recorded as `unblinded_model_filter` in the audit log.

A reviewer:

1. optionally filters the next queue by source and supporting model;
2. chooses `correct`, `incorrect`, or `uncertain`;
3. selects evidence tokens and reviews alignment links;
4. submits, then sees model agreement;
5. may reopen a prior submission from **Previous**, preserving its original
   revision and creating a new editable version.

Correct and determinate corrected strategies require source evidence; every
strategy except `OMIT` also requires target evidence. See
[ANNOTATION_GUIDE.md](ANNOTATION_GUIDE.md) for the protocol.

The UI supports RTL layout for Arabic/Urdu, preserves Japanese token display,
autosaves drafts, renews task leases, detects stale versions, and records every
claim, save, submission, defer-for-later action, login, and administrative action.

## Server operation

For the shared external-review campaign, deploy one Railway service with one
persistent volume. The complete setup, language import, account isolation,
backup procedure, and Windows fallback are documented in the
[Railway deployment runbook](deploy/railway/README.md).

Use a long random session secret and HTTPS in the private deployment:

```bash
export PHASE4A_DATABASE=/secure/path/gemma_anchored_strict_v2.sqlite3
export PHASE4A_CAMPAIGN_ID=gemma-anchored-strict-v2
export PHASE4A_SESSION_SECRET='replace-with-a-long-random-secret'
export PHASE4A_COOKIE_SECURE=1

.venv-phase4a/bin/python -m phase4a_gold_standard.backend init
.venv-phase4a/bin/python -m phase4a_gold_standard.backend create-user \
  --username reviewer-en --display-name 'English reviewer' \
  --role reviewer --language en
.venv-phase4a/bin/python -m phase4a_gold_standard.backend import-tasks \
  phase4a_gold_standard/runs/materialized/2026-08-31_stanza_ud_gemma_anchored_strict_v2/en/payloads/en/annotation_tasks.jsonl
.venv-phase4a/bin/python -m phase4a_gold_standard.backend serve \
  --host 127.0.0.1 --port 8000
```

Create four nominal reviewer accounts, each with exactly one distinct
`--language`. Put the service behind the institution's authenticated HTTPS
reverse proxy; do not expose SQLite or bind the development server directly to
the public internet.

Administrative outputs:

```bash
.venv-phase4a/bin/python -m phase4a_gold_standard.backend export \
  --format jsonl --output phase4a_gold_standard/exports/annotations.jsonl
.venv-phase4a/bin/python -m phase4a_gold_standard.backend report \
  --output phase4a_gold_standard/exports/quality_report.json
```

Reports include strategy correctness overall/by language/source/strategy,
selected words with lemma/POS/dependency metadata, SimAlign acceptance among
judged links, link-judgment coverage, and human-added links. Drafts and deferred tasks are reported as progress but do not enter linguistic
quality denominators. Deferred tasks remain eligible for later review.

## Verification

```bash
.venv-phase4a/bin/python -m pytest phase4a_gold_standard/tests -q
bash -n phase4a_gold_standard/jobs/*.sh
```

The manual browser flow passed on 2026-08-28. Its export assertions and the
separate alignment-acceptance and coverage denominators are recorded in
[the manual UI smoke-test report](reports/manual_ui_smoke_2026-08-28.md).

The tests cover deterministic pool construction, exact hashes and offsets,
spreadsheet safety, pretokenized syntax/materialization, blinded review,
required evidence, immutable submission, enriched exports, quality reports,
and large batched imports.
