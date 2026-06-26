"""Scraper-wide configuration loaded from environment."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_ENV_CANDIDATES = [
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parent.parent / "backend" / ".env",
    Path("/app/.env"),
]
for candidate in _ENV_CANDIDATES:
    if candidate.exists():
        load_dotenv(dotenv_path=str(candidate), override=False)
        break

DATABASE_URL: str = os.getenv("DATABASE_URL", "")
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Egyptian zones we crawl. Keys match the slugs used by both nawy.com and aqarmap.com.eg.
DEFAULT_AREAS: list[str] = [
    "new-cairo",
    "6th-october",
    "new-administrative-capital",
    "north-coast",
    "sheikh-zayed",
    "new-zayed",
    "ain-sokhna",
]

# Source-lock TTL. Must comfortably exceed the worst-case crawl duration, or the
# lock expires mid-run and a second crawler starts (double request rate → ban).
# nawy-all can run for tens of minutes; default 1h, override with SCRAPER_LOCK_TTL.
# The lock is token-owned and released via compare-and-delete (see main.py), so an
# expired-then-reacquired lock can never be stolen by the original holder. [S5]
SOURCE_LOCK_TTL_SECONDS: int = int(os.getenv("SCRAPER_LOCK_TTL", "3600"))

# Persistent dir for Scrapling's auto-learned selector state.
SELECTORS_DIR: Path = Path(os.getenv("SCRAPER_SELECTORS_DIR", "/app/.selectors"))
SELECTORS_DIR.mkdir(parents=True, exist_ok=True)

# Per-site request pacing (politeness).
REQUEST_DELAY_SECONDS: float = float(os.getenv("SCRAPER_DELAY", "1.5"))
MAX_PAGES_PER_AREA: int = int(os.getenv("SCRAPER_MAX_PAGES", "30"))

# Optional residential/rotating proxy. When set, Aqarmap fetches route
# through it (Aqarmap rate-limits/IP-blocks Railway egress aggressively
# and serves HTTP 403 to unproxied requests).
# Examples:
#   http://USER:PASS@geo.iproyal.com:12321
#   http://USER:PASS@premium.residential.obscura.example:9000
# Setting only the standard HTTPS_PROXY env var also works.
SCRAPER_PROXY_URL: str = os.getenv("SCRAPER_PROXY_URL") or os.getenv("HTTPS_PROXY") or ""


# Proxy POOL (Phase 1 / S2). Comma- or newline-separated list of residential
# proxy URLs. The scraper rotates across healthy proxies and quarantines any that
# return blocks (403/429/empty body). Falls back to the single SCRAPER_PROXY_URL
# so existing single-proxy deployments keep working unchanged.
def _parse_proxy_list() -> list[str]:
    raw = os.getenv("SCRAPER_PROXY_URLS", "")
    urls = [u.strip() for u in raw.replace("\n", ",").split(",") if u.strip()]
    if not urls and SCRAPER_PROXY_URL:
        urls = [SCRAPER_PROXY_URL]
    return urls


SCRAPER_PROXY_URLS: list[str] = _parse_proxy_list()


# Realistic rotating browser User-Agents (Phase 1 / S1). A self-identifying UA
# like "OsoolScraper/2.0" is trivially fingerprinted and blocked; present as a
# current desktop browser instead.
BROWSER_USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


def browser_headers(user_agent: str | None = None) -> dict[str, str]:
    """Browser-like default headers with a (rotating) realistic User-Agent. [S1]"""
    import random

    ua = user_agent or random.choice(BROWSER_USER_AGENTS)
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Upgrade-Insecure-Requests": "1",
    }

# Browser kill-switch. When true, skip Scrapling/Playwright (Chromium) and
# fetch via httpx only. Chromium can crash on resource-constrained hosts
# (posix_spawn EAGAIN launching chrome_crashpad_handler -> SIGTRAP), which
# marks the whole cron run CRASHED. httpx through the residential proxy
# (SCRAPER_PROXY_URL) returns valid HTML for both sites, so this keeps the
# cron healthy without the browser. Set SCRAPER_DISABLE_BROWSER=true on the
# Railway nawy-scraper service to enable.
SCRAPER_DISABLE_BROWSER: bool = os.getenv("SCRAPER_DISABLE_BROWSER", "false").strip().lower() in ("1", "true", "yes", "on")

# Health alert key — consumed by the orchestrator's notifications path.
HEALTH_ALERT_KEY: str = "scraper:health:alerts"
HEALTH_ALERT_KEEP: int = 50

# Redis contract with Osool-orchestrator/apps/api/src/jobs/handlers/scraper-refresh.job.ts
PENDING_QUEUE_KEY: str = "scraper:pending"
REFRESH_LOG_KEY: str = "scraper:refresh:log"
REFRESH_LOG_KEEP: int = 100
