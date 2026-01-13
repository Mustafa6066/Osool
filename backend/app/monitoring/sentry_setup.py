"""
Sentry Error Tracking Setup
----------------------------
Real-time error monitoring and performance tracking.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def init_sentry():
    """
    Initialize Sentry SDK with Osool-specific configuration.

    Environment Variables Required:
    - SENTRY_DSN: Sentry project DSN
    - SENTRY_ENVIRONMENT: production, staging, development
    - SENTRY_TRACES_SAMPLE_RATE: 0.0 to 1.0 (performance monitoring)
    """
    sentry_dsn = os.getenv("SENTRY_DSN")

    if not sentry_dsn:
        logger.info("ℹ️  Sentry DSN not configured - error tracking disabled")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.httpx import HttpxIntegration

        environment = os.getenv("SENTRY_ENVIRONMENT", "development")
        traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,

            # Integrations
            integrations=[
                FastApiIntegration(transaction_style="url"),
                SqlalchemyIntegration(),
                RedisIntegration(),
                HttpxIntegration(),
            ],

            # Release tracking
            release=os.getenv("SENTRY_RELEASE", "osool@1.0.0"),

            # Performance monitoring
            enable_tracing=True,

            # Error filtering
            before_send=before_send_filter,

            # Additional options
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send PII by default
            max_breadcrumbs=50,
        )

        logger.info(f"✅ Sentry initialized - Environment: {environment}, Traces: {traces_sample_rate}")
        return True

    except ImportError:
        logger.warning("⚠️  sentry-sdk not installed - run: pip install sentry-sdk[fastapi]")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to initialize Sentry: {e}")
        return False


def before_send_filter(event, hint):
    """
    Filter and enrich events before sending to Sentry.

    Use cases:
    - Filter out noisy errors
    - Add custom context
    - Scrub sensitive data
    """

    # Filter out specific error types
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]

        # Don't report 404s
        if "404" in str(exc_value):
            return None

        # Don't report validation errors (handled by FastAPI)
        if "ValidationError" in str(exc_type):
            return None

        # Don't report rate limit errors (expected behavior)
        if "RateLimitExceeded" in str(exc_type):
            return None

    # Scrub sensitive data from request body
    if "request" in event and "data" in event["request"]:
        data = event["request"]["data"]

        # Remove sensitive fields
        sensitive_fields = [
            "password",
            "token",
            "api_key",
            "secret",
            "credit_card",
            "ssn",
            "private_key"
        ]

        for field in sensitive_fields:
            if field in data:
                data[field] = "[REDACTED]"

    return event


def capture_exception_with_context(
    exception: Exception,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    extra_context: Optional[dict] = None
):
    """
    Capture exception with custom context.

    Args:
        exception: Exception to capture
        user_id: User ID for context
        session_id: Session ID for context
        extra_context: Additional context dict
    """
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            # Add user context
            if user_id:
                scope.set_user({"id": user_id})

            # Add session context
            if session_id:
                scope.set_tag("session_id", session_id)

            # Add extra context
            if extra_context:
                for key, value in extra_context.items():
                    scope.set_context(key, value)

            # Capture exception
            sentry_sdk.capture_exception(exception)

    except ImportError:
        logger.warning("Sentry SDK not available for exception capture")
    except Exception as e:
        logger.error(f"Failed to capture exception in Sentry: {e}")


def capture_message_with_context(
    message: str,
    level: str = "info",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    extra_context: Optional[dict] = None
):
    """
    Capture message with custom context.

    Args:
        message: Message to capture
        level: "debug", "info", "warning", "error", "fatal"
        user_id: User ID for context
        session_id: Session ID for context
        extra_context: Additional context dict
    """
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            # Add user context
            if user_id:
                scope.set_user({"id": user_id})

            # Add session context
            if session_id:
                scope.set_tag("session_id", session_id)

            # Add extra context
            if extra_context:
                for key, value in extra_context.items():
                    scope.set_context(key, value)

            # Capture message
            sentry_sdk.capture_message(message, level=level)

    except ImportError:
        logger.warning("Sentry SDK not available for message capture")
    except Exception as e:
        logger.error(f"Failed to capture message in Sentry: {e}")


def add_breadcrumb(message: str, category: str = "default", level: str = "info", data: Optional[dict] = None):
    """
    Add breadcrumb for debugging context.

    Args:
        message: Breadcrumb message
        category: Category (e.g., "query", "http", "navigation")
        level: "debug", "info", "warning", "error"
        data: Additional data dict
    """
    try:
        import sentry_sdk

        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {}
        )

    except ImportError:
        pass  # Silently fail if Sentry not available
    except Exception as e:
        logger.debug(f"Failed to add breadcrumb: {e}")


def set_user_context(user_id: str, email: Optional[str] = None, username: Optional[str] = None):
    """
    Set user context for error tracking.

    Args:
        user_id: User ID
        email: User email (optional)
        username: Username (optional)
    """
    try:
        import sentry_sdk

        user_data = {"id": user_id}
        if email:
            user_data["email"] = email
        if username:
            user_data["username"] = username

        sentry_sdk.set_user(user_data)

    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"Failed to set user context: {e}")


def set_transaction_name(name: str):
    """
    Set transaction name for performance monitoring.

    Args:
        name: Transaction name (e.g., "chat_endpoint", "property_search")
    """
    try:
        import sentry_sdk

        sentry_sdk.set_transaction_name(name)

    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"Failed to set transaction name: {e}")


# Usage examples for documentation
"""
# Example 1: Initialize in main.py
from app.monitoring.sentry_setup import init_sentry

app = FastAPI()

@app.on_event("startup")
async def startup():
    init_sentry()

# Example 2: Capture exception with context
from app.monitoring.sentry_setup import capture_exception_with_context

try:
    result = await claude_api_call()
except Exception as e:
    capture_exception_with_context(
        exception=e,
        user_id=user.id,
        session_id=session_id,
        extra_context={
            "prompt_length": len(prompt),
            "model": "claude-3-5-sonnet"
        }
    )
    raise

# Example 3: Add breadcrumbs for debugging
from app.monitoring.sentry_setup import add_breadcrumb

add_breadcrumb(
    message="User searched for properties",
    category="search",
    level="info",
    data={"query": "New Cairo 3 bedrooms", "results": 12}
)

# Example 4: Set user context at login
from app.monitoring.sentry_setup import set_user_context

@app.post("/login")
async def login(user: User):
    set_user_context(
        user_id=str(user.id),
        email=user.email,
        username=user.full_name
    )
"""
