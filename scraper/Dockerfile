# Osool Scraper — Scrapling-based, zero LLM tokens
# Supports two modes: cron (one-shot crawl) and worker (Redis poller)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    wget \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    fonts-liberation \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY scraper/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium && python -m patchright install chromium

# Copy scraper package
COPY scraper/main.py scraper/worker.py scraper/settings.py /app/
COPY scraper/sites /app/sites
COPY scraper/extractors /app/extractors
COPY scraper/adapters /app/adapters

# Copy backend ingestion modules (reused as-is)
COPY backend/app/__init__.py /app/app/__init__.py
COPY backend/app/database.py /app/app/database.py
COPY backend/app/models.py /app/app/models.py
COPY backend/app/ingestion/__init__.py /app/app/ingestion/__init__.py
COPY backend/app/ingestion/scraper_schemas.py /app/app/ingestion/scraper_schemas.py
COPY backend/app/ingestion/deterministic_normalizer.py /app/app/ingestion/deterministic_normalizer.py
COPY backend/app/ingestion/repository.py /app/app/ingestion/repository.py
COPY backend/app/ingestion/anomaly_detector.py /app/app/ingestion/anomaly_detector.py

ENV PYTHONPATH=/app

# Persistent storage for Scrapling adaptive selector state
RUN mkdir -p /app/.selectors

CMD ["python", "main.py", "--mode=cron"]
