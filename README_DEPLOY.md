# Osool Platform - V1.0 Production Deployment Guide

## 🦅 Overview
Osool is a Production-Ready AI & Blockchain Real Estate Platform.
- **Frontend**: Next.js 16 (Wallet Auth)
- **Backend**: FastAPI (Python 3.10)
- **Blockchain**: Polygon Amoy (Web3.py)
- **DB**: Postgres + Supabase (Vector Search)

## 🔑 Key Setup (CTO Mandate)

### 1. Payment Integration (Paymob)
You must obtain these credentials from your Paymob Dashboard:
- `PAYMOB_API_KEY`: The main API Key.
- `PAYMOB_INTEGRATION_ID`: The ID for your "Online Card" integration.
- `PAYMOB_IFRAME_ID`: The ID of your checkout iframe.
- `PAYMOB_HMAC_SECRET`: For validating webhooks.

**Endpoint Flow:**
1. Frontend calls `POST /api/payment/initiate` with user details.
2. Backend returns `iframe_url`.
3. User pays. Paymob sends callback to `/api/webhook/paymob`.
4. Webhook triggers Blockchain Reservation.

### 2. Authentication (Auth Bridge)
We Bridge Web2 and Web3.
- **Frontend**: Signs message `Login to Osool`.
- **Backend (`auth.py`)**: `verify_wallet_signature` checks signature.
- **Auto-Signup**: If wallet is new, a `User` row is created automatically.

### 3. Blockchain (Relayer Pattern)
To prevent "Out of Gas" errors for users:
- The Backend acts as a Relayer using the `PRIVATE_KEY` (Admin).
- Ensure this wallet has sufficient **MATIC/POL** on Amoy Testnet.

## 🐳 Deployment (Docker)

1. **Configure Environment**
   Create `.env` using `.env.example` as a template. Fill in all keys above.

2. **Launch Stack**
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

3. **Verify**
   - API: `http://localhost:8000/docs`
   - Frontend: `http://localhost:3000`

## 🧠 AI Agent ("The Wolf")
The agent is now **Data-Driven**.
- It queries the `properties` SQL table for real market stats (`query_market_stats`).
- It compares prices with **Nawy** (`compare_with_nawy`).
- It performs legal checks on contracts (`audit_contract`).

---
*Built for the Osool CTO Office - Jan 2026*
