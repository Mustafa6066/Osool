# Railway Pro Deployment Guide - Osool Platform

Complete guide for deploying the Osool real estate platform to Railway Pro.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Architecture](#architecture)
- [Pre-Deployment](#pre-deployment)
- [Railway Setup](#railway-setup)
- [Environment Configuration](#environment-configuration)
- [Deployment](#deployment)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Post-Deployment](#post-deployment)

---

## Overview

Osool is a sophisticated real estate platform with AI-powered property analysis featuring:
- **Backend**: FastAPI (Python 3.10) with Claude 3.5 Sonnet AI
- **Database**: PostgreSQL 15+ with optional pgvector extension
- **Cache**: Redis for session management and caching
- **Frontend**: Next.js 16 (deployed separately to Vercel)

**Deployment Time**: 45-60 minutes from start to production

---

## Prerequisites

### Required Accounts & API Keys

1. **Railway Account** ([railway.app](https://railway.app))
   - Pro plan recommended for production workloads
   - Credit card for billing

2. **OpenAI API Key** ([platform.openai.com](https://platform.openai.com/api-keys))
   - Required for property embeddings and fallback AI
   - Model used: `text-embedding-ada-002`

3. **Anthropic API Key** ([console.anthropic.com](https://console.anthropic.com/settings/keys))
   - Required for Claude 3.5 Sonnet (AMR Agent)
   - Model: `claude-3-5-sonnet-20241022`

4. **GitHub Repository**
   - Osool codebase pushed to GitHub
   - Railway deploys from GitHub

### Local Requirements

- Python 3.10+ (for generating secrets)
- Git (for version control)
- curl (for testing endpoints)

---

## Architecture

### Railway Services Structure

```
Railway Project: Osool Production
├── PostgreSQL (Railway-managed)
│   ├── Version: 15+
│   ├── Storage: Persistent volumes
│   └── Provides: DATABASE_URL
│
├── Redis (Railway-managed)
│   ├── Version: 7+
│   ├── Use: Caching & sessions
│   └── Provides: REDIS_URL
│
└── Backend (From GitHub)
    ├── Root: /backend
    ├── Build: Dockerfile.prod
    ├── Port: 8000
    └── Links: PostgreSQL + Redis
```

### Deployment Flow

```
GitHub (master branch)
    ↓ (auto-deploy on push)
Railway Build System
    ↓ (Dockerfile.prod)
Docker Container
    ↓ (docker-entrypoint.sh)
1. Wait for services
2. Run migrations (alembic upgrade head)
3. Ingest property data (if empty)
4. Validate environment
5. Start Gunicorn + Uvicorn workers
    ↓
Backend API (port 8000)
```

---

## Pre-Deployment

### Step 1: Generate Security Secrets

Navigate to the backend directory and run the secret generator:

```bash
cd backend
python generate_secrets.py
```

**Output Example**:
```
======================================================================
OSOOL SECURE SECRET GENERATOR
======================================================================

Copy these values to your backend/.env file:

----------------------------------------------------------------------

# JWT Secret (for access tokens)
JWT_SECRET_KEY=o2qVwe^0(dCvme86@VA@@(#s=&GNXZI&2qJ+e$)7YNn2YsyBm5)Ge3uV)9!45pDR

# Admin API Key (for protected admin endpoints)
ADMIN_API_KEY=47819d4e25843785289a028aaced7b5a439296de558ee7c8912cf21d687f291d

# Wallet Encryption Key (CRITICAL - for encrypting user wallets)
WALLET_ENCRYPTION_KEY=-Si1iuU6l--uRhNcwkZcoMcjQrfr5C1SVoDMyUb8z_g=

# Database URL (PostgreSQL)
DATABASE_URL=postgresql://osool_user:t89nN3fdrdftXN1oklh1TyEh@localhost:5432/osool_dev

----------------------------------------------------------------------
```

**IMPORTANT**: Copy these values immediately and store them securely in a password manager. They are shown only once.

### Step 2: Prepare API Keys

Ensure you have:
- **OpenAI API Key**: `sk-proj-...` format
- **Anthropic API Key**: `sk-ant-api03-...` format

Test your keys:
```bash
# Test OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_OPENAI_KEY"

# Test Anthropic
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_ANTHROPIC_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

### Step 3: Commit and Push Code

Ensure all changes are committed and pushed to GitHub:

```bash
# Check status
git status

# Add any pending changes
git add .

# Commit
git commit -m "chore: prepare for Railway deployment"

# Push to master
git push origin master
```

---

## Railway Setup

### Step 1: Create New Project

1. Go to [railway.app](https://railway.app) and log in
2. Click **"New Project"**
3. Name it: `Osool Production` (or your preferred name)
4. Select region closest to your users (for Egypt: Europe regions recommended)

### Step 2: Add PostgreSQL Database

1. In your project, click **"+ New"**
2. Select **"Database"** → **"Add PostgreSQL"**
3. Railway provisions PostgreSQL 15+ automatically
4. Note: pgvector extension is NOT included by default (this is handled via SKIP_PGVECTOR=1)

**Service Configuration**:
- **Name**: `Postgres` (Railway default)
- **Plan**: Hobby or Pro (Pro recommended for production)
- **Storage**: Auto-managed persistent volumes

### Step 3: Add Redis Cache

1. Click **"+ New"** again
2. Select **"Database"** → **"Add Redis"**
3. Railway provisions Redis 7+ automatically

**Service Configuration**:
- **Name**: `Redis` (Railway default)
- **Plan**: Hobby or Pro
- **Persistence**: Enabled by default

### Step 4: Deploy Backend from GitHub

1. Click **"+ New"**
2. Select **"GitHub Repo"**
3. Connect your GitHub account (if not already connected)
4. Select the **Osool** repository
5. Click **"Add"**

**Initial Configuration**:
- Railway auto-detects Dockerfile.prod in `/backend`
- If not detected, manually set:
  - **Root Directory**: `/backend`
  - **Dockerfile Path**: `Dockerfile.prod`

---

## Environment Configuration

### Configuring Backend Service

1. Click on your **Backend service** in Railway dashboard
2. Go to **"Variables"** tab
3. Click **"RAW Editor"** for bulk paste

### Environment Variables Template

Copy and paste the following, replacing placeholders with your actual values:

```bash
# ═══════════════════════════════════════════════════════════════
# CORE SETTINGS
# ═══════════════════════════════════════════════════════════════
ENVIRONMENT=production
PORT=8000
PYTHONPATH=/app

# ═══════════════════════════════════════════════════════════════
# DATABASE (Auto-linked from Railway PostgreSQL)
# ═══════════════════════════════════════════════════════════════
DATABASE_URL=${{Postgres.DATABASE_URL}}

# ═══════════════════════════════════════════════════════════════
# REDIS (Auto-linked from Railway Redis)
# ═══════════════════════════════════════════════════════════════
REDIS_URL=${{Redis.REDIS_URL}}

# ═══════════════════════════════════════════════════════════════
# CRITICAL SECURITY KEYS (From generate_secrets.py)
# ═══════════════════════════════════════════════════════════════
JWT_SECRET_KEY=PASTE_YOUR_JWT_SECRET_KEY_HERE
ADMIN_API_KEY=PASTE_YOUR_ADMIN_API_KEY_HERE
WALLET_ENCRYPTION_KEY=PASTE_YOUR_WALLET_ENCRYPTION_KEY_HERE

# ═══════════════════════════════════════════════════════════════
# AI SERVICES (Required)
# ═══════════════════════════════════════════════════════════════
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_KEY_HERE
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_ANTHROPIC_KEY_HERE

# Claude Configuration
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0.3

# ═══════════════════════════════════════════════════════════════
# PGVECTOR COMPATIBILITY
# ═══════════════════════════════════════════════════════════════
# Railway PostgreSQL doesn't include pgvector by default
# This flag enables text-based fallback (fully functional)
SKIP_PGVECTOR=1

# ═══════════════════════════════════════════════════════════════
# CORS (Update after frontend deployment)
# ═══════════════════════════════════════════════════════════════
FRONTEND_DOMAIN=http://localhost:3000
# After Vercel deployment: FRONTEND_DOMAIN=https://your-app.vercel.app

# ═══════════════════════════════════════════════════════════════
# MONITORING & LOGGING
# ═══════════════════════════════════════════════════════════════
LOG_LEVEL=info
SENTRY_DSN=
# Optional: Add Sentry DSN for error tracking

# ═══════════════════════════════════════════════════════════════
# FEATURE FLAGS (Phase 1 - Disable optional features)
# ═══════════════════════════════════════════════════════════════
ENABLE_BLOCKCHAIN=false
ENABLE_PAYMENTS=false
ENABLE_SMS=false
ENABLE_EMAIL=false
```

### Understanding Railway Variable References

Railway uses `${{Service.VARIABLE}}` syntax to reference other services:

- `${{Postgres.DATABASE_URL}}` → Automatically resolved to PostgreSQL connection string
- `${{Redis.REDIS_URL}}` → Automatically resolved to Redis connection string

This creates service dependencies and ensures services start in the correct order.

---

## Deployment

### Step 1: Deploy Backend

After configuring environment variables:

1. Go to **"Deployments"** tab
2. Click **"Deploy"** button (or push to GitHub for auto-deploy)
3. Monitor build logs in real-time

### Step 2: Monitor Build Logs

Watch for these key steps in the logs:

```
[1/5] Building Docker image...
✓ Docker image built successfully

[2/5] Waiting for PostgreSQL...
✓ PostgreSQL is ready

[3/5] Checking Redis...
✓ Redis configured

[4/5] Running database migrations...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade -> 001_initial_schema
✓ Migrations completed

[5/5] Checking property data ingestion...
Properties in database: 0
Database is empty - running data ingestion...
✓ Data ingestion completed

[6/6] Starting application server...
[*] Osool Backend Starting...
    |-- Environment: production
    |-- Port: 8000
    |-- Database: Connected
    |-- Wallet Encryption: VALIDATED
[+] Osool Backend is ONLINE
```

### Step 3: Get Your Backend URL

Once deployed successfully:

1. Go to **"Settings"** tab
2. Find **"Domains"** section
3. Copy the Railway-provided URL: `https://your-service-name.up.railway.app`

Alternatively, click **"Generate Domain"** to create a public URL.

---

## Verification

### Quick Health Check

Test your backend is running:

```bash
curl https://your-backend.up.railway.app/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "osool-backend",
  "environment": "production",
  "timestamp": "2026-01-13T20:00:00.000Z"
}
```

### API Root Test

```bash
curl https://your-backend.up.railway.app/
```

**Expected Response**:
```json
{
  "message": "Welcome to Osool API",
  "version": "1.0.0",
  "features": ["AI Chat", "Property Search", "Price Valuation", "Contract Analysis"]
}
```

### Database Connection Test

```bash
curl https://your-backend.up.railway.app/api/properties?limit=1
```

Should return a JSON array with property data (or empty array if no properties ingested yet).

### AI Service Test

```bash
curl -X POST https://your-backend.up.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "مرحبا", "user_id": "test-user"}'
```

Should return an AI-generated response in Arabic.

---

## Troubleshooting

### Issue 1: Backend Won't Start - Missing ADMIN_API_KEY

**Error in logs**:
```
RuntimeError: CRITICAL: Missing required environment variables: ADMIN_API_KEY
```

**Solution**:
1. Go to Backend service → Variables tab
2. Verify `ADMIN_API_KEY` is present and not empty
3. Ensure no extra spaces or newlines in the key
4. Redeploy if needed

### Issue 2: Database Connection Failed

**Error in logs**:
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution**:
1. Verify `DATABASE_URL=${{Postgres.DATABASE_URL}}` is set correctly (with double curly braces)
2. Check PostgreSQL service is running in Railway dashboard
3. Ensure Backend service has dependency link to Postgres (Railway auto-creates this)

### Issue 3: Redis Connection Failed

**Error in logs**:
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solution**:
1. Check `REDIS_URL=${{Redis.REDIS_URL}}` is set
2. Verify Redis service is running
3. If Redis is optional for your deployment, set `REDIS_URL=` (empty) and the entrypoint will skip it

### Issue 4: pgvector Extension Not Found

**Error in logs**:
```
psycopg2.errors.UndefinedFunction: extension "vector" does not exist
```

**Solution**:
Ensure `SKIP_PGVECTOR=1` is set in environment variables. This enables text-based fallback for vector search.

### Issue 5: Migration Errors

**Error in logs**:
```
alembic.util.exc.CommandError: Can't locate revision identified by '...'
```

**Solution**:
1. Check if migrations directory exists in `/backend/alembic/versions/`
2. Verify Alembic configuration in `alembic.ini`
3. If migrations corrupted, may need to reset database (caution: data loss)

### Issue 6: CORS Errors from Frontend

**Error in browser console**:
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution**:
1. Update `FRONTEND_DOMAIN` to your actual Vercel URL
2. Redeploy backend
3. Ensure URL includes protocol (`https://`) and no trailing slash

### Viewing Logs

To see detailed logs:
1. Go to Backend service in Railway
2. Click **"Deployments"** tab
3. Select latest deployment
4. Click **"View Logs"**
5. Use search/filter to find specific errors

---

## Post-Deployment

### Step 1: Deploy Frontend to Vercel

The frontend is deployed separately to Vercel:

1. Go to [vercel.com](https://vercel.com)
2. Import the Osool repository
3. Configure:
   - **Root Directory**: `/web`
   - **Build Command**: `npm run build`
   - **Install Command**: `npm install`

4. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://your-railway-backend.up.railway.app
   ```

5. Deploy

### Step 2: Update CORS Settings

After frontend is deployed:

1. Copy your Vercel URL: `https://your-app.vercel.app`
2. Go to Railway → Backend service → Variables
3. Update: `FRONTEND_DOMAIN=https://your-app.vercel.app`
4. Railway will auto-redeploy

### Step 3: Configure Custom Domain (Optional)

#### For Backend (Railway):
1. Go to Backend service → Settings → Domains
2. Click "Add Custom Domain"
3. Enter your domain: `api.yourdomain.com`
4. Add CNAME record to your DNS:
   ```
   CNAME api.yourdomain.com → your-service.up.railway.app
   ```
5. Railway auto-provisions SSL certificate

#### For Frontend (Vercel):
1. Go to Vercel project → Settings → Domains
2. Add your domain: `www.yourdomain.com`
3. Configure DNS records as instructed by Vercel

### Step 4: Set Up Monitoring (Optional)

#### Sentry Error Tracking:
1. Create account at [sentry.io](https://sentry.io)
2. Create new project for "FastAPI"
3. Copy DSN: `https://...@sentry.io/...`
4. Add to Railway environment: `SENTRY_DSN=your_dsn_here`
5. Redeploy

#### Health Check Monitoring:
Set up external monitoring (UptimeRobot, Pingdom, etc.):
- **Endpoint**: `https://your-backend.up.railway.app/health`
- **Interval**: Every 5 minutes
- **Alert**: On 3 consecutive failures

### Step 5: Database Backups

Railway automatically creates backups for PostgreSQL, but you can also:

1. Set up automated backups using Railway CLI:
   ```bash
   railway run pg_dump > backup_$(date +%Y%m%d).sql
   ```

2. Store backups in cloud storage (S3, Google Cloud Storage)

3. Test restore process periodically

---

## Performance Optimization

### Scaling Guidelines

**Railway Pro Plan** provides:
- Auto-scaling based on CPU/Memory
- Up to 8GB RAM per service
- Dedicated CPU cores

**Recommended Settings**:
- **Gunicorn Workers**: 4 (default, configurable via `WORKERS` env var)
- **Worker Timeout**: 120 seconds (configurable via `TIMEOUT`)
- **Max Connections**: Handled by Railway load balancer

### Database Optimization

1. **Connection Pooling**: Already configured in SQLAlchemy
2. **Indexes**: Auto-created via migrations
3. **Query Optimization**: Monitor slow queries in logs

### Redis Caching

Enable caching for frequently accessed data:
- Property search results (TTL: 5 minutes)
- User sessions (TTL: 24 hours)
- AI responses (TTL: 1 hour)

---

## Security Best Practices

### 1. Environment Variables
- ✅ Use Railway's variable management (encrypted at rest)
- ✅ Never commit secrets to git
- ✅ Rotate keys periodically (every 90 days)
- ✅ Use different keys for staging vs production

### 2. API Keys
- ✅ Restrict OpenAI/Anthropic keys to specific IP ranges if possible
- ✅ Monitor API usage for anomalies
- ✅ Set spending limits on API providers

### 3. Database Security
- ✅ Railway PostgreSQL is private by default (only accessible within project)
- ✅ Use strong passwords (auto-generated by Railway)
- ✅ Enable SSL connections (Railway enforces this)

### 4. CORS
- ✅ Set `FRONTEND_DOMAIN` to your exact domain
- ✅ Never use `FRONTEND_DOMAIN=*` in production
- ✅ Update CORS after any domain changes

### 5. Rate Limiting
- ✅ Backend includes SlowAPI rate limiting
- ✅ Default: 100 requests/minute per IP
- ✅ Configure via `RATE_LIMIT` env var if needed

---

## Cost Estimation

### Railway Pro Plan (Monthly)

| Service | Usage | Est. Cost |
|---------|-------|-----------|
| PostgreSQL | 2GB storage, 1GB RAM | $10-15 |
| Redis | 256MB RAM | $5-10 |
| Backend | 2GB RAM, 2 vCPU | $20-30 |
| **Total** | | **$35-55/month** |

### AI API Costs (Variable)

| Provider | Model | Cost |
|----------|-------|------|
| OpenAI | text-embedding-ada-002 | $0.0001/1K tokens |
| Anthropic | claude-3-5-sonnet | $3.00/1M input, $15.00/1M output |

**Example**: 10,000 AI chat messages/month ≈ $50-100

### Total Monthly Cost: $85-155

---

## Support & Resources

### Railway
- **Documentation**: [docs.railway.app](https://docs.railway.app)
- **Community**: [Railway Discord](https://discord.gg/railway)
- **Status**: [status.railway.app](https://status.railway.app)

### Osool Project
- **GitHub**: [github.com/your-org/osool](https://github.com)
- **Issues**: Report bugs via GitHub Issues

### AI APIs
- **OpenAI Status**: [status.openai.com](https://status.openai.com)
- **Anthropic Status**: [status.anthropic.com](https://status.anthropic.com)

---

## Next Steps

1. ✅ Backend deployed to Railway
2. ✅ Environment variables configured
3. ✅ Health checks passing
4. → Deploy frontend to Vercel
5. → Update CORS settings
6. → Configure custom domains
7. → Set up monitoring
8. → Run load tests
9. → Launch to production!

---

## Changelog

**v1.0.0** (2026-01-13)
- Initial Railway Pro deployment guide
- Added ADMIN_API_KEY configuration
- Added SKIP_PGVECTOR compatibility flag
- Railway-specific entrypoint fixes

---

**Need Help?** Check the [Troubleshooting](#troubleshooting) section or review Railway logs for specific errors.
