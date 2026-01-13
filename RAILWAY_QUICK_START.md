# Railway Quick Start Checklist

Fast-track guide for deploying Osool to Railway Pro in under 30 minutes.

> **For detailed instructions**, see [RAILWAY_PRO_DEPLOYMENT_GUIDE.md](RAILWAY_PRO_DEPLOYMENT_GUIDE.md)

---

## Pre-Deployment (5 minutes)

### 1. Generate Security Secrets

```bash
cd backend
python generate_secrets.py
```

**Copy and save these 3 keys**:
- [ ] `JWT_SECRET_KEY`
- [ ] `ADMIN_API_KEY` ← **Critical: Missing this will cause deployment failure**
- [ ] `WALLET_ENCRYPTION_KEY`

### 2. Prepare API Keys

- [ ] OpenAI API Key: `sk-proj-...`
- [ ] Anthropic API Key: `sk-ant-api03-...`

### 3. Commit Current Changes

```bash
git status
git add .
git commit -m "chore: prepare for Railway deployment"
git push origin master
```

---

## Railway Setup (15 minutes)

### Step 1: Create Project

- [ ] Go to [railway.app](https://railway.app)
- [ ] Click **"New Project"**
- [ ] Name: `Osool Production`

### Step 2: Add Services

**Add PostgreSQL**:
- [ ] Click **"+ New"** → **"Database"** → **"PostgreSQL"**
- [ ] Wait for provisioning (~30 seconds)

**Add Redis**:
- [ ] Click **"+ New"** → **"Database"** → **"Redis"**
- [ ] Wait for provisioning (~30 seconds)

**Add Backend**:
- [ ] Click **"+ New"** → **"GitHub Repo"**
- [ ] Select **Osool** repository
- [ ] Railway auto-detects Dockerfile

### Step 3: Configure Backend

1. **Click on Backend service** → **"Variables"** tab
2. **Click "RAW Editor"**
3. **Paste the following** (replace placeholders):

```bash
# Core Settings
ENVIRONMENT=production
PORT=8000
PYTHONPATH=/app

# Auto-linked Services
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

# Security Keys (from generate_secrets.py)
JWT_SECRET_KEY=YOUR_JWT_SECRET_KEY_HERE
ADMIN_API_KEY=YOUR_ADMIN_API_KEY_HERE
WALLET_ENCRYPTION_KEY=YOUR_WALLET_ENCRYPTION_KEY_HERE

# AI Services
OPENAI_API_KEY=sk-proj-YOUR_KEY
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY

# Claude Config
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0.3

# Railway Compatibility
SKIP_PGVECTOR=1

# CORS (update after frontend deployment)
FRONTEND_DOMAIN=http://localhost:3000

# Logging
LOG_LEVEL=info

# Feature Flags
ENABLE_BLOCKCHAIN=false
ENABLE_PAYMENTS=false
ENABLE_SMS=false
ENABLE_EMAIL=false
```

4. **Click "Save"**

### Step 4: Deploy

- [ ] Click **"Deploy"** button
- [ ] Monitor build logs (2-3 minutes)
- [ ] Look for: `[+] Osool Backend is ONLINE`

### Step 5: Get Backend URL

- [ ] Go to **Settings** → **Domains**
- [ ] Click **"Generate Domain"**
- [ ] Copy URL: `https://your-service.up.railway.app`

---

## Verification (5 minutes)

### Quick Health Check

```bash
curl https://your-backend.up.railway.app/health
```

**Expected**:
```json
{"status":"healthy","service":"osool-backend"}
```

### Run Full Verification

```bash
./scripts/verify-railway-deployment.sh https://your-backend.up.railway.app
```

**Expected**: All tests pass ✅

---

## Post-Deployment (10 minutes)

### Deploy Frontend (Vercel)

1. **Go to [vercel.com](https://vercel.com)**
2. **Import Osool repo**
3. **Configure**:
   - Root Directory: `/web`
   - Build Command: `npm run build`
4. **Add environment variable**:
   ```
   NEXT_PUBLIC_API_URL=https://your-railway-backend.up.railway.app
   ```
5. **Deploy**

### Update CORS

After frontend is deployed:

1. **Copy Vercel URL**: `https://your-app.vercel.app`
2. **Go to Railway** → Backend → Variables
3. **Update**:
   ```
   FRONTEND_DOMAIN=https://your-app.vercel.app
   ```
4. **Railway auto-redeploys**

---

## Troubleshooting

### ❌ Backend Won't Start

**Error**: `Missing required environment variables: ADMIN_API_KEY`

**Fix**:
1. Go to Railway → Backend → Variables
2. Verify `ADMIN_API_KEY` is set (no spaces, correct value)
3. Redeploy

### ❌ Database Connection Failed

**Error**: `could not connect to server`

**Fix**:
1. Check `DATABASE_URL=${{Postgres.DATABASE_URL}}` (with double braces `{{}}`)
2. Ensure PostgreSQL service is running

### ❌ pgvector Extension Error

**Error**: `extension "vector" does not exist`

**Fix**:
Ensure `SKIP_PGVECTOR=1` is set in environment variables

### ⚠️ CORS Errors

**Error**: `Access blocked by CORS policy`

**Fix**:
1. Update `FRONTEND_DOMAIN` to your Vercel URL (no trailing slash)
2. Redeploy backend

### 📋 View Logs

Railway → Backend → Deployments → Latest → **View Logs**

---

## Environment Variables Checklist

**Required Variables** (backend will fail without these):
- [ ] `ENVIRONMENT=production`
- [ ] `PORT=8000`
- [ ] `DATABASE_URL=${{Postgres.DATABASE_URL}}`
- [ ] `JWT_SECRET_KEY` (from generate_secrets.py)
- [ ] `ADMIN_API_KEY` (from generate_secrets.py) ← **Most common missing variable**
- [ ] `WALLET_ENCRYPTION_KEY` (from generate_secrets.py)
- [ ] `OPENAI_API_KEY` (your API key)
- [ ] `ANTHROPIC_API_KEY` (your API key)
- [ ] `SKIP_PGVECTOR=1`

**Optional Variables**:
- [ ] `REDIS_URL=${{Redis.REDIS_URL}}`
- [ ] `FRONTEND_DOMAIN` (update after Vercel deployment)
- [ ] `LOG_LEVEL=info`
- [ ] `SENTRY_DSN` (for error tracking)

---

## Success Criteria

✅ **Backend Deployed**:
- Health endpoint returns 200 OK
- Logs show "Osool Backend is ONLINE"
- Database migrations completed

✅ **Services Connected**:
- PostgreSQL accessible
- Redis configured (or skipped)
- No connection errors in logs

✅ **API Functional**:
- `/health` returns healthy status
- `/` returns API info
- `/api/properties` returns data

✅ **AI Services Working**:
- OpenAI key valid
- Anthropic key valid
- Chat endpoint responds

✅ **Frontend Connected** (after Vercel deployment):
- CORS configured correctly
- API calls succeed from frontend
- No console errors

---

## Next Steps

1. ✅ Backend running on Railway
2. → Test all endpoints with verification script
3. → Deploy frontend to Vercel
4. → Update CORS settings
5. → Configure custom domains (optional)
6. → Set up monitoring (Sentry, UptimeRobot)
7. → Run load tests
8. → Launch to users!

---

## Quick Reference

| Task | Command/Link |
|------|--------------|
| Generate secrets | `python backend/generate_secrets.py` |
| Railway dashboard | [railway.app/dashboard](https://railway.app/dashboard) |
| Verify deployment | `./scripts/verify-railway-deployment.sh <url>` |
| View logs | Railway → Backend → Deployments → View Logs |
| Health check | `curl https://your-backend.up.railway.app/health` |
| Vercel dashboard | [vercel.com/dashboard](https://vercel.com/dashboard) |

---

## Support

- **Detailed Guide**: [RAILWAY_PRO_DEPLOYMENT_GUIDE.md](RAILWAY_PRO_DEPLOYMENT_GUIDE.md)
- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)

---

**Deployment Time**: ~30 minutes from start to fully functional production backend

🚀 **Ready to deploy? Start with Step 1: Generate Security Secrets**
