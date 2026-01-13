# ✅ Osool Phase 1 Deployment Checklist

Use this checklist to track your deployment progress. Check off items as you complete them.

---

## 🔐 Pre-Deployment (Do This First!)

- [ ] Generate JWT Secret Key (see [GENERATE_KEYS.md](GENERATE_KEYS.md))
- [ ] Generate Wallet Encryption Key
- [ ] Get OpenAI API Key
- [ ] Get Anthropic API Key (for AMR agent)
- [ ] Get Supabase URL and Key
- [ ] Get ThirdWeb Client ID
- [ ] Save all keys in password manager

---

## 🚂 Railway Backend Deployment

### Setup
- [ ] Log in to [Railway.app](https://railway.app/)
- [ ] Create new project
- [ ] Connect GitHub repository: `Mustafa6066/Osool`

### Configure Build
- [ ] Set Root Directory to: `backend`
- [ ] Set Watch Paths to: `backend/**`
- [ ] Verify Dockerfile path: `backend/Dockerfile.prod`

### Database
- [ ] Add PostgreSQL database service
- [ ] Verify `DATABASE_URL` is auto-generated

### Environment Variables
Copy from `RAILWAY_ENV_TEMPLATE.txt` and add:

- [ ] `ENVIRONMENT=production`
- [ ] `PORT=8000`
- [ ] `PYTHONPATH=/app`
- [ ] `DATABASE_URL=${{Postgres.DATABASE_URL}}`
- [ ] `OPENAI_API_KEY=sk-proj-...`
- [ ] `ANTHROPIC_API_KEY=sk-ant-api03-...`
- [ ] `CLAUDE_MODEL=claude-3-5-sonnet-20241022`
- [ ] `CLAUDE_MAX_TOKENS=4096`
- [ ] `CLAUDE_TEMPERATURE=0.3`
- [ ] `SUPABASE_URL=https://...`
- [ ] `SUPABASE_KEY=...`
- [ ] `JWT_SECRET_KEY=...` (generated)
- [ ] `WALLET_ENCRYPTION_KEY=...` (generated)
- [ ] `FRONTEND_DOMAIN=http://localhost:3000` (update later)
- [ ] `LOG_LEVEL=info`
- [ ] Optional: `SENTRY_DSN=...`

### Deploy & Verify
- [ ] Click Deploy
- [ ] Wait for build to complete (3-5 minutes)
- [ ] Copy Railway URL (e.g., `https://osool-backend-production.up.railway.app`)
- [ ] Test health endpoint: `https://YOUR_URL/health`
- [ ] Expected: `{"status": "healthy"}`

---

## ▲ Vercel Frontend Deployment

### Setup
- [ ] Log in to [Vercel.com](https://vercel.com/)
- [ ] Click "Add New" → "Project"
- [ ] Import GitHub repository: `Mustafa6066/Osool`

### Configure Build
- [ ] Set Framework Preset: Next.js
- [ ] **CRITICAL:** Set Root Directory to: `web`
- [ ] Verify Build Command: `npm run build`
- [ ] Verify Output Directory: `.next`

### Environment Variables
Copy from `VERCEL_ENV_TEMPLATE.txt` and add:

- [ ] `NEXT_PUBLIC_API_URL=https://YOUR_RAILWAY_URL`
- [ ] `NEXT_PUBLIC_THIRDWEB_CLIENT_ID=...`

### Deploy & Verify
- [ ] Click Deploy
- [ ] Wait for build to complete (2-3 minutes)
- [ ] Copy Vercel URL (e.g., `https://osool-web.vercel.app`)
- [ ] Open URL in browser - verify site loads

---

## 🔗 Connect Services

### Update CORS
- [ ] Go back to Railway Variables
- [ ] Update `FRONTEND_DOMAIN` to Vercel URL
- [ ] Example: `https://osool-web.vercel.app`
- [ ] **NO TRAILING SLASH!**
- [ ] Wait for Railway to redeploy (2-3 minutes)

---

## 🧪 End-to-End Testing

### Test AI Chat
- [ ] Open Vercel URL
- [ ] Navigate to Chat interface
- [ ] Send message: "Hello"
- [ ] Verify AMR agent responds
- [ ] Test property query: "Show me villas in New Cairo"
- [ ] Verify intelligent response with property data

### Test Authentication
- [ ] Try sign up flow
- [ ] Try sign in flow
- [ ] Verify JWT tokens are issued
- [ ] Test protected endpoints

### Check Logs
- [ ] Railway: Check deployment logs for errors
- [ ] Vercel: Check deployment logs for errors
- [ ] Browser: Open DevTools Console - verify no errors

---

## 📊 Monitoring Setup

### Railway
- [ ] Enable metrics in Railway dashboard
- [ ] Set up alerts for high CPU/memory
- [ ] Monitor request count and errors

### Vercel
- [ ] Enable Web Analytics (included in Pro)
- [ ] Check page load performance
- [ ] Monitor visitor count

### Optional: Sentry
- [ ] Create Sentry project
- [ ] Add `SENTRY_DSN` to Railway
- [ ] Verify error tracking works

---

## 🎯 Post-Deployment Validation

- [ ] Backend health endpoint returns 200 OK
- [ ] Frontend loads without errors
- [ ] AI chat works end-to-end
- [ ] Authentication flow works
- [ ] No CORS errors in browser console
- [ ] Railway dashboard shows healthy service
- [ ] Vercel dashboard shows successful deployment
- [ ] Database migrations ran successfully
- [ ] Vector store is accessible (Supabase)

---

## 🚨 Common Issues Checklist

If something doesn't work, verify:

- [ ] Railway Root Directory is `backend` (not root!)
- [ ] Vercel Root Directory is `web` (not root!)
- [ ] All environment variables are set correctly
- [ ] No typos in URLs
- [ ] No trailing slashes in URLs
- [ ] API keys are valid and not expired
- [ ] Supabase project is active
- [ ] Database is connected in Railway
- [ ] Both services finished deploying

---

## ✅ Deployment Complete!

When all items are checked:

🎉 **Congratulations!** Your Osool Phase 1 is live!

### Share your deployment:
- Frontend: `https://YOUR_VERCEL_URL`
- Backend API: `https://YOUR_RAILWAY_URL`

### Next Steps:
1. Test with real users
2. Monitor performance and errors
3. Set up custom domain (optional)
4. Prepare for Phase 2 (Blockchain)

---

**Deployment Date:** __________
**Frontend URL:** __________
**Backend URL:** __________
**Deployed By:** __________

---

**Need Help?**
- Review: [PHASE1_DEPLOYMENT_ACTION_PLAN.md](PHASE1_DEPLOYMENT_ACTION_PLAN.md)
- Check Railway logs
- Check Vercel deployment logs
- Review browser console for errors
