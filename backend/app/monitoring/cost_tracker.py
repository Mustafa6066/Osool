"""
AI Cost Monitoring and Token Limit Enforcement
-----------------------------------------------
Track API costs for Claude and OpenAI to prevent budget overruns.
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import redis
import json

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# COST CONSTANTS (USD)
# ---------------------------------------------------------------------------

# Claude 3.5 Sonnet Pricing
CLAUDE_INPUT_COST_PER_1M = 3.0  # USD per 1M input tokens
CLAUDE_OUTPUT_COST_PER_1M = 15.0  # USD per 1M output tokens

# OpenAI Pricing
OPENAI_GPT4O_INPUT_COST_PER_1M = 2.5  # USD per 1M input tokens
OPENAI_GPT4O_OUTPUT_COST_PER_1M = 10.0  # USD per 1M output tokens
OPENAI_EMBEDDING_COST_PER_1M = 0.13  # USD per 1M tokens (text-embedding-3-small)

# Cost Limits
SESSION_COST_LIMIT = 0.50  # USD per session
DAILY_COST_LIMIT = 100.0  # USD per day
MONTHLY_COST_LIMIT = 3000.0  # USD per month


class CostTracker:
    """
    Track and enforce API cost limits.

    Uses Redis for distributed tracking across multiple workers.
    Falls back to in-memory tracking if Redis unavailable.
    """

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize cost tracker with optional Redis connection."""
        self.redis_client = None
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("✅ Cost tracker connected to Redis")
            except Exception as e:
                logger.warning(f"⚠️  Redis unavailable for cost tracking: {e}")

        # Fallback in-memory storage
        self._memory_store: Dict[str, Dict] = defaultdict(dict)

    # -----------------------------------------------------------------------
    # TOKEN COST CALCULATION
    # -----------------------------------------------------------------------

    def calculate_claude_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for Claude API call."""
        input_cost = (input_tokens / 1_000_000) * CLAUDE_INPUT_COST_PER_1M
        output_cost = (output_tokens / 1_000_000) * CLAUDE_OUTPUT_COST_PER_1M
        return input_cost + output_cost

    def calculate_openai_cost(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        embedding_tokens: int = 0
    ) -> float:
        """Calculate cost for OpenAI API call."""
        input_cost = (input_tokens / 1_000_000) * OPENAI_GPT4O_INPUT_COST_PER_1M
        output_cost = (output_tokens / 1_000_000) * OPENAI_GPT4O_OUTPUT_COST_PER_1M
        embedding_cost = (embedding_tokens / 1_000_000) * OPENAI_EMBEDDING_COST_PER_1M
        return input_cost + output_cost + embedding_cost

    # -----------------------------------------------------------------------
    # COST TRACKING
    # -----------------------------------------------------------------------

    def track_claude_usage(
        self,
        session_id: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict:
        """
        Track Claude API usage and return cost summary.

        Returns:
            dict with: cost, total_session_cost, limit_reached, remaining
        """
        cost = self.calculate_claude_cost(input_tokens, output_tokens)

        # Update session cost
        session_cost = self._get_session_cost(session_id) + cost
        self._set_session_cost(session_id, session_cost)

        # Update daily cost
        daily_cost = self._get_daily_cost() + cost
        self._increment_daily_cost(cost)

        # Check limits
        limit_reached = session_cost >= SESSION_COST_LIMIT

        return {
            "service": "claude",
            "cost_usd": round(cost, 4),
            "session_cost_usd": round(session_cost, 4),
            "daily_cost_usd": round(daily_cost, 4),
            "session_limit": SESSION_COST_LIMIT,
            "limit_reached": limit_reached,
            "remaining_session_budget": round(max(0, SESSION_COST_LIMIT - session_cost), 4),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }

    def track_openai_usage(
        self,
        session_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        embedding_tokens: int = 0
    ) -> Dict:
        """
        Track OpenAI API usage and return cost summary.

        Returns:
            dict with: cost, total_session_cost, limit_reached, remaining
        """
        cost = self.calculate_openai_cost(input_tokens, output_tokens, embedding_tokens)

        # Update session cost
        session_cost = self._get_session_cost(session_id) + cost
        self._set_session_cost(session_id, session_cost)

        # Update daily cost
        daily_cost = self._get_daily_cost() + cost
        self._increment_daily_cost(cost)

        # Check limits
        limit_reached = session_cost >= SESSION_COST_LIMIT

        return {
            "service": "openai",
            "cost_usd": round(cost, 4),
            "session_cost_usd": round(session_cost, 4),
            "daily_cost_usd": round(daily_cost, 4),
            "session_limit": SESSION_COST_LIMIT,
            "limit_reached": limit_reached,
            "remaining_session_budget": round(max(0, SESSION_COST_LIMIT - session_cost), 4),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "embedding_tokens": embedding_tokens
        }

    # -----------------------------------------------------------------------
    # LIMIT CHECKING
    # -----------------------------------------------------------------------

    def check_session_limit(self, session_id: str) -> tuple[bool, float]:
        """
        Check if session has reached cost limit.

        Returns:
            (limit_reached, current_cost)
        """
        session_cost = self._get_session_cost(session_id)
        return session_cost >= SESSION_COST_LIMIT, session_cost

    def check_daily_limit(self) -> tuple[bool, float]:
        """
        Check if daily cost limit has been reached.

        Returns:
            (limit_reached, current_cost)
        """
        daily_cost = self._get_daily_cost()
        return daily_cost >= DAILY_COST_LIMIT, daily_cost

    # -----------------------------------------------------------------------
    # STORAGE METHODS (Redis or In-Memory)
    # -----------------------------------------------------------------------

    def _get_session_cost(self, session_id: str) -> float:
        """Get total cost for a session."""
        key = f"cost:session:{session_id}"

        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                return float(value) if value else 0.0
            except Exception as e:
                logger.error(f"Redis get error: {e}")
                return self._memory_store.get(key, 0.0)
        else:
            return self._memory_store.get(key, 0.0)

    def _set_session_cost(self, session_id: str, cost: float):
        """Set total cost for a session."""
        key = f"cost:session:{session_id}"

        if self.redis_client:
            try:
                # Expire after 24 hours
                self.redis_client.setex(key, 86400, str(cost))
            except Exception as e:
                logger.error(f"Redis set error: {e}")
                self._memory_store[key] = cost
        else:
            self._memory_store[key] = cost

    def _get_daily_cost(self) -> float:
        """Get total cost for today."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        key = f"cost:daily:{today}"

        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                return float(value) if value else 0.0
            except Exception as e:
                logger.error(f"Redis get error: {e}")
                return self._memory_store.get(key, 0.0)
        else:
            return self._memory_store.get(key, 0.0)

    def _increment_daily_cost(self, cost: float):
        """Increment daily cost counter."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        key = f"cost:daily:{today}"

        if self.redis_client:
            try:
                # Use INCRBYFLOAT for atomic increment
                self.redis_client.incrbyfloat(key, cost)
                # Expire at end of day
                tomorrow = datetime.utcnow().replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) + timedelta(days=1)
                ttl = int((tomorrow - datetime.utcnow()).total_seconds())
                self.redis_client.expire(key, ttl)
            except Exception as e:
                logger.error(f"Redis increment error: {e}")
                self._memory_store[key] = self._memory_store.get(key, 0.0) + cost
        else:
            self._memory_store[key] = self._memory_store.get(key, 0.0) + cost

    # -----------------------------------------------------------------------
    # REPORTING
    # -----------------------------------------------------------------------

    def get_cost_summary(self, session_id: str) -> Dict:
        """Get comprehensive cost summary."""
        session_cost = self._get_session_cost(session_id)
        daily_cost = self._get_daily_cost()

        return {
            "session_id": session_id,
            "session_cost_usd": round(session_cost, 4),
            "session_limit_usd": SESSION_COST_LIMIT,
            "session_usage_percent": round((session_cost / SESSION_COST_LIMIT) * 100, 1),
            "daily_cost_usd": round(daily_cost, 4),
            "daily_limit_usd": DAILY_COST_LIMIT,
            "daily_usage_percent": round((daily_cost / DAILY_COST_LIMIT) * 100, 1),
            "limits": {
                "session_limit_reached": session_cost >= SESSION_COST_LIMIT,
                "daily_limit_reached": daily_cost >= DAILY_COST_LIMIT
            }
        }


# ---------------------------------------------------------------------------
# GLOBAL INSTANCE
# ---------------------------------------------------------------------------

# Initialize cost tracker (will use Redis if REDIS_URL env var is set)
import os
cost_tracker = CostTracker(redis_url=os.getenv("REDIS_URL"))
