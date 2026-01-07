"""
Osool Backend - Main FastAPI Application
-----------------------------------------
State-of-the-art Real Estate Platform for Egyptian Market

Features:
- Legal-compliant blockchain registry (CBE Law 194)
- AI-powered contract analysis (Egyptian Real Estate Law)
- Smart property valuation with market reasoning
- EGP payment verification (InstaPay/Fawry)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from app.api.endpoints import router as api_router

# ═══════════════════════════════════════════════════════════════
# APPLICATION SETUP
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="Osool API",
    description="""
    🏠 **Osool (أصول)** - State-of-the-Art Real Estate Platform
    
    ## Features
    
    ### 🔗 Blockchain Registry (CBE Law 194 Compliant)
    - Property listing and status tracking
    - Immutable ownership records
    - EGP payments via InstaPay/Fawry (no crypto)
    
    ### 🤖 AI Intelligence Layer
    - **Legal Contract Analysis**: Scans for Egyptian real estate scams
    - **Smart Valuation**: AI-powered price estimation with reasoning
    - **Price Comparison**: Is the asking price fair?
    
    ### 💳 Payment Flow
    1. User pays via InstaPay/Fawry (EGP)
    2. Backend verifies payment
    3. Blockchain status updated
    4. User receives TX hash as proof
    """,
    version="1.0.0",
    """,
    version="1.0.0",
    docs_url=None, # Disabled for Production Security
    redoc_url=None
)

# ═══════════════════════════════════════════════════════════════
# CORS MIDDLEWARE
# ═══════════════════════════════════════════════════════════════

import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

# ═══════════════════════════════════════════════════════════════
# CORS MIDDLEWARE
# ═══════════════════════════════════════════════════════════════

origins = [
    "http://localhost:3000", # Dev
    "http://localhost:8000", # Swagger
    os.getenv("FRONTEND_DOMAIN", "https://osool.com"), # Production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ═══════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════

app.include_router(api_router)


@app.get("/")
def root():
    """Root endpoint - API status"""
    return {
        "name": "Osool API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "features": [
            "blockchain_registry",
            "ai_contract_analysis",
            "ai_valuation",
            "egp_payment_verification"
        ]
    }


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "osool-backend"}


# ═══════════════════════════════════════════════════════════════
# STARTUP EVENT
# ═══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    print("[*] Osool Backend Starting...")
    print("    |-- AI Intelligence Layer: READY")
    print("    |-- Blockchain Service: READY")
    print("    +-- Payment Verification: READY")
    print("[+] Osool Backend is ONLINE")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
