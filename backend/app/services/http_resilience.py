"""
HTTP resilience helpers.

Provides consistent retry/backoff behavior for outbound HTTP calls to reduce
transient failures across service integrations.
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Optional, Set

import httpx

logger = logging.getLogger(__name__)

# Statuses that are usually transient and safe to retry.
DEFAULT_RETRYABLE_STATUSES: Set[int] = {408, 425, 429, 500, 502, 503, 504}

# Statuses that are caller/data/auth errors and should fail fast.
DEFAULT_NON_RETRYABLE_STATUSES: Set[int] = {400, 401, 403, 404, 422}


def _retry_backoff_seconds(attempt: int, base: float = 0.5, cap: float = 8.0) -> float:
    # Exponential backoff with small jitter to prevent synchronized retries.
    backoff = min(cap, base * (2 ** (attempt - 1)))
    return backoff + random.uniform(0.0, 0.2)


async def request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    service_name: str,
    max_attempts: int = 3,
    timeout: float = 10.0,
    retryable_statuses: Optional[Set[int]] = None,
    non_retryable_statuses: Optional[Set[int]] = None,
    **kwargs,
) -> httpx.Response:
    """
    Execute an HTTP request with bounded retries and exponential backoff.

    Raises the last exception on transport failure after max attempts.
    Returns the final HTTP response otherwise.
    """
    retryable = retryable_statuses or DEFAULT_RETRYABLE_STATUSES
    non_retryable = non_retryable_statuses or DEFAULT_NON_RETRYABLE_STATUSES

    last_exc: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = await client.request(method, url, timeout=timeout, **kwargs)

            if response.status_code in non_retryable:
                return response

            if response.status_code in retryable and attempt < max_attempts:
                wait_for = _retry_backoff_seconds(attempt)
                logger.warning(
                    "%s request got retryable status %s (%s/%s); retrying in %.2fs",
                    service_name,
                    response.status_code,
                    attempt,
                    max_attempts,
                    wait_for,
                )
                await asyncio.sleep(wait_for)
                continue

            return response

        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError) as exc:
            last_exc = exc
            if attempt >= max_attempts:
                break

            wait_for = _retry_backoff_seconds(attempt)
            logger.warning(
                "%s request transport error (%s) (%s/%s); retrying in %.2fs",
                service_name,
                exc.__class__.__name__,
                attempt,
                max_attempts,
                wait_for,
            )
            await asyncio.sleep(wait_for)

    if last_exc is not None:
        raise last_exc

    raise RuntimeError(f"{service_name} request failed without response")
