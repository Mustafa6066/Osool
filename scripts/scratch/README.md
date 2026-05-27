# scripts/scratch/

One-shot diagnostic and migration scripts. **Not product code.**

Anything in this directory is:
- Code somebody wrote once to inspect a bug, repair data, or test a hypothesis
- Kept in git so the team has a record of what was tried
- Free to delete if it's clearly obsolete (check `git log` for context first)

## Subdirectories

- `data/` — local debris (sqlite dev DBs, captured curl payloads, scraped
  JSON dumps, log files). **Gitignored.** Anything here is your local mess,
  not the team's. Delete freely.

## What does NOT belong here

- Anything imported by `backend/app/` or `web/`
- Anything called by CI (`make`, `pytest`, `npm run`)
- Anything called by Railway / Vercel deploy hooks

If a script in here graduates to a real workflow, move it to `scripts/` and
wire it into the `Makefile`.
