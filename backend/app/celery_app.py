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

if __name__ == "__main__":
    celery_app.start()
