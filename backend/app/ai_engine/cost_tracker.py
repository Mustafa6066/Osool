"""
Cost Tracker — Lightweight token-usage & cost accounting.

Extracted from claude_sales_agent.py during architecture consolidation.
Singleton instance tracks cumulative token usage across the process lifetime.
"""

import logging

logger = logging.getLogger(__name__)

# Claude 3.5 Sonnet pricing (USD per 1M tokens)
COST_PER_1M_INPUT_TOKENS = 3.0
COST_PER_1M_OUTPUT_TOKENS = 15.0


class CostTracker:
    """Tracks cumulative LLM token usage and cost."""

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def record(self, input_tokens: int, output_tokens: int):
        """Record token usage from an LLM call."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def get_cost_summary(self) -> dict:
        """Return a cost summary dict (USD)."""
        input_cost = (self.total_input_tokens / 1_000_000) * COST_PER_1M_INPUT_TOKENS
        output_cost = (self.total_output_tokens / 1_000_000) * COST_PER_1M_OUTPUT_TOKENS
        total_cost = input_cost + output_cost

        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "input_cost_usd": round(input_cost, 4),
            "output_cost_usd": round(output_cost, 4),
            "total_cost_usd": round(total_cost, 4),
        }


# Singleton
cost_tracker = CostTracker()
