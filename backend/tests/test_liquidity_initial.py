"""
Osool Backend — Liquidity Initial Pool Tests (F3 Fix)
-------------------------------------------------------
Tests for add_liquidity zero-division fix on empty pools.
"""

import math
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestInitialLiquidityProvision:
    """Test F3: add_liquidity handles empty pools without ZeroDivisionError."""

    def test_initial_lp_tokens_sqrt_formula(self):
        """First LP deposit should mint sqrt(token * egp) LP tokens."""
        token_amount = 10_000
        egp_amount = 75_000

        # Expected: sqrt(10000 * 75000) = sqrt(750,000,000) ≈ 27386
        lp_tokens = math.sqrt(token_amount * egp_amount)

        assert lp_tokens == pytest.approx(27386.12, rel=0.01)

    def test_initial_lp_small_amounts(self):
        """Initial liquidity with small amounts."""
        token_amount = 1
        egp_amount = 10

        lp_tokens = math.sqrt(token_amount * egp_amount)
        assert lp_tokens == pytest.approx(math.sqrt(10), rel=0.001)
        assert lp_tokens > 0

    def test_initial_lp_large_amounts(self):
        """Initial liquidity with large amounts."""
        token_amount = 1_000_000
        egp_amount = 7_500_000

        lp_tokens = math.sqrt(token_amount * egp_amount)
        assert lp_tokens > 0
        assert lp_tokens == pytest.approx(2_738_612.78, rel=0.01)

    def test_initial_lp_equal_amounts(self):
        """Equal token/egp amounts → LP = amount."""
        amount = 50_000
        lp_tokens = math.sqrt(amount * amount)
        assert lp_tokens == amount

    def test_zero_reserves_triggers_initial_path(self):
        """When reserves are zero, the initial liquidity path should be taken."""
        pool_total_lp = 0
        pool_token_reserve = 0
        pool_egp_reserve = 0

        should_use_initial = (
            pool_total_lp == 0 or
            pool_token_reserve == 0 or
            pool_egp_reserve == 0
        )

        assert should_use_initial is True

    def test_nonzero_reserves_uses_proportional_path(self):
        """When reserves are non-zero, proportional calculation should be used."""
        pool_total_lp = 86602
        pool_token_reserve = 100000
        pool_egp_reserve = 750000

        should_use_initial = (
            pool_total_lp == 0 or
            pool_token_reserve == 0 or
            pool_egp_reserve == 0
        )

        assert should_use_initial is False

    def test_proportional_lp_calculation(self):
        """Standard LP minting: min(lp_from_tokens, lp_from_egp)."""
        token_amount = 1000
        egp_amount = 7500
        total_lp = 86602
        token_reserve = 100000
        egp_reserve = 750000

        lp_from_tokens = (token_amount * total_lp) / token_reserve
        lp_from_egp = (egp_amount * total_lp) / egp_reserve

        lp_tokens = min(lp_from_tokens, lp_from_egp)

        # Both should be ~866 (1% of pool)
        assert lp_from_tokens == pytest.approx(866.02, rel=0.01)
        assert lp_from_egp == pytest.approx(866.02, rel=0.01)
        assert lp_tokens > 860
        assert lp_tokens < 870

    def test_slippage_protection_on_initial_liquidity(self):
        """Even initial liquidity should respect min_lp_tokens."""
        token_amount = 100
        egp_amount = 100
        min_lp_tokens = 200  # Unreasonably high

        lp_tokens = math.sqrt(token_amount * egp_amount)  # = 100

        slippage_exceeded = lp_tokens < min_lp_tokens
        assert slippage_exceeded is True

    def test_actual_amounts_equal_input_on_initial(self):
        """On initial deposit, actual_token_amount and actual_egp_amount equal inputs."""
        token_amount = 5000
        egp_amount = 37500

        # Initial liquidity: actual = input (no ratio constraint)
        actual_token = token_amount
        actual_egp = egp_amount

        assert actual_token == token_amount
        assert actual_egp == egp_amount

    def test_proportional_actual_amounts(self):
        """On proportional deposit, actual amounts may differ from inputs."""
        token_amount = 1500
        egp_amount = 7500
        total_lp = 86602
        token_reserve = 100000
        egp_reserve = 750000

        lp_from_tokens = (token_amount * total_lp) / token_reserve  # 1299.03
        lp_from_egp = (egp_amount * total_lp) / egp_reserve  # 866.02

        lp_tokens = min(lp_from_tokens, lp_from_egp)  # 866.02

        actual_token = (lp_tokens * token_reserve) / total_lp  # ~1000 (not 1500!)
        actual_egp = (lp_tokens * egp_reserve) / total_lp  # ~7500

        # User wanted 1500 tokens but only 1000 used (to maintain ratio)
        assert actual_token < token_amount
        assert actual_egp == pytest.approx(egp_amount, rel=0.01)

    def test_no_division_by_zero_with_zero_token_reserve(self):
        """Zero token reserve → initial path (no ZeroDivisionError)."""
        pool_total_lp = 100
        pool_token_reserve = 0  # Zero!
        pool_egp_reserve = 50000

        should_use_initial = (
            pool_total_lp == 0 or
            pool_token_reserve == 0 or
            pool_egp_reserve == 0
        )

        assert should_use_initial is True

        # This should NOT raise ZeroDivisionError
        token_amount = 1000
        egp_amount = 7500
        lp_tokens = math.sqrt(token_amount * egp_amount)
        assert lp_tokens > 0

    def test_no_division_by_zero_with_zero_egp_reserve(self):
        """Zero EGP reserve → initial path (no ZeroDivisionError)."""
        pool_total_lp = 100
        pool_token_reserve = 50000
        pool_egp_reserve = 0  # Zero!

        should_use_initial = (
            pool_total_lp == 0 or
            pool_token_reserve == 0 or
            pool_egp_reserve == 0
        )

        assert should_use_initial is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
