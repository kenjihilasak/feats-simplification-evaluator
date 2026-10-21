# Railway deployment for Phase 4a

This is the recommended shared deployment for the multilingual human-review
campaign. Railway hosts one FastAPI service and one persistent volume. Reviewers
need only the generated HTTPS URL and their individual Phase 4a credentials;
they do not need AIRE, GitHub, Python, or access to any dataset files.

## Active deployment

- Project: `feats-phase4a-gold-review`
- Service: `phase4a-review`
- URL: <https://phase4a-review-production.up.railway.app>
- Region/replicas: EU West, one replica
- Loaded pool (2026-08-28): 271,395 materialized tasks across 12 languages

Credentials, payloads, the live database, and downloaded backups remain private.

## Runtime architecture

```text
Reviewer browser
    -> Railway HTTPS domain
    -> Phase 4a FastAPI service (one replica)
    -> /data/gemma_anchored_strict_v2.sqlite3 on the attached volume
```

The Docker image contains application code only. Materialized language payloads,
the live database, exports, backups, passwords, and session secrets stay outside
Git.

## 1. Create the Railway service

In the Railway dashboard:

1. Create a new project and choose **Deploy from GitHub repo**.
2. Authorize Railway for the private
   `kenjihilasak/feats-simplification-evaluator` repository.
3. Set the service **Root Directory** to `/phase4a_gold_standard`.
4. Confirm that Railway detects `phase4a_gold_standard/Dockerfile`.
5. Select a single EU West replica. Do not horizontally scale SQLite.
6. Attach a persistent volume with mount path `/data`.
7. Add these service variables:

```text
PHASE4A_DATABASE=/data/gemma_anchored_strict_v2.sqlite3
S1_DATABASE=/data/s1_validation_v1.sqlite3
PHASE4A_CAMPAIGN_ID=gemma-anchored-strict-v2
PHASE4A_SESSION_SECRET=<at-least-32-random-characters>
PHASE4A_COOKIE_SECURE=1
PHASE4A_LANGUAGE_PRIORITY=en,es,it,ru,ar
```

Generate the secret on AIRE without printing it into a repository file:

```bash
openssl rand -hex 48
```

Railway supplies `PORT`; do not define it manually. The container refuses to
start on Railway without the `/data` volume or a sufficiently long session
secret.

In the service settings:

- set the healthcheck path to `/api/health`;
- set the restart policy to **Always**;
- keep exactly one replica;
- generate a Railway public domain.

The UI will then be available at a URL similar to
`https://<service>.up.railway.app`.

## 2. Link the Railway CLI on AIRE

Install and authenticate the CLI:

```bash
npm install -g @railway/cli
railway login --browserless
```

The browserless command prints a URL and code. Open the URL on your laptop,
approve it with the paid Railway account, and return to the AIRE terminal.

From the repository root:

```bash
cd /scratch/pjbd103/feats-simplification-evaluator
railway link
railway service
railway status
```

Select the project, production environment, Phase 4a service, and its attached
volume when prompted.

## 3. Upload and import one language

Only upload syntax-materialized payloads. For Spanish:

```bash
test -s phase4a_gold_standard/runs/materialized/2026-08-31_stanza_ud_gemma_anchored_strict_v2/es/payloads/es/annotation_tasks.jsonl

phase4a_gold_standard/deploy/railway/upload_language.sh \
  es \
  phase4a_gold_standard/runs/materialized/2026-08-31_stanza_ud_gemma_anchored_strict_v2/es/payloads/es/annotation_tasks.jsonl
```

The script:

1. uploads the JSONL to temporary storage in the running Railway service;
2. imports it into the SQLite campaign on the persistent volume;
3. prints administrative progress.

Importing the same payload again is idempotent: unchanged tasks are not
duplicated. Repeat the command for each approved language only after its
materialized payload has passed validation.

## 4. Create named accounts

Create an administrator account from an interactive Railway shell. Omitting
`--password` prevents the password from entering shell history:

```bash
railway ssh -- python -m phase4a_gold_standard.backend create-user \
  --username phase4a-admin \
  --display-name "Phase 4a administrator" \
  --role admin
```

Create one reviewer restricted to exactly one language:

```bash
phase4a_gold_standard/deploy/railway/create_reviewer.sh \
  es \
  kenji-es \
  "Kenji — Spanish reviewer"
```

Examples for other reviewers:

```bash
phase4a_gold_standard/deploy/railway/create_reviewer.sh it reviewer-it "Italian reviewer"
phase4a_gold_standard/deploy/railway/create_reviewer.sh ru reviewer-ru "Russian reviewer"
phase4a_gold_standard/deploy/railway/create_reviewer.sh en reviewer-en "English reviewer"
```

Each command prompts for the password without terminal echo. Share the URL and
password separately, using an approved secure channel. Never share accounts.

## 5. Verify before inviting reviewers

```bash
railway ssh -- python -m phase4a_gold_standard.backend progress
railway logs -n 100
```

Then test in a private browser window:

1. login with the Spanish reviewer;
2. confirm only Spanish tasks appear;
3. save one draft;
4. reopen it and confirm the selection persists;
5. do not submit the calibration task unless it should enter the campaign.

Run the same access-isolation check for every reviewer account.

## 6. Backups

Enable daily volume backups in the Railway dashboard. Also download an
independent backup set at the end of every review day:

```bash
phase4a_gold_standard/deploy/railway/backup.sh phase4a_gold_standard/backups
```

The script creates and downloads:

- a consistent SQLite backup;
- the deterministic annotation JSONL export;
- the current quality report.

The backup directory is ignored by Git. Copy these files to approved
institutional storage. Do not back up only the live SQLite file while it is
running; use the provided backup command.

## 7. Windows laptop fallback

Railway remains online without the Windows laptop. The laptop is useful for
administration and storing independent backups.

For an emergency local-only copy, install Docker Desktop, clone the repository,
and run in PowerShell:

```powershell
cd feats-simplification-evaluator\phase4a_gold_standard
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(48))"
```

Paste the generated value into `.env`, then run:

```powershell
docker compose up -d --build
```

The local UI is at `http://127.0.0.1:8000`. This fallback is not accessible to
external reviewers by itself and must not be exposed through router port
forwarding.

## Security constraints

- Keep `PHASE4A_COOKIE_SECURE=1` on Railway.
- Never commit `.env`, payloads, SQLite files, exports, or backups.
- Keep one Railway replica while using SQLite.
- Use one named account per reviewer and one language per reviewer.
- Disable accounts when their assignment ends.
- Review Railway usage, logs, and backups daily during the campaign.
- Stop public access after the review window and retain the final backup in
  approved institutional storage.


## S1 degradation-validation module

S1 shares this service, login and existing accounts, but uses its own database at `/data/s1_validation_v1.sqlite3`. Its code never opens the Phase 4a database. An English reviewer sees the **S1 validation** project link because access is derived from the existing `allowed_languages`; reviewers without `en` receive HTTP 403. Administrators can inspect aggregate progress. Do not create another reviewer or permission migration.

Before the first S1 deployment, back up the live Phase 4a campaign:

```bash
phase4a_gold_standard/deploy/railway/backup.sh phase4a_gold_standard/backups/pre-s1
```

Then deploy the reviewed commit through Railway and verify `/api/health`. Build controls locally, and load the frozen 300 items plus 30 controls into the existing English username (replace `reviewer-en` if production uses another name):

```bash
python -m phase6_degraded_corpus.src.annotation.package_s1
phase4a_gold_standard/deploy/railway/upload_s1.sh \
  phase6_degraded_corpus/runs/annotation_v1/s1_items.jsonl \
  phase6_degraded_corpus/runs/annotation_v1/s1_controls.jsonl \
  reviewer-en \
  phase6_degraded_corpus/runs/annotation_v1/s1_gemini_3p8_flash.jsonl
```

The hidden `s1_key.json` and `s1_controls_key.json` must never be uploaded. In private browser windows, confirm that the English reviewer can choose Phase 4a or S1 and sees 330 S1 items, while a French/non-English reviewer gets no S1 access. Confirm Phase 4a still shows its existing submitted reviews.

During annotation, inspect progress without accessing Phase 4a SQLite:

```bash
railway ssh -- python -m phase4a_gold_standard.backend.s1_cli progress
```

Download an independent S1 SQLite backup and JSONL export:

```bash
phase4a_gold_standard/deploy/railway/backup_s1.sh
python -m phase6_degraded_corpus.src.annotation.ingest_annotations \
  phase6_degraded_corpus/runs/annotation_v1/exports/<timestamp>/annotations.jsonl
```

### Spanish and French rounds

S1 also serves Spanish and French rounds (`phase6_degraded_corpus/runs/annotation_es_v1` and `annotation_fr_v1`). Access follows each reviewer's `allowed_languages`, and an item is shown only to a reviewer allowed its `language`. The interface and the guidelines (`/s1/guidelines?lang=es|fr`) switch to the item language. Case ids carry the language (`ES-S001`, `FR-C001`), so all rounds share one S1 database. Load each round into its own reviewer, with all controls marked as identical pairs:

```bash
railway service files --service phase4a-review upload --overwrite phase6_degraded_corpus/runs/annotation_fr_v1/s1_items.jsonl /tmp/s1_fr_items.jsonl
railway service files --service phase4a-review upload --overwrite phase6_degraded_corpus/runs/annotation_fr_v1/s1_controls.jsonl /tmp/s1_fr_controls.jsonl
railway ssh --service phase4a-review -- python -m phase4a_gold_standard.backend.s1_cli load /tmp/s1_fr_items.jsonl /tmp/s1_fr_controls.jsonl --reviewer reviewer-fr --identical-controls 999
```

One reviewer holds one round: queue ranks are unique per reviewer. Ingest with `--language es|fr`; the export contains every round and each ingest keeps its own cases.

The ingest step joins hidden keys only on AIRE and writes the results and adjudication queue locally. The team performs all Railway deployment and production data operations.
