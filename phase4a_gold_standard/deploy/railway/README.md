# Railway deployment for Phase 4a

This is the recommended shared deployment for the multilingual human-review
campaign. Railway hosts one FastAPI service and one persistent volume. Reviewers
need only the generated HTTPS URL and their individual Phase 4a credentials;
they do not need AIRE, GitHub, Python, or access to any dataset files.

## Runtime architecture

```text
Reviewer browser
    -> Railway HTTPS domain
    -> Phase 4a FastAPI service (one replica)
    -> /data/gold_review.sqlite3 on the attached volume
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
PHASE4A_DATABASE=/data/gold_review.sqlite3
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
test -s phase4a_gold_standard/runs/materialized/2026-08-27_stanza_ud_full_v1/es/payloads/es/annotation_tasks.jsonl

phase4a_gold_standard/deploy/railway/upload_language.sh \
  es \
  phase4a_gold_standard/runs/materialized/2026-08-27_stanza_ud_full_v1/es/payloads/es/annotation_tasks.jsonl
```

The script:

1. uploads the JSONL to `/data/imports` on the Railway volume;
2. imports it into the persistent SQLite campaign;
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
