# Changelog

All notable changes to Osool. Format roughly follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Commit history is
the source of truth — this file groups commits by user-visible theme.

## [Unreleased]

### Developer experience
- New `Makefile` exposes `dev / backend / frontend / migrate / seed / test / lint`.
- New `docker-compose.yml` brings up Postgres (pgvector) + Redis for local dev.
- README quick-start now covers Postgres/Redis, frontend (`cd web && npm run dev`),
  and the actual production API surface (was listing endpoints that don't exist).
- Collapsed two redundant CI workflows into one (`ci-cd.yml`).
- `npm test` in `web/` now runs lint + Playwright instead of silently no-op'ing.
- Cleared ~25 ad-hoc scripts and ~17 data-dump files out of repo root into
  `scripts/scratch/`; data dumps and sqlite dev DBs are now gitignored.

### Chat
- `/api/v1/chat` now requires authentication. Anonymous callers get a 401
  with `requires_auth: true`; the frontend stashes the prompt in localStorage
  and redirects to `/signup?next=/chat`, replaying the prompt after auth.
- Differentiated chat error messages: timeout vs server vs offline vs generic,
  in both English and Arabic.
- 500 errors in chat now log the full traceback to Railway so we can actually
  diagnose them.

### Retrieval (zero-token property search)
- New `/api/v1/retrieve` endpoint: 22k properties searched with no per-query
  LLM or embedding cost. Pure SQL + Redis. Targets p50 ≤ 80ms.
- L1 intent extractor: regex + dictionary parse, no API calls.
- L2 retrieval: 4 parallel SQL sub-queries (structured / BM25 / trigram fuzzy /
  pgvector "more like this") with own AsyncSession each.
- L3 ranking: Reciprocal Rank Fusion + decision-fit boosts (budget, payment,
  freshness, La2ta flag).
- L4 augmentation: NPV math, payment-fit, "why matched" template.
- L5 caching: 5-min hot result cache + 1h dictionary cache (compounds /
  developers / locations) with pubsub freshness invalidation.
- One-shot embedding backfill (~$0.07 total) + HNSW index for L2d.
- Compound/developer dictionary wiring with longest-match-first + Arabic
  dialect aliases.

### Scrapers
- Nawy: `--mode=nawy-all` walks every compound via listing-api XHR
  (the SSR `/nawy-now?page=N` ignores pagination).
- Nawy Now: pulls instant-delivery feed with full `paymentPlan` + `readyBy`.
- Aqarmap: optional `SCRAPER_PROXY_URL` env routes fetches through a
  residential proxy when Railway egress IPs are blocked.
- Repository upsert: `search_tsv` excluded from UPDATE SET (it's a generated
  column); ON CONFLICT predicate emitted as raw `text()` to match the partial
  unique index; curated feeds (Nawy Now) bypass the anomaly detector.
- Scrape run IDs registered in Redis so `mark_stale_properties()` can flag
  sold listings.

### UI / Design
- "Editorial + Cairene" design refresh per `DESIGN.md` — warm paper bg,
  Newsreader + Cairo Display typography, mashrabiya motifs.
- Mobile compatibility pass on `/chat` and landing.
- Free/paid demo toggle is admin-only (`showDemoToggle={isAdmin}`).
- Landing hero composer routes anonymous users through `/signup?next=/chat`
  with the prompt stashed in localStorage.

### Bug fixes
- Chat `/api/v1/chat` 500: response now wrapped in `JSONResponse` so slowapi
  can attach rate-limit headers.
- Chat language: always send `language=auto` so AI replies match input
  language regardless of UI toggle.
- Web footer: repointed broken "Buyer's guide" link off the 404'd path.

---

Earlier history lives in `git log`. For a structured changelog going forward,
keep entries above the `---` line and graduate them into a versioned section
on release.
