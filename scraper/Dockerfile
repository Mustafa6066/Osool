# Osool Nawy Scraper v3 — Railway Cron Service
# Full compound discovery + Nawy Now pagination, zero AI tokens
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# System dependencies for Playwright/Chromium
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

# Install Python dependencies
COPY scraper/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright + Chromium browser
RUN playwright install chromium

# Copy scraper entry point
COPY nawy_scraper_v3.py .

# Copy ingestion pipeline modules
COPY backend/app/__init__.py /app/backend/app/__init__.py
COPY backend/app/ingestion/__init__.py /app/backend/app/ingestion/__init__.py
COPY backend/app/ingestion/deterministic_normalizer.py /app/backend/app/ingestion/deterministic_normalizer.py
COPY backend/app/ingestion/repository.py /app/backend/app/ingestion/repository.py
COPY backend/app/database.py /app/backend/app/database.py
COPY backend/app/models.py /app/backend/app/models.py

ENV PYTHONPATH=/app/backend

RUN mkdir -p backend/backend data

CMD ["python", "nawy_scraper_v3.py"]
