"""
Osool Ingestion Pipeline
-------------------------
Autonomous, stealth, differential-hash data pipeline for Nawy.com.

Architecture summary:
  worker.py        — ARQ task queue entry point + dynamic URL discovery
  core_scraper.py  — Stealth Playwright async scraper (Next.js __NEXT_DATA__ + XHR)
  llm_normalizer.py — gpt-4o-mini structured normalization + Pydantic v2 schemas
  repository.py    — SHA256 differential hash upsert + text-embedding-3-small

Run the worker:
    python -m arq app.ingestion.worker.WorkerSettings
"""

# Worker and core_scraper have heavy deps (arq, full app.services) that may not
# be available in stripped-down environments like the Railway Cron scraper container.
try:
    from app.ingestion.worker import (
        WorkerSettings,
        master_discovery_job,
        scrape_compound_task,
    )
except ImportError:
    WorkerSettings = None  # type: ignore[assignment,misc]
    master_discovery_job = None  # type: ignore[assignment]
    scrape_compound_task = None  # type: ignore[assignment]

try:
    from app.ingestion.core_scraper import ScraperError, scrape_compound
except ImportError:
    ScraperError = Exception  # type: ignore[assignment,misc]
    scrape_compound = None  # type: ignore[assignment]

from app.ingestion.llm_normalizer import (
    NormalizedProperty,
    NormalizationResult,
    normalize_properties,
)
from app.ingestion.repository import UpsertResult, upsert_properties

__all__ = [
    # Worker
    "WorkerSettings",
    "master_discovery_job",
    "scrape_compound_task",
    # Scraper
    "scrape_compound",
    "ScraperError",
    # Normalizer
    "normalize_properties",
    "NormalizedProperty",
    "NormalizationResult",
    # Repository
    "upsert_properties",
    "UpsertResult",
]
