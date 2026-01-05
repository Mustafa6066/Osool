# Osool Backend

FastAPI backend for the Osool real estate platform.

## Features

- 🤖 Hybrid AI (XGBoost + GPT-4o) for property valuation
- ⛓️ Blockchain integration (Polygon)
- 💳 EGP payment verification (Paymob-ready)
- 🏢 Fractional investment endpoints

## Local Development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs for API documentation.

## Deploy to Render (Free)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Mustafa6066/Osool)

Or manually:
1. Go to https://render.com
2. New → Web Service → Connect GitHub
3. Select `Osool` repo
4. Render will auto-detect `render.yaml`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for AI features |
| `PRIVATE_KEY` | No | Wallet key for blockchain transactions |
| `OSOOL_REGISTRY_ADDRESS` | No | Deployed contract address |
| `POLYGON_RPC_URL` | No | Defaults to Amoy testnet |
