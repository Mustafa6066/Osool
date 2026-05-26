"""
Orchestrator Client — Fetch cross-session intelligence from the Osool Orchestrator.
Non-blocking, fire-and-forget, gracefully degrades when orchestrator is unavailable.
"""

import os
import logging
import json
import uuid
import time
import hmac
import hashlib
from typing import Optional, Dict, Any

import httpx
from app.services.circuit_breaker import CircuitBreaker
from app.services.http_resilience import request_with_retry

logger = logging.getLogger(__name__)

_ORCHESTRATOR_URL = (os.getenv("ORCHESTRATOR_URL") or "").rstrip("/")
_ORCHESTRATOR_API_KEY = os.getenv("ORCHESTRATOR_API_KEY") or ""
_TIMEOUT = 3.0
_orchestrator_breaker = CircuitBreaker(failure_threshold=4, timeout=30)


def get_orchestrator_health_status() -> Dict[str, Any]:
    """Return lightweight orchestrator dependency health for monitoring endpoints."""
    return {
        "configured": bool(_ORCHESTRATOR_URL),
        "timeout_seconds": _TIMEOUT,
        "circuit_breaker": _orchestrator_breaker.status,
    }


async def fetch_user_context(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch cross-session user context from the orchestrator.
    Returns None if orchestrator is unavailable or not configured.
    """
    if not _ORCHESTRATOR_URL:
        return None

    async def _request_context() -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await request_with_retry(
                client,
                "GET",
                f"{_ORCHESTRATOR_URL}/data/user-context/{user_id}",
                service_name="orchestrator_user_context",
                timeout=_TIMEOUT,
                max_attempts=3,
                headers={"x-api-key": _ORCHESTRATOR_API_KEY},
            )
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 404:
                return None
            logger.warning("Orchestrator user-context returned %d for user %s", resp.status_code, user_id)
            return None

    try:
        return await _orchestrator_breaker.call_async(_request_context)
    except httpx.TimeoutException:
        logger.warning("Orchestrator user-context timed out for user %s", user_id)
    except httpx.ConnectError:
        logger.info("Orchestrator unreachable (connection refused)")
    except Exception as e:
        logger.warning("Orchestrator user-context error: %s", e)

    return None


async def sync_user_memory(
    user_id: int,
    budget_min: Optional[float] = None,
    budget_max: Optional[float] = None,
    preferred_areas: Optional[list] = None,
    preferred_developers: Optional[list] = None,
    preferences_text: Optional[str] = None,
) -> None:
    """
    Forward user memory/preferences to the orchestrator via webhook.
    Fire-and-forget — never raises.
    """
    webhook_secret = os.getenv("ORCHESTRATOR_WEBHOOK_SECRET") or ""
    if not _ORCHESTRATOR_URL or not webhook_secret:
        return

    payload: Dict[str, Any] = {
        "eventType": "user_memory_update",
        "userId": str(user_id),
    }
    if budget_min is not None:
        payload["budgetMin"] = budget_min
    if budget_max is not None:
        payload["budgetMax"] = budget_max
    if preferred_areas:
        payload["preferredAreas"] = preferred_areas
    if preferred_developers:
        payload["preferredDevelopers"] = preferred_developers
    if preferences_text:
        payload["preferencesText"] = preferences_text

    body = json.dumps(payload, separators=(",", ":"))
    timestamp = str(int(time.time()))
    nonce = str(uuid.uuid4())
    signature = hmac.new(
        webhook_secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    async def _push_memory() -> None:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await request_with_retry(
                client,
                "POST",
                f"{_ORCHESTRATOR_URL}/webhooks/user-memory",
                service_name="orchestrator_user_memory_sync",
                timeout=_TIMEOUT,
                max_attempts=3,
                headers={
                    "Content-Type": "application/json",
                    "x-webhook-secret": webhook_secret,
                    "x-webhook-signature": signature,
                    "x-webhook-timestamp": timestamp,
                    "x-webhook-nonce": nonce,
                },
                content=body,
            )
            if resp.status_code >= 400:
                logger.warning("Failed to sync user memory: orchestrator returned %d", resp.status_code)

    try:
        await _orchestrator_breaker.call_async(_push_memory)
    except httpx.TimeoutException:
        logger.warning("Failed to sync user memory: orchestrator timed out")
    except httpx.ConnectError:
        logger.info("Failed to sync user memory: orchestrator unreachable")
    except Exception as e:
        logger.warning("Failed to sync user memory to orchestrator: %s", e)
