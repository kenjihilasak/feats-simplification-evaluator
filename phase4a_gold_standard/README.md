# Phase 4a — Gold-standard human validation

Phase 4a turns the single-strategy majority-vote candidates from Phase 3a into
a human-validated multilingual evaluation set. It is a standalone component:
the historical HTML under `/scratch/pjbd103/Align-and-Shine-dev` informed the
visual layout only. Phase 4a does not import its code, assets, or runtime
packages.

## Status

- Primary pool built and validated: **271,395** tasks in 12 languages.
- One clean canonical CSV and one spreadsheet-safe CSV are available per
  language.
- Phase 3b v2 SimAlign links join all 271,395 candidates.
- Stanza UD syntax enrichment, materialization, private review server, audit
  trail, deterministic exports, and reports are implemented.
- Human review has not started, so this pool is a **gold candidate**, not yet a
  gold standard.
- Four reviewers will each receive a different language. The exact four
  account-to-language assignments remain deployment configuration; the
  priority order is `en, es, it, ru, ar`.
- Sparse-language expansion, especially for Arabic, remains a separate
  supplemental pool and never changes the 271,395-task primary denominator.

## Inputs

| Input | Role |
|---|---|
| Phase 3a `2026-08-26_single_strategy_majority_vote_v1` | One candidate strategy supported by at least two of E5, Qwen, and XLM-R |
| Phase 3b `2026-08-23_simalign_xlmr_large_itermax_full_v2` | Exact tokens, offsets, orthographic parents, and SimAlign links |
| Stanza 1.10.1 / resources 1.10.0 | Pretokenized UD lemma, POS, features, heads, and dependency relations |

## Primary pool

| Language | Tasks |
|---|---:|
| ar | 1 |
| ca | 244 |
| de | 94 |
| en | 128,114 |
| es | 267 |
| fr | 49,490 |
| it | 40,801 |
| ja | 26,569 |
| pt-BR | 176 |
| ru | 25,462 |
| sl | 32 |
| ur | 145 |
| **Total** | **271,395** |

Generated files are local and intentionally excluded from Git:

```text
phase4a_gold_standard/data/2026-08-27_single_strategy_full_v1/
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
label, the three lowercase `yes/no` model columns, `majority_votes`,
`quality_tier`, and `pool_type`. The spreadsheet-safe copy neutralizes
formula prefixes for office software; use the canonical CSV for computation.

Build or revalidate the full pool:

```bash
.venv-phase4a/bin/python phase4a_gold_standard/src/prepare_annotation_pool.py \
  --config phase4a_gold_standard/configs/annotation_pool_full_v1.json

.venv-phase4a/bin/python phase4a_gold_standard/src/prepare_annotation_pool.py \
  --validate-only phase4a_gold_standard/data/2026-08-27_single_strategy_full_v1
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
`runs/materialized/2026-08-27_stanza_ud_full_v1/<language>/payloads/`.

## Private review UI

The reviewer sees the candidate strategy, original dependency tree above the
source tokens, SimAlign links between both sentences, target tokens, and the
mirrored target dependency tree below. Model identities, individual votes,
majority size, and quality tier are hidden to prevent anchoring.

A reviewer:

1. chooses `correct`, `incorrect`, or `uncertain`;
2. selects the strategy-specific source and target evidence tokens;
3. marks visible SimAlign links valid/invalid and may add missing links;
4. saves a draft or submits the immutable final judgment.

Correct and determinate corrected strategies require source evidence; every
strategy except `OMIT` also requires target evidence. See
[ANNOTATION_GUIDE.md](ANNOTATION_GUIDE.md) for the protocol.

The UI supports RTL layout for Arabic/Urdu, preserves Japanese token display,
autosaves drafts, renews task leases, detects stale versions, and records every
claim, save, submission, skip, login, and administrative action.

## Server operation

For the shared external-review campaign, deploy one Railway service with one
persistent volume. The complete setup, language import, account isolation,
backup procedure, and Windows fallback are documented in the
[Railway deployment runbook](deploy/railway/README.md).

Use a long random session secret and HTTPS in the private deployment:

```bash
export PHASE4A_DATABASE=/secure/path/phase4a.sqlite3
export PHASE4A_SESSION_SECRET='replace-with-a-long-random-secret'
export PHASE4A_COOKIE_SECURE=1

.venv-phase4a/bin/python -m phase4a_gold_standard.backend init
.venv-phase4a/bin/python -m phase4a_gold_standard.backend create-user \
  --username reviewer-en --display-name 'English reviewer' \
  --role reviewer --language en
.venv-phase4a/bin/python -m phase4a_gold_standard.backend import-tasks \
  phase4a_gold_standard/runs/materialized/2026-08-27_stanza_ud_full_v1/en/payloads/en/annotation_tasks.jsonl
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
judged links, link-judgment coverage, and human-added links. Drafts/skips are
reported as progress but do not enter linguistic quality denominators.

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
