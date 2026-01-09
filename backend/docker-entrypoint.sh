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
# 4. Create Initial Data (if needed)
# ==========================================
echo -e "${YELLOW}[4/5] Checking initial data...${NC}"

python -c "
from app.database import SessionLocal
from app.models import User
db = SessionLocal()
user_count = db.query(User).count()
db.close()
print(f'Users in database: {user_count}')
"

# ==========================================
# 5. Start Application
# ==========================================
echo -e "${YELLOW}[5/5] Starting Uvicorn server...${NC}"
echo -e "${GREEN}[+] Osool Backend is ONLINE${NC}"

# Start Uvicorn with production settings
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port ${PORT:-8000} \
  --workers ${WORKERS:-4} \
  --log-level ${LOG_LEVEL:-info} \
  --access-log \
  --proxy-headers \
  --forwarded-allow-ips='*' \
  --timeout-keep-alive 75
