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
    Regularly scrapes Nawy website for new listings.
    Scheduled every 6 hours via Beat.
    """
    from app.services.nawy_scraper import ingest_nawy_data
    return ingest_nawy_data()

celery_app.conf.beat_schedule = {
    "scrape-every-6-hours": {
        "task": "scrape_nawy",
        "schedule": 21600.0, # 6 hours in seconds
    },
}

if __name__ == "__main__":
    celery_app.start()
