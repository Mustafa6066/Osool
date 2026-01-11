#!/bin/bash
# Osool Backend - Docker Entrypoint Script
# Phase 4.3: Production Deployment
# ------------------------------------------

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}[*] Osool Backend Starting...${NC}"

# ==========================================
# 1. Wait for Database
# ==========================================
echo -e "${YELLOW}[1/5] Waiting for PostgreSQL...${NC}"

until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo -e "${GREEN}✓ PostgreSQL is up${NC}"

# ==========================================
# 2. Wait for Redis
# ==========================================
echo -e "${YELLOW}[2/5] Waiting for Redis...${NC}"

until redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null | grep -q PONG; do
  echo "Redis is unavailable - sleeping"
  sleep 2
done

echo -e "${GREEN}✓ Redis is up${NC}"

# ==========================================
# 3. Run Database Migrations
# ==========================================
echo -e "${YELLOW}[3/5] Running database migrations...${NC}"

alembic upgrade head

if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ Migrations completed${NC}"
else
  echo -e "${RED}✗ Migration failed${NC}"
  exit 1
fi

# ==========================================
# 4. Data Ingestion (if database is empty)
# ==========================================
echo -e "${YELLOW}[4/6] Checking property data ingestion...${NC}"

PROPERTY_COUNT=$(python -c "
from app.database import SessionLocal
from app.models import Property
db = SessionLocal()
count = db.query(Property).count()
db.close()
print(count)
" 2>/dev/null || echo "0")

echo "Properties in database: ${PROPERTY_COUNT}"

if [ "$PROPERTY_COUNT" -eq "0" ]; then
    echo -e "${YELLOW}Database is empty - running data ingestion...${NC}"

    PROPERTIES_JSON="../data/properties.json"
    if [ -f "$PROPERTIES_JSON" ]; then
        echo "Found properties.json - ingesting data..."
        python ingest_data_postgres.py

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Data ingestion completed${NC}"
        else
            echo -e "${RED}✗ Data ingestion failed - continuing anyway${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ properties.json not found${NC}"
    fi
else
    echo -e "${GREEN}✓ Database already contains ${PROPERTY_COUNT} properties${NC}"
fi

# ==========================================
# 5. Environment Validation (Production Only)
# ==========================================
if [ "${ENVIRONMENT}" = "production" ]; then
    echo -e "${YELLOW}[5/6] Validating production environment...${NC}"

    REQUIRED_VARS=(
        "WALLET_ENCRYPTION_KEY"
        "JWT_SECRET_KEY"
        "DATABASE_URL"
        "OPENAI_API_KEY"
    )

    MISSING_VARS=()
    for VAR in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!VAR}" ]; then
            MISSING_VARS+=("$VAR")
        fi
    done

    if [ ${#MISSING_VARS[@]} -ne 0 ]; then
        echo -e "${RED}✗ CRITICAL: Missing required environment variables:${NC}"
        printf '%s\n' "${MISSING_VARS[@]}"
        exit 1
    fi

    echo -e "${GREEN}✓ All required environment variables present${NC}"
else
    echo -e "${YELLOW}[5/6] Running in ${ENVIRONMENT} mode - skipping strict validation${NC}"
fi

# ==========================================
# 6. Start Application
# ==========================================
echo -e "${YELLOW}[6/6] Starting application server...${NC}"
echo -e "${GREEN}[+] Osool Backend is ONLINE${NC}"

# Production: Use Gunicorn with Uvicorn workers
if [ "${ENVIRONMENT}" = "production" ]; then
    echo "Starting Gunicorn with Uvicorn workers..."
    exec gunicorn app.main:app \
        --bind 0.0.0.0:${PORT:-8000} \
        --workers ${WORKERS:-4} \
        --worker-class uvicorn.workers.UvicornWorker \
        --timeout ${TIMEOUT:-120} \
        --keep-alive 75 \
        --access-logfile - \
        --error-logfile - \
        --log-level ${LOG_LEVEL:-info}
else
    # Development: Use Uvicorn directly with auto-reload
    echo "Starting Uvicorn (development mode)..."
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port ${PORT:-8000} \
        --reload \
        --log-level ${LOG_LEVEL:-info}
fi
