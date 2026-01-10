"""
Production Configuration with Strict Environment Variable Validation
---------------------------------------------------------------------
This module validates all required environment variables at startup.
Raises ValueError if any critical variables are missing in production.
"""

import os
from typing import Optional


class Config:
    """Production configuration with strict validation."""

    # ═══════════════════════════════════════════════════════════════
    # CORE SETTINGS
    # ═══════════════════════════════════════════════════════════════

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # ═══════════════════════════════════════════════════════════════
    # DATABASE (REQUIRED)
    # ═══════════════════════════════════════════════════════════════

    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("❌ DATABASE_URL environment variable is required")

    # ═══════════════════════════════════════════════════════════════
    # JWT (REQUIRED)
    # ═══════════════════════════════════════════════════════════════

    JWT_SECRET_KEY: Optional[str] = os.getenv("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
        raise ValueError("❌ JWT_SECRET_KEY environment variable is required")

    # ═══════════════════════════════════════════════════════════════
    # AI (REQUIRED)
    # ═══════════════════════════════════════════════════════════════

    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("❌ OPENAI_API_KEY environment variable is required")

    # ═══════════════════════════════════════════════════════════════
    # BLOCKCHAIN (REQUIRED IN PRODUCTION)
    # ═══════════════════════════════════════════════════════════════

    PRIVATE_KEY: Optional[str] = os.getenv("PRIVATE_KEY")

    if ENVIRONMENT == "production":
        if not PRIVATE_KEY:
            raise ValueError("❌ PRIVATE_KEY required in production environment")

        # Polygon Mainnet RPC URL (Alchemy)
        ALCHEMY_RPC_URL: Optional[str] = os.getenv("ALCHEMY_RPC_URL")
        if not ALCHEMY_RPC_URL:
            raise ValueError("❌ ALCHEMY_RPC_URL required in production for Polygon Mainnet")

        # Verify it's a mainnet URL
        if "polygon-mainnet" not in ALCHEMY_RPC_URL and "polygon-rpc.com" not in ALCHEMY_RPC_URL:
            raise ValueError("❌ ALCHEMY_RPC_URL must be Polygon Mainnet in production")

    # Contract Addresses
    OSOOL_REGISTRY_ADDRESS: Optional[str] = os.getenv("OSOOL_REGISTRY_ADDRESS")
    ELITE_PLATFORM_ADDRESS: Optional[str] = os.getenv("ELITE_PLATFORM_ADDRESS")

    # ═══════════════════════════════════════════════════════════════
    # PAYMENT VERIFICATION (REQUIRED IN PRODUCTION)
    # ═══════════════════════════════════════════════════════════════

    PAYMOB_API_KEY: Optional[str] = os.getenv("PAYMOB_API_KEY")

    if ENVIRONMENT == "production" and not PAYMOB_API_KEY:
        raise ValueError("❌ PAYMOB_API_KEY required in production for payment verification")

    # ═══════════════════════════════════════════════════════════════
    # SMS (REQUIRED IN PRODUCTION FOR KYC)
    # ═══════════════════════════════════════════════════════════════

    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER")

    if ENVIRONMENT == "production":
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
            raise ValueError("❌ Twilio credentials (SID, TOKEN, PHONE) required in production for KYC OTP")

    # ═══════════════════════════════════════════════════════════════
    # EMAIL (REQUIRED IN PRODUCTION)
    # ═══════════════════════════════════════════════════════════════

    SENDGRID_API_KEY: Optional[str] = os.getenv("SENDGRID_API_KEY")

    if ENVIRONMENT == "production" and not SENDGRID_API_KEY:
        raise ValueError("❌ SENDGRID_API_KEY required in production for email verification")

    # ═══════════════════════════════════════════════════════════════
    # OPTIONAL SERVICES
    # ═══════════════════════════════════════════════════════════════

    # Sentry (Recommended for production)
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")

    # Redis (Recommended for caching and OTP storage)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Google OAuth (Optional)
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")

    # Frontend URL (for email verification links)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # Admin API Key (for admin endpoints)
    ADMIN_API_KEY: Optional[str] = os.getenv("ADMIN_API_KEY")


# Validate configuration on module import
try:
    config = Config()
    print(f"✅ Configuration validated for {config.ENVIRONMENT} environment")
except ValueError as e:
    print(f"\n{'='*60}")
    print(f"CONFIGURATION ERROR")
    print(f"{'='*60}")
    print(f"{e}")
    print(f"{'='*60}\n")
    raise


# Export config instance
__all__ = ["config"]
