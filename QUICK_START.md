# 🚀 Osool Quick Start Guide

**Get your production-ready platform running in 30 minutes**

---

## 📋 Prerequisites

- [x] PostgreSQL 15+ installed
- [x] Python 3.10+ installed
- [x] Node.js 18+ installed
- [x] OpenAI API key
- [x] Google OAuth credentials (optional)
- [x] Twilio account (optional)
- [x] SendGrid API key (optional)

---

## ⚡ 5-Minute Setup

### 1. Install Dependencies (2 min)

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../web
npm install
```

### 2. Configure Environment (2 min)

**Create `backend/.env`:**

```bash
# === REQUIRED ===
JWT_SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://postgres:password@localhost:5432/osool
OPENAI_API_KEY=sk-your_key_here

# === OPTIONAL (for full features) ===
ADMIN_API_KEY=$(openssl rand -hex 32)
SENDGRID_API_KEY=SG...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1234567890
GOOGLE_CLIENT_ID=...apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=...
FROM_EMAIL=noreply@osool.com
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
```

**Create `web/.env.local`:**

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id
```

### 3. Set Up Database (1 min)

```bash
# Create database
createdb osool

# Enable pgvector
psql -d osool -c "CREATE EXTENSION vector;"
```

---

## 🎯 Run Data Migration (15 min)

```bash
cd backend
python ingest_data_postgres.py
```

**Wait for:**
```
🎉 Done! All properties migrated to PostgreSQL.
   🔢 Total properties in database: 3274
```

---

## ✅ Integrate Auth Endpoints (2 min)

**Option 1: If you have a main router**

In `backend/app/api/endpoints.py` or your main router file:

```python
from app.api.auth_endpoints import router as auth_router

# Add this where you include routers
router.include_router(auth_router)
```

**Option 2: If you use app.include_router directly**

In `backend/app/main.py`:

```python
from app.api.auth_endpoints import router as auth_router

app.include_router(auth_router)
```

---

## 🚀 Start Services (1 min)

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd web
npm run dev
```

---

## 🧪 Verify Everything Works

### Test 1: Database (10 sec)

```bash
psql -d osool -c "SELECT COUNT(*) FROM properties;"
```

**Expected:** 3274

### Test 2: Backend Health (10 sec)

```bash
curl http://localhost:8000/api/health
```

**Expected:** JSON response with health status

### Test 3: Google OAuth Endpoint (10 sec)

```bash
curl http://localhost:8000/api/auth/google -X POST -H "Content-Type: application/json" -d '{"id_token":"test"}'
```

**Expected:** Error (because token is invalid, but endpoint exists)

### Test 4: Frontend (10 sec)

Open browser: http://localhost:3000

**Expected:** App loads with authentication options

---

## 🎊 You're Ready!

### ✅ What's Working:

1. **Data Layer**
   - PostgreSQL with 3,274 properties
   - Vector search enabled
   - Hallucination prevention active

2. **Authentication**
   - Email/Password (existing)
   - Google OAuth (new endpoint)
   - Phone OTP (new endpoint)
   - Email verification (new endpoint)
   - Password reset (new endpoint)
   - Web3 Wallet (existing)

3. **Security**
   - No hardcoded JWT secret
   - Rate limiting on auth endpoints
   - Input validation

4. **Services**
   - Circuit breakers (ready to integrate)
   - Cost monitoring (ready to integrate)
   - SMS service (ready to use)
   - Email service (ready to use)

---

## 📖 Next Steps

### For Development:
- Read `IMPLEMENTATION_PROGRESS.md` for detailed implementation status
- Check `PRODUCTION_READY_GUIDE.md` for integration details

### For Testing:
- Review test cases in `PRODUCTION_READY_GUIDE.md`
- Run migration verification commands

### For Deployment:
- Follow `PRODUCTION_READY_GUIDE.md` deployment checklist
- Configure production environment variables
- Set up monitoring (Sentry, Prometheus)

---

## ⚠️ Common Issues

### Issue: "Module 'pgvector' not found"
```bash
pip install --upgrade pgvector
```

### Issue: "Could not connect to PostgreSQL"
Check DATABASE_URL format:
```bash
# Correct:
postgresql://user:pass@localhost:5432/osool

# NOT postgres:// (missing 'ql')
```

### Issue: "JWT_SECRET_KEY not set"
```bash
# Add to .env:
JWT_SECRET_KEY=$(openssl rand -hex 32)
```

### Issue: "OpenAI rate limit"
Wait 60 seconds and re-run. The migration script will skip already-inserted properties.

---

## 🆘 Need Help?

1. **Check logs:**
   ```bash
   # Backend logs
   tail -f backend/logs/app.log
   ```

2. **Verify environment:**
   ```bash
   cd backend
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('JWT_SECRET_KEY:', 'SET' if os.getenv('JWT_SECRET_KEY') else 'NOT SET')"
   ```

3. **Test database connection:**
   ```bash
   psql $DATABASE_URL -c "SELECT 1"
   ```

---

## 📞 Documentation Index

- **This Guide:** Quick start (you are here)
- **Migration Details:** `backend/MIGRATION_GUIDE.md`
- **Integration Guide:** `PRODUCTION_READY_GUIDE.md`
- **Implementation Status:** `IMPLEMENTATION_PROGRESS.md`
- **Work Summary:** `COMPLETED_WORK_SUMMARY.md`
- **Master Plan:** `C:\Users\mmoha\.claude\plans\squishy-enchanting-treasure.md`

---

**Congratulations! Your Osool platform is now running with production-grade infrastructure!** 🎉
