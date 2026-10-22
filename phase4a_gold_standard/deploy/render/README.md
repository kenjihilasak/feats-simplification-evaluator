# Moving the review service from Railway to Render

The service is one FastAPI container with two SQLite files on a persistent disk at `/data`:

- `gemma_anchored_strict_v2.sqlite3`: Phase 4a campaign
- `s1_validation_v1.sqlite3`: S1 degradation validation

The Docker image holds code only, so moving means deploying the same image on Render and copying the two databases. Run the Railway and Render commands from a laptop: AIRE blocks outbound SSH to both platforms.

## 0. Before starting

- No reviewer may write during the move. Announce a window; nothing on Railway changes after step 1.
- Install the Railway CLI and log in. Add your SSH public key to Render (Account Settings → SSH Public Keys).
- Check out the branch to deploy (`s1-multilingual`) so the `deploy/railway/*.sh` scripts are available.

## 1. Consistent backups from Railway

```bash
phase4a_gold_standard/deploy/railway/backup.sh phase4a_gold_standard/backups/pre-render
phase4a_gold_standard/deploy/railway/backup_s1.sh phase4a_gold_standard/backups/pre-render-s1
```

Both use SQLite's backup API, so the copies are consistent while the service runs. Check them:

```bash
sqlite3 phase4a_gold_standard/backups/pre-render/phase4a-*.sqlite3 'PRAGMA integrity_check;'
sqlite3 phase4a_gold_standard/backups/pre-render-s1/*/s1_validation_v1.sqlite3 'PRAGMA integrity_check;'
railway ssh --service phase4a-review -- python -m phase4a_gold_standard.backend progress > railway_progress.json
```

Keep `railway_progress.json` for the comparison in step 4. The stale `/data/imports/*.jsonl` files are not copied.

## 2. Create the Render web service

Dashboard → New → Web Service → connect `kenjihilasak/feats-simplification-evaluator`:

| Setting | Value |
|---|---|
| Branch | `s1-multilingual` (or `main` after merging) |
| Root Directory | `phase4a_gold_standard` |
| Runtime / Dockerfile path | Docker, `./Dockerfile` |
| Region | Frankfurt (EU) |
| Instance type | a paid type (persistent disks need one); Starter is enough |
| Health check path | `/api/health` |
| Disk | mount path `/data`, 10 GB |

Environment variables:

```text
PHASE4A_DATABASE=/data/gemma_anchored_strict_v2.sqlite3
S1_DATABASE=/data/s1_validation_v1.sqlite3
PHASE4A_CAMPAIGN_ID=gemma-anchored-strict-v2
PHASE4A_SESSION_SECRET=<new value from: openssl rand -hex 48>
PHASE4A_COOKIE_SECURE=1
PHASE4A_LANGUAGE_PRIORITY=en,es,it,ru,ar
```

Render supplies `PORT`. A new session secret also rotates the Railway one, as Railway's security notice advised. The first deploy starts with empty databases; that is expected.

## 3. Copy the databases onto the disk

Compress, then copy with SCP to the service's SSH address (Render dashboard → service → Connect → SSH):

```bash
gzip -k phase4a_gold_standard/backups/pre-render/phase4a-*.sqlite3
gzip -k phase4a_gold_standard/backups/pre-render-s1/*/s1_validation_v1.sqlite3
ssh <service>@ssh.frankfurt.render.com 'mkdir -p /data/incoming'
scp -s phase4a_gold_standard/backups/pre-render/phase4a-*.sqlite3.gz <service>@ssh.frankfurt.render.com:/data/incoming/phase4a.sqlite3.gz
scp -s phase4a_gold_standard/backups/pre-render-s1/*/s1_validation_v1.sqlite3.gz <service>@ssh.frankfurt.render.com:/data/incoming/s1.sqlite3.gz
```

In the Render Shell (dashboard, works from any browser) or over SSH, replace the empty databases:

```bash
cd /data
gunzip incoming/phase4a.sqlite3.gz incoming/s1.sqlite3.gz
rm -f gemma_anchored_strict_v2.sqlite3* s1_validation_v1.sqlite3*
mv incoming/phase4a.sqlite3 gemma_anchored_strict_v2.sqlite3
mv incoming/s1.sqlite3 s1_validation_v1.sqlite3
rmdir incoming
```

Then dashboard → Manual Deploy → Restart service, so the process opens the copied files.

## 4. Verify before switching reviewers

```bash
python -m phase4a_gold_standard.backend progress        # must equal railway_progress.json
python -m phase4a_gold_standard.backend.s1_cli progress  # English S1 round: 330 items
curl -fsS https://<service>.onrender.com/api/health
```

In private browser windows: sign in as an existing reviewer, open a submitted Phase 4a review, and open `/s1/guidelines?lang=es`.

## 5. Load the Spanish and French S1 rounds

Copy from AIRE to the laptop, then to `/data/incoming` as in step 3:

- `phase6_degraded_corpus/runs/annotation_{es,fr}_v1/s1_items.jsonl`, `s1_controls.jsonl`
- `phase6_degraded_corpus/runs/annotation_{v1,es_v1,fr_v1}/s1_openai_gpt54mini.jsonl`

Never copy `s1_key.json` or `s1_controls_key.json`. Then:

```bash
python -m phase4a_gold_standard.backend create-user --username reviewer-fr --display-name "French reviewer" --role reviewer --language fr
python -m phase4a_gold_standard.backend.s1_cli load /data/incoming/es_items.jsonl /data/incoming/es_controls.jsonl --reviewer <spanish-reviewer> --identical-controls 999
python -m phase4a_gold_standard.backend.s1_cli load /data/incoming/fr_items.jsonl /data/incoming/fr_controls.jsonl --reviewer reviewer-fr --identical-controls 999
for f in /data/incoming/*_openai.jsonl; do python -m phase4a_gold_standard.backend.s1_cli load-suggestions "$f"; done
python -m phase4a_gold_standard.backend.s1_cli progress
```

The existing Spanish Phase 4a reviewer already has S1 access through `allowed_languages`. Delete `/data/incoming` afterwards.

## 6. Switch and retire Railway

1. Send reviewers the new URL; passwords are unchanged, and everyone signs in again because the secret changed.
2. In Railway, remove the service's public domain (Settings → Networking) so nobody writes to the old copy.
3. Keep the Railway volume and the local backups for two weeks, then delete the Railway project.
4. From then on, back up with the Render Shell (`backend backup`, `s1_cli backup`) and SCP.
