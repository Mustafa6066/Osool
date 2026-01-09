"""
OpenAI Cost Monitor - Phase 4: Budget Protection
-------------------------------------------------
Tracks token usage and costs for OpenAI API calls to prevent budget overruns.
Alerts when daily spending exceeds threshold.
"""

import logging
from datetime import date
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class CostMonitor:
    """
    Monitors OpenAI API usage and calculates costs.

    Pricing (as of 2024):
    - GPT-4o: $0.0025/1K input tokens, $0.01/1K output tokens
    - text-embedding-ada-002: $0.0001/1K tokens
    - text-embedding-3-small: $0.00002/1K tokens
    """

    # Pricing per 1K tokens (USD)
    COSTS = {
        'gpt-4o': {
            'input': 0.0025,
            'output': 0.01
        },
        'gpt-4o-mini': {
            'input': 0.00015,
            'output': 0.0006
        },
        'text-embedding-ada-002': {
            'usage': 0.0001
        },
        'text-embedding-3-small': {
            'usage': 0.00002
        },
        'text-embedding-3-large': {
            'usage': 0.00013
        }
    }

    DAILY_BUDGET_THRESHOLD = 100  # USD - alert if exceeded

    def __init__(self):
        """Initialize cost monitor"""
        pass

    def log_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int = 0,
        context: str = ""
    ) -> float:
        """
        Log API usage and calculate cost.

        Args:
            model: OpenAI model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens (for chat models)
            context: Optional context (e.g., "chat", "embedding", "valuation")

        Returns:
            Cost in USD
        """
        cost = self._calculate_cost(model, input_tokens, output_tokens)

        # Store in Redis for daily aggregation
        self._store_usage(model, input_tokens, output_tokens, cost, context)

        # Check if daily threshold exceeded
        daily_total = self._get_daily_total()
        if daily_total > self.DAILY_BUDGET_THRESHOLD:
            logger.critical(
                f"🚨 COST ALERT: Daily OpenAI spending ${daily_total:.2f} "
                f"exceeds threshold ${self.DAILY_BUDGET_THRESHOLD}"
            )

        logger.info(
            f"💰 OpenAI usage - Model: {model}, Tokens: {input_tokens + output_tokens}, "
            f"Cost: ${cost:.4f}, Daily total: ${daily_total:.2f}"
        )

        return cost

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage"""
        pricing = self.COSTS.get(model)

        if not pricing:
            logger.warning(f"⚠️ Unknown model: {model} - cost tracking unavailable")
            return 0.0

        if 'usage' in pricing:
            # Embedding models (single token count)
            return (input_tokens / 1000) * pricing['usage']
        else:
            # Chat models (separate input/output pricing)
            input_cost = (input_tokens / 1000) * pricing['input']
            output_cost = (output_tokens / 1000) * pricing['output']
            return input_cost + output_cost

    def _store_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        context: str
    ):
        """Store usage data in Redis with daily aggregation"""
        try:
            from app.services.cache import cache

            today = date.today().isoformat()
            cache_key = f"cost:{today}"

            # Get or initialize daily stats
            current = cache.get_json(cache_key) or {
                'total_cost': 0.0,
                'total_tokens': 0,
                'by_model': {},
                'by_context': {}
            }

            # Update totals
            current['total_cost'] += cost
            current['total_tokens'] += input_tokens + output_tokens

            # Update by model
            if model not in current['by_model']:
                current['by_model'][model] = {'cost': 0.0, 'tokens': 0}
            current['by_model'][model]['cost'] += cost
            current['by_model'][model]['tokens'] += input_tokens + output_tokens

            # Update by context
            if context:
                if context not in current['by_context']:
                    current['by_context'][context] = {'cost': 0.0, 'tokens': 0}
                current['by_context'][context]['cost'] += cost
                current['by_context'][context]['tokens'] += input_tokens + output_tokens

            # Store with 7-day TTL (keep history for a week)
            cache.set_json(cache_key, current, ttl=86400 * 7)

        except Exception as e:
            logger.error(f"Failed to store cost data: {e}")

    def _get_daily_total(self) -> float:
        """Get total cost for today"""
        try:
            from app.services.cache import cache

            today = date.today().isoformat()
            cache_key = f"cost:{today}"

            data = cache.get_json(cache_key)
            return data.get('total_cost', 0.0) if data else 0.0

        except Exception as e:
            logger.error(f"Failed to retrieve daily total: {e}")
            return 0.0

    def get_daily_stats(self, day: Optional[str] = None) -> Dict:
        """
        Get cost statistics for a specific day.

        Args:
            day: Date in ISO format (YYYY-MM-DD), defaults to today

        Returns:
            Dictionary with cost breakdown
        """
        try:
            from app.services.cache import cache

            if not day:
                day = date.today().isoformat()

            cache_key = f"cost:{day}"
            data = cache.get_json(cache_key) or {}

            return {
                'date': day,
                'total_cost_usd': data.get('total_cost', 0.0),
                'total_tokens': data.get('total_tokens', 0),
                'by_model': data.get('by_model', {}),
                'by_context': data.get('by_context', {}),
                'budget_exceeded': data.get('total_cost', 0.0) > self.DAILY_BUDGET_THRESHOLD
            }

        except Exception as e:
            logger.error(f"Failed to get daily stats: {e}")
            return {}


# Singleton instance
cost_monitor = CostMonitor()
