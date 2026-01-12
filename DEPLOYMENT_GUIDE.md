# 🚀 Osool Deployment Guide (Phase 1)

This guide covers the deployment of the **Osool Real Estate Platform** (Phase 1: AI Chatting & Selling) to production.

**Architecture:**
- **Backend:** Railway (Python/FastAPI)
- **Frontend:** Vercel (Next.js)
- **Database:** Supabase or Railway Postgres
- **AI:** OpenAI & Anthropic APIs

---

## 1. Preparation & GitHub

Before deploying, ensuring your code is clean and pushed to GitHub.

1.  **Check `.gitignore`**: Ensure `.env`, `__pycache__`, `venv/`, and `.next/` are ignored.
2.  **Commit & Push**:
    ```bash
    git add .
    git commit -m "chore: Prepare for Phase 1 Deployment"
    git push origin main
    ```

---

## 2. Backend Deployment (Railway)

We use **Railway** for the Python Backend because it handles `Dockerfile` and Python dependencies automatically and natively supports FastAPI.

### Step 2.1: Create Project
1.  Go to [Railway.app](https://railway.app/).
2.  Click **"New Project"** -> **"Deploy from GitHub repo"**.
3.  Select your repository (`Mustafa6066/Osool`).
4.  Click **"Deploy Now"**. Railway will detect the `Dockerfile.prod` or `requirements.txt`.

### Step 2.2: Configure Build
1.  Go to **Settings** -> **Build**.
2.  **Root Directory**: `/backend` (Important! Your python code is in the backend folder).
3.  **Watch Paths**: `/backend/**`.

### Step 2.3: Environment Variables (Critical)
Go to the **Variables** tab in Railway and add the following. **Copy these from your local `.env`.**

| Variable | Value / Description |
| :--- | :--- |
| `ENVIRONMENT` | `production` |
| `PORT` | `8000` |
| `DATABASE_URL` | Connection string to your Postgres DB (Railway provides one if you add a Database service, or use Supabase) |
| `OPENAI_API_KEY` | `sk-...` (Your OpenAI Key) |
| `ANTHROPIC_API_KEY` | `sk-...` (Your Claude/AMR Key) |
| `JWT_SECRET_KEY` | Generate a long random string (e.g. `openssl rand -hex 32`) |
| `WALLET_ENCRYPTION_KEY` | Generate with Python Fernet (see `backend/.env.production.example`) |
| `FRONTEND_DOMAIN` | `https://your-project.vercel.app` (You will get this in Section 3) |
| `NEXT_PUBLIC_API_URL` | `https://your-backend.up.railway.app` (Railway provides this) |

> **Note:** If you don't have a database yet, right-click the empty space in Railway project view -> **Create** -> **Database** -> **PostgreSQL**. Railway will automatically verify the `DATABASE_URL` variable.

### Step 2.4: Verify Backend
1.  Once deployed, Railway gives you a public URL (e.g., `https://osool-backend-production.up.railway.app`).
2.  Visit `https://<YOUR_URL>/health`. You should see `{"status": "healthy"}`.
3.  Visit `https://<YOUR_URL>/docs` (might be disabled in prod) or test `/api/chat` via Postman.

---

## 3. Frontend Deployment (Vercel)

We use **Vercel** for the Next.js Frontend.

### Step 3.1: Create Project
1.  Go to [Vercel.com](https://vercel.com/).
2.  Click **"Add New"** -> **"Project"**.
3.  Import `Mustafa6066/Osool`.

### Step 3.2: Configure Build
1.  **Framework Preset**: Next.js.
2.  **Root Directory**: Click "Edit" and select `web`. **(Crucial step!)**

### Step 3.3: Environment Variables
Add the following in the **Environment Variables** section:

| Variable | Value / Description |
| :--- | :--- |
| `NEXT_PUBLIC_API_URL` | `https://<YOUR_RAILWAY_BACKEND_URL>` (No trailing slash, e.g., `https://osool.up.railway.app`) |
| `NEXT_PUBLIC_THIRDWEB_CLIENT_ID`| Your ThirdWeb Client ID |

### Step 3.4: Deploy
1.  Click **"Deploy"**.
2.  Wait for the build to complete.
3.  Vercel will provide a domain (e.g., `osool-web.vercel.app`).

---

## 4. Final Connection Steps

1.  **Update Backend CORS**:
    -   Go back to **Railway** Variables.
    -   Update `FRONTEND_DOMAIN` to your new Vercel domain (e.g., `https://osool-web.vercel.app`).
    -   Redeploy the Backend (Railway usually auto-redeploys on variable changes).

2.  **Test the Full Flow**:
    -   Open your Vercel URL.
    -   Open the **Chat Interface**.
    -   Type "Hello".
    -   **Expected**: The frontend calls your Railway backend, which calls Claude, stores data in Postgres, and replies.

---

## Troubleshooting

-   **Frontend 404 on API calls?**
    -   Check `NEXT_PUBLIC_API_URL` in Vercel. It must match your Railway URL exactly.
    -   Check Browser Console -> Network Tab. See where the request is going.
-   **Backend 500 Error?**
    -   Check Railway **Logs**. It usually means a missing env variable (like `DATABASE_URL` or `OPENAI_API_KEY`).
-   **CORS Error?**
    -   Ensure `FRONTEND_DOMAIN` in Railway matches the Vercel URL exactly (no trailing slash).
