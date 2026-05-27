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

# Lock TTL must match the orchestrator's scraper-refresh.job.ts (10 minutes).
SOURCE_LOCK_TTL_SECONDS: int = int(os.getenv("SCRAPER_LOCK_TTL", "600"))

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

# Health alert key — consumed by the orchestrator's notifications path.
HEALTH_ALERT_KEY: str = "scraper:health:alerts"
HEALTH_ALERT_KEEP: int = 50

# Redis contract with Osool-orchestrator/apps/api/src/jobs/handlers/scraper-refresh.job.ts
PENDING_QUEUE_KEY: str = "scraper:pending"
REFRESH_LOG_KEY: str = "scraper:refresh:log"
REFRESH_LOG_KEEP: int = 100
