"""
Celery Configuration for Osool Backend
--------------------------------------
Standard Celery setup using Redis as broker and backend.
"""

import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery
celery_app = Celery(
    "osool_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"]  # Register tasks module
)

# Optional: Configure Celery options
celery_app.conf.update(
    result_expires=3600,  # Results expire after 1 hour
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Africa/Cairo",
    enable_utc=True,
)

# ---------------------------------------------------------------------------
# PERIODIC TASKS (BEAT)
# ---------------------------------------------------------------------------

@celery_app.task(name="scrape_nawy")
def scrape_nawy_task():
    """
    Nawy property scraping is now handled by the Railway Cron container
    (nawy_scraper_v2.py, runs Sundays 03:00 UTC). This task is a no-op stub
    to preserve Celery Beat schedule registration without breaking anything.
    """
    return {"status": "noop — scraping handled by Railway Cron (nawy_scraper_v2.py)"}


@celery_app.task(name="scrape_geopolitical", bind=True, max_retries=2, autoretry_for=(Exception,), retry_backoff=True)
def scrape_geopolitical_task(self):
    """
    Daily geopolitical & macroeconomic event scraper.
    Fetches RSS feeds, filters for RE relevance, summarizes impact via LLM,
    and stores in GeopoliticalEvent table.
    """
    import asyncio
    from app.services.geopolitical_scraper import run_geopolitical_scraper
    logger = __import__('logging').getLogger(__name__)
    logger.info("🌍 [CELERY] Starting geopolitical scraper task")
    result = asyncio.get_event_loop().run_until_complete(run_geopolitical_scraper())
    logger.info(f"🌍 [CELERY] Geopolitical scraper complete: {result}")
    return result


celery_app.conf.beat_schedule = {
    "scrape-every-6-hours": {
        "task": "scrape_nawy",
        "schedule": 21600.0, # 6 hours in seconds
    },
    "scrape-geopolitical-daily": {
        "task": "scrape_geopolitical",
        "schedule": 86400.0,  # 24 hours in seconds
    },
    "drip-emails-every-hour": {
        "task": "app.tasks.process_drip_emails_task",
        "schedule": 3600.0,  # 1 hour
    },
}

if __name__ == "__main__":
    celery_app.start()
