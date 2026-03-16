"""
Orchestrator Client — Fetch cross-session intelligence from the Osool Orchestrator.
Non-blocking, fire-and-forget, gracefully degrades when orchestrator is unavailable.
"""

import os
import logging
from typing import Optional, Dict, Any

import httpx

logger = logging.getLogger(__name__)

_ORCHESTRATOR_URL = (os.getenv("ORCHESTRATOR_URL") or "").rstrip("/")
_ORCHESTRATOR_API_KEY = os.getenv("ORCHESTRATOR_API_KEY") or ""
_TIMEOUT = 3.0  # seconds — must be fast, runs in the hot path


async def fetch_user_context(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch cross-session user context from the orchestrator.
    Returns None silently if orchestrator is unavailable or not configured.
    """
    if not _ORCHESTRATOR_URL:
        return None

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_ORCHESTRATOR_URL}/data/user-context/{user_id}",
                headers={"x-api-key": _ORCHESTRATOR_API_KEY},
            )
            if resp.status_code == 200:
                return resp.json()
            logger.debug(f"Orchestrator user-context returned {resp.status_code}")
    except Exception as e:
        logger.debug(f"Orchestrator unreachable: {e}")

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

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            await client.post(
                f"{_ORCHESTRATOR_URL}/webhooks/user-memory",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-webhook-secret": webhook_secret,
                },
            )
    except Exception as e:
        logger.debug(f"Failed to sync user memory to orchestrator: {e}")
