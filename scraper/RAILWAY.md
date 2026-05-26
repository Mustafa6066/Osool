# Osool Scraper — Railway Deployment

The scraper runs as **two Railway services** built from the same Dockerfile.

## 1. `scraper-cron` (existing service, redeploy)

Config: [`railway.toml`](railway.toml).
Schedule: daily 03:00 UTC.
Action: one-shot crawl of every site x every zone, then exit.

```
startCommand   = python main.py --mode=cron
cronSchedule   = 0 3 * * *
restartPolicy  = NEVER
```

## 2. `scraper-worker` (new service)

Config: [`railway.worker.toml`](railway.worker.toml).
Always-on. Consumes `scraper:pending` from Redis (populated by the orchestrator's `scraper-refresh.job.ts`).

```
startCommand   = python main.py --mode=worker
restartPolicy  = ON_FAILURE
```

Create it via the Railway UI: New Service -> from same repo -> set `RAILWAY_DOCKERFILE_PATH=scraper/Dockerfile` and the start command above. Or via CLI:

```
railway service create scraper-worker
railway link --service scraper-worker
railway up --detach
```

## Required environment variables (both services)

| Var | Notes |
| --- | --- |
| `DATABASE_URL` | Same Postgres as the FastAPI backend |
| `REDIS_URL` | Same Redis as the orchestrator (the worker reads `scraper:pending` from here) |

**Not required:** `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`. The scraper image contains no LLM SDK.

## Optional knobs

| Var | Default | Effect |
| --- | --- | --- |
| `SCRAPER_LOCK_TTL` | 600 | Source-lock TTL in seconds (must match the orchestrator) |
| `SCRAPER_DELAY` | 1.5 | Inter-request politeness delay (seconds) |
| `SCRAPER_MAX_PAGES` | 30 | Page cap per area per cron run |
| `SCRAPER_SELECTORS_DIR` | `/app/.selectors` | Where Scrapling persists auto-learned selectors |

## Health alerts

When any field's null-rate exceeds 15% (per `ScrapeHealthReport`), the scraper LPUSHes an alert to the Redis list `scraper:health:alerts` and keeps the most recent 50. Surface this in the admin UI or wire it to the orchestrator's notifications channel.

## Manual one-off runs

```
railway run -s scraper-cron python main.py --mode=cron --site=aqarmap --area=new-cairo --dry-run
railway run -s scraper-cron python main.py --mode=cron --site=nawy --area=6th-october
```
