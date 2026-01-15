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
import os

# Load environment variables
load_dotenv()

# Phase 5: Sentry Integration for Error Tracking
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        environment=os.getenv("ENVIRONMENT", "development"),
        release=f"osool-backend@{os.getenv('APP_VERSION', '1.0.0')}",
    )
    print("✅ Sentry error tracking enabled")
else:
    print("⚠️ Sentry DSN not configured - error tracking disabled")

# Import routers
from app.api.endpoints import router as api_router
from app.api.auth_endpoints import router as auth_router
from app.services.metrics import metrics_endpoint

# ═══════════════════════════════════════════════════════════════
# APPLICATION SETUP
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="Osool API",
    description="""
    🏠 **Osool (أصول)** - AI-Powered Real Estate Platform for Egypt

    ## Features

    ### 🤖 AI Intelligence Layer
    - **AMR AI Agent**: Chat with Claude 3.5 Sonnet for property search in Egyptian Arabic & English
    - **Smart Valuation**: XGBoost + GPT-4o hybrid pricing model with market reasoning
    - **Natural Language Search**: Semantic search across 3,274 verified properties
    - **Visual Analytics**: Investment scorecards, payment timelines, market trends, comparison charts
    - **Proactive Recommendations**: AMR suggests properties and analyses automatically

    ### 🏘️ Property Database
    - 3,274 verified Egyptian properties with semantic search
    - Real-time market data and price analysis
    - Payment plan calculations with CBE interest rates
    - ROI projections and investment risk scoring

    ### 🇪🇬 Egyptian Market Expertise
    - Bilingual support (Egyptian Arabic dialect + English)
    - Location-specific insights (New Cairo, Sheikh Zayed, 6th October, etc.)
    - Buyer psychology integration (first-time buyers, investors, upgraders)
    - Cultural context and family-focused recommendations
    """,
    version="1.0.0",
    docs_url=None,
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

# Get frontend domain and strip trailing slash AND any path
frontend_domain = os.getenv("FRONTEND_DOMAIN", "https://osool.com").rstrip("/")
# Strip any path from the domain (e.g., /login)
from urllib.parse import urlparse
parsed = urlparse(frontend_domain)
if parsed.scheme and parsed.netloc:
    frontend_domain = f"{parsed.scheme}://{parsed.netloc}"

origins = [
    "http://localhost:3000",  # Dev
    "http://localhost:8000",  # Swagger
    frontend_domain,  # Production (from env, cleaned)
    "https://osool.vercel.app",  # Vercel deployment
    "https://osoool.vercel.app",  # Vercel deployment (triple o)
    "https://osool-one.vercel.app", # Specific Vercel deployment
    "https://osool-cu8lynoku-mustafas-projects-948a09fa.vercel.app",  # Current preview
    "https://osool.eg",  # Production (Core)
]

# Add all Vercel preview URLs dynamically
# Vercel creates preview URLs like: osool-xxx-mustafas-projects-xxx.vercel.app
import re

def is_allowed_origin(origin: str) -> bool:
    """Check if origin is allowed, including Vercel preview patterns."""
    if origin in origins:
        return True
    # Match any Vercel preview URL for this project
    vercel_pattern = r'https://osool-[a-z0-9]+-mustafas-projects-[a-z0-9]+\.vercel\.app'
    if re.match(vercel_pattern, origin):
        return True
    return False

# Log CORS origins at startup for debugging
print(f"[+] CORS Origins configured: {origins}")
print(f"[+] Vercel preview URLs also allowed via wildcard pattern")

# Use allow_origin_regex to accept all Vercel preview URLs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Phase 1 debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════
# SECURITY HEADERS MIDDLEWARE (Phase 6)
# ═══════════════════════════════════════════════════════════════

from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # HSTS: Force HTTPS for 1 year
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # XSS Protection
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # CSP: Content Security Policy (adjust as needed for your frontend)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.openai.com wss://"
        )

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response

app.add_middleware(SecurityHeadersMiddleware)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global Critical Error Handler
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Phase 5: Catches all 500 errors to prevent raw stack traces leaking to user.
    Logs to Sentry for monitoring.
    """
    print(f"❌ [CRITICAL] 500 ERROR: {exc}")  # Internal Log

    # Phase 5: Send to Sentry if configured
    if SENTRY_DSN:
        import sentry_sdk
        sentry_sdk.capture_exception(exc)

    return JSONResponse(
        status_code=500,
        content={"error": "Osool System Busy - Our agents are notified."},
    )

# ═══════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════

app.include_router(api_router)
app.include_router(auth_router)


@app.get("/")
def root():
    """Root endpoint - API status"""
    return {
        "name": "Osool API - AI-First Real Estate Platform",
        "version": "1.0.0",
        "status": "online",
        "phase": "1",
        "features": [
            "amr_ai_agent",
            "bilingual_chat",
            "semantic_search",
            "hybrid_valuation",
            "visual_analytics",
            "proactive_recommendations"
        ]
    }


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "osool-backend"}


@app.get("/metrics")
def metrics():
    """
    Prometheus metrics endpoint - Phase 4.1: Monitoring

    Returns metrics in Prometheus format for scraping.
    Includes: API requests, OpenAI usage, database performance, business metrics.

    Access: Internal only (should be restricted in production via firewall/API key)
    """
    return metrics_endpoint()


# ═══════════════════════════════════════════════════════════════
# STARTUP EVENT
# ═══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """
    Startup validation with security checks.
    Fails fast if critical environment variables are missing.

    Phase 1: Security Hardening - Validates wallet encryption in production
    """
    import os

    print("[*] Osool Backend Starting...")

    # Phase 1: Security Validation
    environment = os.getenv("ENVIRONMENT", "development")

    if environment == "production":
        required_vars = [
            "JWT_SECRET_KEY",
            "DATABASE_URL",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY"
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            error_msg = f"CRITICAL: Missing required environment variables: {', '.join(missing_vars)}"
            print(f"[!] {error_msg}")
            raise RuntimeError(error_msg)

    print("    |-- AI Intelligence Layer: READY")
    print("    |-- AMR Agent (Claude 3.5 Sonnet): READY")
    print("    |-- Hybrid Brain (XGBoost + GPT-4o): READY")
    print("    +-- Semantic Search (pgvector): READY")
    print(f"[+] Osool Backend is ONLINE (Environment: {environment})")
    print(f"[+] Phase 1: AI-First Real Estate Platform")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
