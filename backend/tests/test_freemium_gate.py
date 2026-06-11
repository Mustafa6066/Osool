"""
Osool Backend — Freemium Gate Tests
------------------------------------
Critical-path tests for the freemium tier gate in freemium_router:
3/24h rate-limit enforcement, in-memory fallback when Redis is down,
and the premium masking contract ([GATED_PREMIUM_ACCESS] sentinel).
"""

import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.api.freemium_router import (
    _FREE_TIER_REQUEST_LIMIT,
    _GATED_SENTINEL,
    _build_arbitrage_alternative,
    _enforce_rate_limit,
    _mem_rate_limit_check,
    _mem_rl,
)


def _sample_row() -> dict:
    return {
        "listing_id": "L-001",
        "compound_id": "1077-solana-east",
        "geographic_zone": "new_cairo",
        "total_price_egp": 5_000_000.0,
        "size_sqm": 150.0,
        "floor_level": 3,
        "view_orientation": "garden",
        "delivery_year": 2027,
        "is_secondary_market": True,
        "cash_npv_egp": 4_200_000.0,
        "normalized_cash_price_sqm": 28_000.0,
        "savings_vs_offer_pct": 0.12,
        "discount_vs_compound_mean_pct": 0.08,
    }


class TestMaskingContract:
    """Free tier must see the sentinel; premium sees actionable identifiers."""

    def test_free_tier_masks_identification_fields(self):
        alt = _build_arbitrage_alternative(_sample_row(), is_premium=False)
        assert alt.broker_direct_contact == _GATED_SENTINEL
        assert alt.building_number == _GATED_SENTINEL
        assert alt.exact_unit_id == _GATED_SENTINEL

    def test_free_tier_preserves_valuation_numbers(self):
        """Numeric value fields stay visible to demonstrate upgrade value."""
        alt = _build_arbitrage_alternative(_sample_row(), is_premium=False)
        assert alt.cash_npv_egp == 4_200_000.0
        assert alt.savings_vs_offer_pct == 0.12
        assert alt.total_price_egp == 5_000_000.0

    def test_premium_gets_unmasked_fields(self):
        alt = _build_arbitrage_alternative(_sample_row(), is_premium=True)
        assert _GATED_SENTINEL not in (
            alt.broker_direct_contact, alt.building_number, alt.exact_unit_id
        )
        assert "L-001" in alt.broker_direct_contact
        assert alt.exact_unit_id == "L-001"


class TestMemoryRateLimitFallback:
    """In-process fallback counter used when Redis is unavailable."""

    def setup_method(self):
        _mem_rl.clear()

    def test_limit_enforced_within_window(self):
        ip = "203.0.113.7"
        for i in range(_FREE_TIER_REQUEST_LIMIT):
            exceeded, count, _ = _mem_rate_limit_check(ip, _FREE_TIER_REQUEST_LIMIT, 86400)
            assert exceeded is False
            assert count == i + 1
        exceeded, count, ttl = _mem_rate_limit_check(ip, _FREE_TIER_REQUEST_LIMIT, 86400)
        assert exceeded is True
        assert count == _FREE_TIER_REQUEST_LIMIT + 1
        assert ttl >= 1

    def test_window_reset_clears_count(self):
        ip = "203.0.113.8"
        _mem_rate_limit_check(ip, _FREE_TIER_REQUEST_LIMIT, 86400)
        # Simulate window expiry by backdating the window start
        _mem_rl[ip]["window_start"] -= 86401
        exceeded, count, _ = _mem_rate_limit_check(ip, _FREE_TIER_REQUEST_LIMIT, 86400)
        assert exceeded is False
        assert count == 1

    def test_ips_are_isolated(self):
        for _ in range(_FREE_TIER_REQUEST_LIMIT + 1):
            _mem_rate_limit_check("203.0.113.9", _FREE_TIER_REQUEST_LIMIT, 86400)
        exceeded, count, _ = _mem_rate_limit_check("203.0.113.10", _FREE_TIER_REQUEST_LIMIT, 86400)
        assert exceeded is False
        assert count == 1


class TestEnforceRateLimit:
    """_enforce_rate_limit end-to-end with Redis unavailable (memory path)."""

    def setup_method(self):
        _mem_rl.clear()

    @pytest.mark.asyncio
    async def test_redis_down_still_enforces_limit(self):
        """Redis being unreachable must NOT disable the free-tier limit."""
        mock_cache = MagicMock()
        mock_cache.redis = None  # cache service in memory-fallback mode

        with patch("app.services.cache.cache", mock_cache):
            ip = "198.51.100.5"
            for _ in range(_FREE_TIER_REQUEST_LIMIT):
                remaining = await _enforce_rate_limit(ip)
                assert remaining >= 0

            with pytest.raises(HTTPException) as exc:
                await _enforce_rate_limit(ip)
            assert exc.value.status_code == 429
            assert "Retry-After" in exc.value.headers

    @pytest.mark.asyncio
    async def test_redis_pipeline_failure_falls_back_to_memory(self):
        """A Redis error mid-request degrades to the memory counter, not open access."""
        mock_redis = MagicMock()
        mock_redis.pipeline.side_effect = ConnectionError("redis down")
        mock_cache = MagicMock()
        mock_cache.redis = mock_redis

        with patch("app.services.cache.cache", mock_cache):
            ip = "198.51.100.6"
            for _ in range(_FREE_TIER_REQUEST_LIMIT):
                await _enforce_rate_limit(ip)
            with pytest.raises(HTTPException) as exc:
                await _enforce_rate_limit(ip)
            assert exc.value.status_code == 429
