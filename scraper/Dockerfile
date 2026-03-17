# Osool Nawy Scraper — Railway Cron Service
# Playwright + Chromium headless for weekly property scraping
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system dependencies for Playwright/Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    wget \
    # Chromium dependencies
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

# Install Python dependencies (minimal set for scraper)
COPY scraper/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright + Chromium browser
RUN playwright install chromium

# Copy scraper code + data
COPY nawy_scraper_v2.py .
COPY nawy_compound_urls.json .

# Copy ingestion pipeline modules (Strategy 1 + 2: NEXT_DATA + LLM normalizer)
# These are imported as `from app.ingestion.xxx import ...` via PYTHONPATH=/app/backend
COPY backend/app/__init__.py /app/backend/app/__init__.py
COPY backend/app/ingestion/__init__.py /app/backend/app/ingestion/__init__.py
COPY backend/app/ingestion/llm_normalizer.py /app/backend/app/ingestion/llm_normalizer.py
COPY backend/app/ingestion/repository.py /app/backend/app/ingestion/repository.py
COPY backend/app/database.py /app/backend/app/database.py
COPY backend/app/models.py /app/backend/app/models.py

# Set PYTHONPATH so `from app.ingestion.xxx` resolves to /app/backend/app/ingestion/
ENV PYTHONPATH=/app/backend

# Create backend directory for .env compatibility
# (Railway injects env vars directly, so this is just for the load_dotenv fallback)
RUN mkdir -p backend/backend

# Create data directory for scrape summary output
RUN mkdir -p data

# Run the scraper
CMD ["python", "nawy_scraper_v2.py"]
