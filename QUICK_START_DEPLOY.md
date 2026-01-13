# 🚀 Osool Phase 1 - Quick Start Deployment

**Goal:** Get your AMR AI Agent live on Vercel Pro + Railway Pro in under 30 minutes.

---

## 📚 Documentation Files

1. **This file** - Quick start (you are here!)
2. [PHASE1_DEPLOYMENT_ACTION_PLAN.md](PHASE1_DEPLOYMENT_ACTION_PLAN.md) - Detailed guide
3. [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Step-by-step checklist
4. [GENERATE_KEYS.md](GENERATE_KEYS.md) - How to generate security keys
5. [RAILWAY_ENV_TEMPLATE.txt](RAILWAY_ENV_TEMPLATE.txt) - Railway environment variables
6. [VERCEL_ENV_TEMPLATE.txt](VERCEL_ENV_TEMPLATE.txt) - Vercel environment variables

---

## ⚡ Ultra-Quick Deploy (For the Impatient)

### 1. Generate Keys (5 minutes)

```bash
# JWT Secret
python -c "import secrets; print(secrets.token_hex(32))"

# Wallet Encryption Key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Save these + your API keys in a secure note.

### 2. Deploy Backend to Railway (10 minutes)

1. Go to [railway.app](https://railway.app/) → New Project → Deploy from GitHub
2. Select: `Mustafa6066/Osool`
3. Settings → Root Directory: `backend`
4. Add PostgreSQL database
5. Copy all variables from `RAILWAY_ENV_TEMPLATE.txt` to Variables tab
6. Wait for deploy → Copy Railway URL

### 3. Deploy Frontend to Vercel (5 minutes)

1. Go to [vercel.com](https://vercel.com/) → New Project → Import from GitHub
2. Select: `Mustafa6066/Osool`
3. **CRITICAL:** Root Directory: `web`
4. Add variables from `VERCEL_ENV_TEMPLATE.txt`
5. Deploy → Copy Vercel URL

### 4. Connect Services (5 minutes)

1. Go back to Railway → Variables
2. Update `FRONTEND_DOMAIN` to your Vercel URL
3. Wait for redeploy

### 5. Test (5 minutes)

1. Open Vercel URL
2. Go to Chat
3. Type: "Show me villas in New Cairo"
4. AMR agent should respond!

---

## 🎯 What You're Deploying

### AMR (Advanced Multi-Reasoning) Agent
Your AI agent powered by Claude 3.5 Sonnet that:
- Answers property questions intelligently
- Retrieves data from Supabase vector store
- Maintains conversation context
- Provides personalized recommendations

### Tech Stack
- **Frontend:** Next.js 16 on Vercel Pro
- **Backend:** FastAPI (Python) on Railway Pro
- **Database:** PostgreSQL (Railway)
- **Vector Store:** Supabase (for RAG)
- **AI:** Claude 3.5 Sonnet + OpenAI Embeddings

---

## 🔑 Required Accounts & Keys

| Service | Purpose | Get It From |
|---------|---------|-------------|
| Railway Pro | Backend hosting | [railway.app](https://railway.app/) |
| Vercel Pro | Frontend hosting | [vercel.com](https://vercel.com/) |
| OpenAI | Embeddings | [platform.openai.com](https://platform.openai.com/api-keys) |
| Anthropic | AMR Agent (Claude) | [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| Supabase | Vector database | [supabase.com](https://supabase.com/) |
| ThirdWeb | Wallet (optional for Phase 1) | [thirdweb.com](https://thirdweb.com/dashboard) |

---

## 🚨 Common Mistakes to Avoid

1. ❌ **Wrong Root Directory**
   - Railway: Must be `backend`
   - Vercel: Must be `web`

2. ❌ **Trailing Slashes in URLs**
   - ✅ `https://api.example.com`
   - ❌ `https://api.example.com/`

3. ❌ **CORS Mismatch**
   - Railway `FRONTEND_DOMAIN` must match Vercel URL exactly

4. ❌ **Missing Environment Variables**
   - Use the templates! Don't skip any variables.

5. ❌ **Deploying Before Generating Keys**
   - Generate JWT and Wallet keys FIRST

---

## 📊 Health Check Endpoints

After deployment, verify these URLs work:

### Backend Health
```
https://YOUR_RAILWAY_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-13T...",
  "database": "connected",
  "ai_service": "ready"
}
```

### Detailed Health
```
https://YOUR_RAILWAY_URL/health/detailed
```

Shows status of all services (database, AI, circuit breakers).

### Version Info
```
https://YOUR_RAILWAY_URL/health/version
```

Shows app version and enabled features.

---

## 🔍 Troubleshooting Quick Fixes

### Frontend shows 404 on API calls
```bash
# Check Vercel environment variables
NEXT_PUBLIC_API_URL=https://YOUR_RAILWAY_URL
# No trailing slash!
```

### Backend returns 500
```bash
# Check Railway logs
# Common issues:
# - Missing DATABASE_URL (add PostgreSQL service)
# - Missing OPENAI_API_KEY or ANTHROPIC_API_KEY
# - Invalid Supabase credentials
```

### CORS Error in Browser
```bash
# Railway Variables → Update:
FRONTEND_DOMAIN=https://your-exact-vercel-url.vercel.app
# Must match exactly, no trailing slash
```

### AI Chat doesn't respond
```bash
# Check:
# 1. Railway logs for API errors
# 2. ANTHROPIC_API_KEY is valid
# 3. SUPABASE_URL and SUPABASE_KEY are correct
# 4. Vector store has data (run ingest_data.py locally first)
```

---

## 📈 Post-Deployment Checklist

- [ ] Backend `/health` endpoint returns 200 OK
- [ ] Frontend loads without errors
- [ ] Chat interface connects to backend
- [ ] AMR agent responds to queries
- [ ] No CORS errors in browser console
- [ ] Railway dashboard shows healthy metrics
- [ ] Vercel deployment is successful

---

## 🎉 Success!

If all checks pass, your Osool Phase 1 is LIVE!

### What's Working:
✅ AI-powered property chat (AMR Agent)
✅ Intelligent recommendations
✅ RAG-based property retrieval
✅ Conversation memory
✅ Production-ready infrastructure

### Share Your Deployment:
- **Frontend:** `https://your-project.vercel.app`
- **API Docs:** `https://your-railway-url.up.railway.app/health/version`

---

## 🔄 Next Steps

1. **Test with Real Users**
   - Share the Vercel URL
   - Get feedback on AI responses

2. **Monitor Performance**
   - Check Railway metrics
   - Review Vercel analytics

3. **Optimize**
   - Review cost tracking endpoint: `/health/costs`
   - Adjust rate limits if needed

4. **Custom Domain** (Optional)
   - Add your domain in Vercel settings
   - Update Railway CORS

5. **Prepare Phase 2**
   - Blockchain integration
   - Property tokenization

---

## 💡 Pro Tips

1. **Enable Vercel Analytics** - Included in Pro plan
2. **Set up Railway Alerts** - Get notified of issues
3. **Use Sentry for Error Tracking** - Optional but recommended
4. **Monitor API Costs** - Check `/health/costs` endpoint regularly
5. **Test Different Queries** - Ensure AMR responds well

---

## 📞 Need Help?

1. Check [PHASE1_DEPLOYMENT_ACTION_PLAN.md](PHASE1_DEPLOYMENT_ACTION_PLAN.md) for detailed steps
2. Review [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
3. Check Railway deployment logs
4. Check Vercel deployment logs
5. Review browser DevTools console

---

**Deployment Time:** ~30 minutes
**Difficulty:** Intermediate
**Cost:** ~$20-40/month (Railway Pro + Vercel Pro + API usage)

**Last Updated:** January 13, 2026
