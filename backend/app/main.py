"""
Osool Backend - Main FastAPI Application
-----------------------------------------
State-of-the-art Real Estate Platform for Egyptian Market

Features:
- AI-powered contract analysis (Egyptian Real Estate Law)
- Smart property valuation with market reasoning
- EGP payment verification (InstaPay/Fawry)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Logger
logger = logging.getLogger("osool")
logging.basicConfig(level=logging.INFO)
# Silence SQLAlchemy SQL echo at INFO level (prevents Railway log flood)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

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
    logger.info("✅ Sentry error tracking enabled")
else:
    logger.warning("⚠️ Sentry DSN not configured - error tracking disabled")

logger.info("🐺 WOLF OF OSOOL: PROTOCOL 6 ACTIVATED (New Version Loaded)")
logger.info("✅ Velvet Rope Gating: ENABLED")
logger.info("✅ Market Intel Injection: ENABLED")

# Import routers
from app.api.endpoints import router as api_router
from app.api.auth_endpoints import router as auth_router
from app.api.gamification_endpoints import router as gamification_router
from app.api.admin_endpoints import router as admin_router
from app.api.ticket_endpoints import router as ticket_router
from app.api.seo_endpoints import router as seo_router
from app.api.intent_endpoints import router as intent_router
from app.api.lead_endpoints import router as lead_router
from app.api.consultation_endpoints import router as consultation_router
from app.api.email_endpoints import router as email_router
from app.api.analytics_endpoints import router as analytics_router
from app.api.campaign_endpoints import router as campaign_router
from app.api.health_endpoints import router as health_router
from app.api.orchestrator_endpoints import router as orchestrator_router
from app.api.orchestrator_endpoints import user_prefs_router
from app.api.pricing_router import router as pricing_router
from app.services.metrics import metrics_endpoint

# ═══════════════════════════════════════════════════════════════
# APPLICATION SETUP
# ═══════════════════════════════════════════════════════════════

# Security: Disable API documentation in production
_is_production = os.getenv("ENVIRONMENT") == "production"


# ═══════════════════════════════════════════════════════════════
# LIFESPAN (replaces deprecated @app.on_event)
# Compatible with FastAPI >= 0.93 / Starlette >= 0.20
# ═══════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup then yield then shutdown."""
    # ── STARTUP ────────────────────────────────────────────────
    import os as _os
    logger.info("🚀 Osool Backend Starting...")

    environment = _os.getenv("ENVIRONMENT", "development")
    if environment == "production":
        required_vars = [
            "JWT_SECRET_KEY",
            "DATABASE_URL",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
        ]
        missing_vars = [v for v in required_vars if not _os.getenv(v)]
        if missing_vars:
            logger.error(
                "CRITICAL: Missing required environment variables: %s",
                ", ".join(missing_vars),
            )

    try:
        from app.database import init_db
        await init_db()
        logger.info("✅ Database tables: VERIFIED")
    except Exception as e:
        logger.warning("⚠️ Database tables: init_db skipped (%s)", e)

    try:
        from app.ingest_pipeline import create_valuation_tables
        await create_valuation_tables()
        logger.info("✅ Valuation Pipeline: valuation_listings table READY")
    except Exception as e:
        logger.warning("⚠️ Valuation Pipeline: table init skipped (%s)", e)

    try:
        from sqlalchemy import select
        from app.database import AsyncSessionLocal
        from app.models import MarketIndicator
        from app import valuation_engine as _ve

        async with AsyncSessionLocal() as session:
            row = await session.scalar(
                select(MarketIndicator).where(MarketIndicator.key == "bank_cd_rate")
            )
        if row and row.value:
            _ve.set_cbe_rate(float(row.value), source=f"db:{row.source or 'unknown'}")
            logger.info(
                "✅ CBE Rate: %.4f (from MarketIndicator, updated %s)",
                row.value,
                row.last_updated,
            )
        else:
            logger.info(
                "ℹ️ CBE Rate: %.4f (env/default — no MarketIndicator row)",
                _ve.get_cbe_rate(),
            )
    except Exception as e:
        logger.warning("⚠️ CBE Rate refresh skipped (%s) — using %.4f", e, 0.22)

    try:
        from app.intelligence_loop import create_intelligence_tables, start_intelligence_worker
        await create_intelligence_tables()
        await start_intelligence_worker()
        logger.info("✅ Intelligence Loop: telemetry tables READY, drift worker STARTED")
    except Exception as e:
        logger.warning("⚠️ Intelligence Loop: startup skipped (%s)", e)

    try:
        from app.database import AsyncSessionLocal
        from app.services.gamification import gamification_engine
        async with AsyncSessionLocal() as session:
            await gamification_engine.seed_achievements(session)
        logger.info("✅ Gamification Engine: ACHIEVEMENTS SEEDED")
    except Exception as e:
        logger.warning("⚠️ Gamification Engine: Seed skipped (%s)", e)

    try:
        from app.services.scheduler import init_scheduler
        init_scheduler()
    except Exception as e:
        logger.warning("⚠️ APScheduler: Init skipped (%s)", e)

    try:
        from app.services.cache import cache
        if cache.redis:
            cache.redis.ping()
            logger.info("✅ Redis: CONNECTED (token blacklist active)")
        elif _os.getenv("ENVIRONMENT") == "production":
            logger.error("❌ Redis: UNAVAILABLE in production — token blacklist degraded!")
        else:
            logger.warning("⚠️ Redis: Not configured (using in-memory fallback)")
    except Exception as e:
        if _os.getenv("ENVIRONMENT") == "production":
            logger.error("❌ Redis: Connection failed in production — %s", e)
        else:
            logger.warning("⚠️ Redis: Connection failed (%s)", e)

    logger.info("✅ AI Intelligence Layer: READY")
    logger.info("✅ CoInvestor Agent (Claude 3.5 Sonnet): READY")
    logger.info("✅ Hybrid Brain (XGBoost + GPT-4o): READY")
    logger.info("✅ Gamification Engine: READY")
    logger.info("✅ Semantic Search (pgvector): READY")
    logger.info("🎉 Osool Backend is ONLINE (Environment: %s)", environment)
    logger.info("🐺 Phase 9: AI + Gamification Platform")

    yield  # ── Application runs here ──────────────────────────

    # ── SHUTDOWN ───────────────────────────────────────────────
    try:
        from app.services.scheduler import shutdown_scheduler
        shutdown_scheduler()
    except Exception:
        pass
    try:
        from app.intelligence_loop import stop_intelligence_worker
        await stop_intelligence_worker()
    except Exception:
        pass
    logger.info("👋 Osool Backend shutting down")


app = FastAPI(
    title="Osool API",
    description="""
    🏠 **Osool (أصول)** - AI-Powered Real Estate Platform for Egypt

    ## Features

    ### 🤖 AI Intelligence Layer
    - **CoInvestor AI Agent**: Chat with Claude 3.5 Sonnet for property search in Egyptian Arabic & English
    - **Smart Valuation**: XGBoost + GPT-4o hybrid pricing model with market reasoning
    - **Natural Language Search**: Semantic search across 3,274 verified properties
    - **Visual Analytics**: Investment scorecards, payment timelines, market trends, comparison charts
    - **Proactive Recommendations**: CoInvestor suggests properties and analyses automatically

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
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    lifespan=lifespan,
)

# ═══════════════════════════════════════════════════════════════
# CORS MIDDLEWARE
# ═══════════════════════════════════════════════════════════════

import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Rate Limiter (per-IP; user-aware limiter used by /api/v1/chat lives in
# app/middleware/rate_limiting.py — they share storage via storage_uri).
limiter = Limiter(key_func=get_remote_address)

# ═══════════════════════════════════════════════════════════════
# CORS MIDDLEWARE
# ═══════════════════════════════════════════════════════════════

# Get frontend domain and strip trailing slash AND any path
frontend_domain = os.getenv("FRONTEND_DOMAIN", "https://osool-ten.vercel.app").rstrip("/")
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
    "https://osool-ten.vercel.app", # Latest Vercel deployment
    "https://osool.eg",  # Production (Core)
    "https://osool-production.up.railway.app",  # Railway deployment
]

extra_origins = os.getenv("ALLOWED_ORIGINS", "")
if extra_origins:
    origins.extend([o.strip() for o in extra_origins.split(",") if o.strip()])

# Keep order stable while removing duplicates
origins = list(dict.fromkeys(origins))

if os.getenv("ENVIRONMENT") == "production":
    origins = [o for o in origins if not o.startswith("http://localhost")]

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
logger.info(f"CORS Origins configured: {origins}")
logger.info(f"Vercel preview URLs also allowed via wildcard pattern")

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

        # Security Fix M2: Tightened CSP — removed unsafe-eval, kept unsafe-inline
        # for styles only (Next.js requires it). Scripts restricted to self + CDN.
        # wss:// restricted to explicit known hostnames (bare wss:// is a wildcard).
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            # MEDIUM-10 fix: removed https://api.openai.com (backend only, not browser);
            # corrected wss domain to osool-ten.vercel.app
            "connect-src 'self' https://osool-ten.vercel.app wss://osool.eg wss://osool-ten.vercel.app"
        )

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response

# Simple in-memory rate limiter (safety net)
from app.middleware.simple_rate_limiter import SimpleRateLimiterMiddleware
from app.middleware.csrf_protection import CSRFProtectionMiddleware

# NOTE: Middleware order matters in FastAPI (LIFO - Last In First Out)
# Middleware added LAST executes FIRST in the request chain.
# Order (outer → inner): CORS → Rate Limiter → CSRF → Security Headers

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFProtectionMiddleware, allowed_origins=origins)  # CRITICAL-3 fix: was defined but never registered
app.add_middleware(SimpleRateLimiterMiddleware)

# CORS MIDDLEWARE - MUST BE ADDED LAST (executes first in middleware chain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # MEDIUM-9 fix: Anchor regex with ^ and $ so a string like
    # "https://evil.com/https://osool-abc-mustafas-projects-xyz.vercel.app" doesn't bypass it
    allow_origin_regex=r"^https://osool-[a-z0-9]+-mustafas-projects-[a-z0-9]+\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Key", "X-CSRF-Token"],
    expose_headers=["X-CSRF-Token"],
)

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
    # Log internal error without exposing details to clients
    logger.exception("Unhandled exception during request: %s %s", request.method, request.url)

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

from app.api.chat import router as chat_router
app.include_router(chat_router, prefix="/api/v1")
app.include_router(api_router)
app.include_router(auth_router)
app.include_router(gamification_router)
app.include_router(admin_router)
app.include_router(ticket_router)
app.include_router(seo_router)
app.include_router(intent_router)
app.include_router(lead_router)
app.include_router(consultation_router)
app.include_router(email_router)
app.include_router(analytics_router)
app.include_router(campaign_router)

# Billing: always registered — GET /plans powers /pricing even when payments
# are disabled; pay endpoints themselves return 503 in that case.
from app.api.billing_endpoints import router as billing_router
app.include_router(billing_router)

# Buyer tools: mortgage (تمويل عقاري) + installment-vs-cash calculators
from app.api.tools_endpoints import router as tools_router
app.include_router(tools_router)

# Simple health endpoint registered FIRST so Railway healthcheck always
# gets a fast 200 regardless of startup-event completion status.
@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "osool-backend"}

app.include_router(health_router)
app.include_router(orchestrator_router)
app.include_router(user_prefs_router)
app.include_router(pricing_router)

try:
    from app.ingest_pipeline import router as ingest_router
    app.include_router(ingest_router)
except Exception as _e:
    logger.error("Failed to load ingest_pipeline router: %s", _e)

try:
    from app.intelligence_loop import router as intelligence_router
    app.include_router(intelligence_router)
except Exception as _e:
    logger.error("Failed to load intelligence_loop router: %s", _e)

try:
    from app.api.freemium_router import router as freemium_router
    app.include_router(freemium_router)
except Exception as _e:
    logger.error("Failed to load freemium_router: %s", _e)


@app.get("/")
def root():
    """Root endpoint - API status"""
    # SECURITY: Never expose version, phase, or internal feature names.
    # Attackers use version strings to look up known CVEs.
    return {"status": "online", "service": "Osool API"}


# Security Fix H4: Lazy import of verify_api_key to protect metrics
from fastapi import Depends as _Depends
from fastapi.security import APIKeyHeader as _APIKeyHeader

_metrics_api_key_header = _APIKeyHeader(name="X-Admin-Key", auto_error=False)

async def _verify_metrics_key(api_key: str = _Depends(_metrics_api_key_header)):
    import secrets as _sec
    admin_key = os.getenv("ADMIN_API_KEY")
    if not admin_key or not _sec.compare_digest(api_key or "", admin_key):
        from fastapi import HTTPException as _HTTPExc
        raise _HTTPExc(status_code=403, detail="Invalid API Key")

@app.get("/metrics")
def metrics(_key: str = _Depends(_verify_metrics_key)):
    """
    Prometheus metrics endpoint - Phase 4.1: Monitoring

    Returns metrics in Prometheus format for scraping.
    Includes: API requests, OpenAI usage, database performance, business metrics.

    Access: Protected with X-Admin-Key header.
    """
    return metrics_endpoint()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
