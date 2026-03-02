# Railway Scraper Deployment Guide

## Architecture

The project deploys **two Railway services** from one GitHub repo:

| Service | Type | Schedule | Dockerfile |
|---------|------|----------|------------|
| **Backend API** | Web Service | Always running | `backend/Dockerfile.prod` |
| **Nawy Scraper** | Cron Job | Weekly (Sunday 03:00 UTC) | `scraper/Dockerfile` |

Both services share the same Railway PostgreSQL database.

---

## Step 1: Push to GitHub

```bash
git add -A
git commit -m "Add Nawy scraper v2 + Railway cron deployment"
git push origin main
```

## Step 2: Set Up Backend API Service (if not already done)

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. **New Project** → **Deploy from GitHub repo** → Select `Mustafa6066/Osool`
3. Railway auto-detects the root `railway.toml` → uses `backend/Dockerfile.prod`
4. Add environment variables:
   - `DATABASE_URL` → (use Railway's PostgreSQL plugin reference: `${{Postgres.DATABASE_URL}}`)
   - `OPENAI_API_KEY` → your OpenAI key
   - `ANTHROPIC_API_KEY` → your Anthropic key
   - `SECRET_KEY` → generate with `python -c "import secrets; print(secrets.token_hex(32))"`
   - `ENVIRONMENT` → `production`

## Step 3: Set Up Scraper Cron Service

1. In the same Railway project, click **+ New** → **Service** → **GitHub Repo** → Select `Mustafa6066/Osool`
2. Go to **Settings** for this new service:
   - **Root Directory**: `/` (project root)
   - **Build Command**: Leave empty (uses Dockerfile)
   - **Dockerfile Path**: `scraper/Dockerfile`
3. Go to **Settings → Deploy** section:
   - **Cron Schedule**: `0 3 * * 0` (every Sunday at 3 AM UTC)
   - This makes it a cron service (runs, completes, then stops until next trigger)
4. Add environment variables (same PostgreSQL + OpenAI):
   - `DATABASE_URL` → `${{Postgres.DATABASE_URL}}`  
   - `OPENAI_API_KEY` → your OpenAI key

## Step 4: Link PostgreSQL

1. Ensure you have a **PostgreSQL plugin** in the project
2. Both services should reference `${{Postgres.DATABASE_URL}}` for their `DATABASE_URL`
3. The pgvector extension needs to be enabled:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

## Step 5: Run Migrations

The backend API auto-runs `alembic upgrade head` on startup (see `Dockerfile.prod` CMD).  
No manual migration step needed.

## Step 6: Test the Scraper

To test the scraper manually before waiting for the cron:
1. Go to the scraper service in Railway
2. Click **Deploy** → **Trigger Deploy** (or redeploy)
3. Watch the logs — you should see compound-by-compound scrape progress

---

## Environment Variables Reference

| Variable | Required By | Description |
|----------|------------|-------------|
| `DATABASE_URL` | Both | PostgreSQL connection string |
| `OPENAI_API_KEY` | Both | For embeddings (text-embedding-3-small) |
| `ANTHROPIC_API_KEY` | Backend only | For Claude AI responses |
| `SECRET_KEY` | Backend only | JWT/session secret |
| `ENVIRONMENT` | Backend only | `production` |

---

## Cron Schedule

The scraper runs weekly: **every Sunday at 03:00 UTC** (`0 3 * * 0`).

To change the schedule, update `scraper/railway.toml`:
```toml
[deploy]
cronSchedule = "0 3 * * 0"  # Change this cron expression
```

Common schedules:
- Daily at midnight: `0 0 * * *`
- Every Monday at 6 AM: `0 6 * * 1`
- Every 3 days: `0 0 */3 * *`
- Twice a week (Wed + Sun): `0 3 * * 0,3`
