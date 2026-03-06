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

    # Claude AI (Phase 1: Advanced Reasoning)
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    if not ANTHROPIC_API_KEY:
        raise ValueError("❌ ANTHROPIC_API_KEY environment variable is required for AMR")

    # Claude Model Configuration
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
    CLAUDE_MAX_TOKENS: int = int(os.getenv("CLAUDE_MAX_TOKENS", "8192"))
    CLAUDE_TEMPERATURE: float = float(os.getenv("CLAUDE_TEMPERATURE", "0.3"))

    # Claude Extended Thinking (State-of-the-Art reasoning)
    CLAUDE_EXTENDED_THINKING: bool = os.getenv("CLAUDE_EXTENDED_THINKING", "true").lower() == "true"
    CLAUDE_THINKING_BUDGET: int = int(os.getenv("CLAUDE_THINKING_BUDGET", "5000"))

    # GPT Model Configuration
    GPT_MODEL: str = os.getenv("GPT_MODEL", "gpt-4o")
    GPT_MINI_MODEL: str = os.getenv("GPT_MINI_MODEL", "gpt-4o-mini")

    # Feature Flags
    ENABLE_PROMPT_CACHING: bool = os.getenv("ENABLE_PROMPT_CACHING", "true").lower() == "true"
    ENABLE_REAL_STREAMING: bool = os.getenv("ENABLE_REAL_STREAMING", "true").lower() == "true"
    ENABLE_VISION_CONTRACTS: bool = os.getenv("ENABLE_VISION_CONTRACTS", "true").lower() == "true"

    # ═══════════════════════════════════════════════════════════════
    # PAYMENT VERIFICATION (OPTIONAL - Phase 2+)
    # ═══════════════════════════════════════════════════════════════

    PAYMOB_API_KEY: Optional[str] = os.getenv("PAYMOB_API_KEY")

    # Feature flag: Enable payment processing (Phase 2+)
    PAYMENTS_ENABLED: bool = os.getenv("ENABLE_PAYMENTS", "false").lower() == "true"

    if ENVIRONMENT == "production" and PAYMENTS_ENABLED:
        if not PAYMOB_API_KEY:
            raise ValueError("❌ PAYMOB_API_KEY required when payments are enabled")

    # ═══════════════════════════════════════════════════════════════
    # SMS (OPTIONAL - Phase 2+)
    # ═══════════════════════════════════════════════════════════════

    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER")

    # Feature flag: Enable SMS/KYC features (Phase 2+)
    SMS_ENABLED: bool = os.getenv("ENABLE_SMS", "false").lower() == "true"

    if ENVIRONMENT == "production" and SMS_ENABLED:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
            raise ValueError("❌ Twilio credentials (SID, TOKEN, PHONE) required when SMS is enabled")

    # ═══════════════════════════════════════════════════════════════
    # EMAIL (OPTIONAL - Phase 2+)
    # ═══════════════════════════════════════════════════════════════

    SENDGRID_API_KEY: Optional[str] = os.getenv("SENDGRID_API_KEY")

    # Feature flag: Enable email features (Phase 2+)
    EMAIL_ENABLED: bool = os.getenv("ENABLE_EMAIL", "false").lower() == "true"

    if ENVIRONMENT == "production" and EMAIL_ENABLED:
        if not SENDGRID_API_KEY:
            raise ValueError("❌ SENDGRID_API_KEY required when email is enabled")

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
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://osool-ten.vercel.app")

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
