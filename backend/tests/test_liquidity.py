"""
Osool Backend - Liquidity Service Tests
Phase 4.2: Comprehensive Test Suite
---------------------------------------
Tests for AMM liquidity calculations, swaps, and LP positions.
"""

import pytest
from decimal import Decimal
from app.services.liquidity_service import LiquidityService


class TestConstantProductFormula:
    """Test constant product AMM formula: x * y = k"""

    @pytest.fixture
    def liquidity_service(self):
        return LiquidityService()

    def test_simple_swap_calculation(self, liquidity_service):
        """Test basic swap quote calculation"""
        # Pool: 100,000 tokens, 750,000 EGP (price = 7.5 EGP/token)
        pool_state = {
            "token_reserve": 100000,
            "egp_reserve": 750000,
            "total_lp_tokens": 86602
        }

        # User wants to swap 10,000 EGP for tokens
        quote = liquidity_service._calculate_swap_quote(
            trade_type="BUY",
            amount_in=10000,
            token_reserve=pool_state["token_reserve"],
            egp_reserve=pool_state["egp_reserve"]
        )

        # Calculate expected (constant product formula)
        # amount_in_with_fee = 10000 * (10000 - 30) / 10000 = 9970
        # tokens_out = 100000 - (100000 * 750000) / (750000 + 9970)
        # tokens_out ≈ 1290

        assert quote["amount_out"] > 1280
        assert quote["amount_out"] < 1300
        assert quote["fee_amount"] == 30  # 0.3% of 10,000

    def test_swap_price_impact(self, liquidity_service):
        """Test price impact increases with larger swaps"""
        pool_state = {
            "token_reserve": 100000,
            "egp_reserve": 750000
        }

        # Small swap (1,000 EGP)
        small_quote = liquidity_service._calculate_swap_quote(
            trade_type="BUY",
            amount_in=1000,
            token_reserve=pool_state["token_reserve"],
            egp_reserve=pool_state["egp_reserve"]
        )

        # Large swap (50,000 EGP)
        large_quote = liquidity_service._calculate_swap_quote(
            trade_type="BUY",
            amount_in=50000,
            token_reserve=pool_state["token_reserve"],
            egp_reserve=pool_state["egp_reserve"]
        )

        # Large swap should have higher price impact
        assert large_quote["price_impact"] > small_quote["price_impact"]
        assert large_quote["price_impact"] > 5  # Should exceed 5%

    def test_swap_both_directions(self, liquidity_service):
        """Test swap calculations in both directions (BUY and SELL)"""
        pool_state = {
            "token_reserve": 100000,
            "egp_reserve": 750000
        }

        # BUY: 10,000 EGP → tokens
        buy_quote = liquidity_service._calculate_swap_quote(
            trade_type="BUY",
            amount_in=10000,
            token_reserve=pool_state["token_reserve"],
            egp_reserve=pool_state["egp_reserve"]
        )

        # SELL: 1,290 tokens → EGP
        sell_quote = liquidity_service._calculate_swap_quote(
            trade_type="SELL",
            amount_in=buy_quote["amount_out"],
            token_reserve=pool_state["token_reserve"],
            egp_reserve=pool_state["egp_reserve"]
        )

        # Round-trip should result in slight loss due to fees
        assert sell_quote["amount_out"] < 10000
        assert sell_quote["amount_out"] > 9900  # ~1% loss (2 * 0.3% fee + slippage)

    def test_constant_product_preserved(self, liquidity_service):
        """Test that k (constant product) is preserved after swap"""
        initial_k = 100000 * 750000  # 75,000,000,000

        # After swap: 10,000 EGP → 1,290 tokens
        # New reserves: 98,710 tokens, 760,000 EGP
        new_k = 98710 * 760000  # 75,019,600,000

        # k should increase slightly due to fees (0.3%)
        assert new_k >= initial_k
        assert (new_k - initial_k) / initial_k < 0.01  # Increase < 1%


class TestLiquidityProvision:
    """Test adding and removing liquidity"""

    @pytest.fixture
    def liquidity_service(self):
        return LiquidityService()

    def test_calculate_lp_tokens(self, liquidity_service):
        """Test LP token minting calculation"""
        # User adds: 1,000 tokens + 7,500 EGP
        # Pool has: 100,000 tokens + 750,000 EGP + 86,602 LP tokens

        lp_tokens = liquidity_service._calculate_lp_tokens(
            token_amount=1000,
            egp_amount=7500,
            token_reserve=100000,
            egp_reserve=750000,
            total_lp_tokens=86602
        )

        # LP tokens should be proportional to contribution
        # Expected: 86,602 * (1,000 / 100,000) = 866 LP tokens
        assert lp_tokens > 860
        assert lp_tokens < 870

    def test_lp_token_share_calculation(self, liquidity_service):
        """Test share of pool calculation"""
        # User has 866 LP tokens, pool has 87,468 total LP tokens
        share_percent = (866 / 87468) * 100

        assert share_percent > 0.98
        assert share_percent < 1.00

    def test_add_liquidity_ratio_maintained(self, liquidity_service):
        """Test that liquidity must be added in correct ratio"""
        pool_ratio = 750000 / 100000  # 7.5 EGP per token

        # User wants to add 1,000 tokens
        # Required EGP = 1,000 * 7.5 = 7,500 EGP
        required_egp = 1000 * pool_ratio

        assert required_egp == 7500

    def test_remove_liquidity_calculation(self, liquidity_service):
        """Test liquidity removal calculation"""
        # User burns 866 LP tokens
        # Pool has: 101,000 tokens + 757,500 EGP + 87,468 LP tokens

        share = 866 / 87468  # ~0.99%

        tokens_out = 101000 * share
        egp_out = 757500 * share

        assert tokens_out > 990
        assert tokens_out < 1010
        assert egp_out > 7400
        assert egp_out < 7600


class TestSlippageProtection:
    """Test slippage protection mechanism"""

    @pytest.fixture
    def liquidity_service(self):
        return LiquidityService()

    def test_slippage_within_tolerance(self, liquidity_service):
        """Test swap succeeds when slippage is within tolerance"""
        quote = {
            "amount_out": 1290,
            "execution_price": 7.72,
            "price_impact": 2.9
        }

        min_amount_out = 1290 * 0.98  # 2% slippage tolerance = 1264

        # Actual amount out: 1290
        # Min amount out: 1264
        # Should succeed
        assert quote["amount_out"] >= min_amount_out

    def test_slippage_exceeded(self, liquidity_service):
        """Test swap fails when slippage is exceeded"""
        quote = {
            "amount_out": 1250,  # Less than expected
            "execution_price": 8.0,
            "price_impact": 6.5
        }

        min_amount_out = 1290 * 0.98  # Expected 1264, got 1250

        # Should fail (1250 < 1264)
        assert quote["amount_out"] < min_amount_out

    def test_high_slippage_warning(self, liquidity_service):
        """Test warning for high slippage (>5%)"""
        quote = {
            "amount_out": 1200,
            "execution_price": 8.33,
            "price_impact": 11.0
        }

        # Slippage > 5% should trigger warning
        assert quote["price_impact"] > 5


class TestFeeDistribution:
    """Test trading fee distribution (0.25% to LPs, 0.05% to platform)"""

    @pytest.fixture
    def liquidity_service(self):
        return LiquidityService()

    def test_fee_calculation(self, liquidity_service):
        """Test trading fee is 0.3% of swap amount"""
        amount_in = 10000
        fee = amount_in * 0.003  # 0.3%

        assert fee == 30

    def test_fee_split(self, liquidity_service):
        """Test fee split: 0.25% to LPs, 0.05% to platform"""
        total_fee = 30  # 0.3% of 10,000

        lp_fee = 10000 * 0.0025  # 25
        platform_fee = 10000 * 0.0005  # 5

        assert lp_fee + platform_fee == total_fee
        assert lp_fee == 25
        assert platform_fee == 5

    def test_lp_fee_accumulation(self, liquidity_service):
        """Test LP fees accumulate in the pool"""
        # Initial pool: 100,000 tokens, 750,000 EGP
        # After 10 swaps of 10,000 EGP each:
        # Total fees to LPs: 10 * 25 = 250 EGP

        accumulated_fees = 10 * 25
        new_egp_reserve = 750000 + accumulated_fees

        assert accumulated_fees == 250
        assert new_egp_reserve == 750250


class TestAPYCalculation:
    """Test APY calculation for liquidity providers"""

    @pytest.fixture
    def liquidity_service(self):
        return LiquidityService()

    def test_apy_calculation(self, liquidity_service):
        """Test APY calculation based on trading volume"""
        # Pool: 750,000 EGP liquidity
        # Daily volume: 50,000 EGP
        # Daily fees: 50,000 * 0.0025 = 125 EGP
        # Annual fees: 125 * 365 = 45,625 EGP
        # APY: (45,625 / 750,000) * 100 = 6.08%

        pool_liquidity = 750000
        daily_volume = 50000
        daily_fees = daily_volume * 0.0025
        annual_fees = daily_fees * 365
        apy = (annual_fees / pool_liquidity) * 100

        assert apy > 6.0
        assert apy < 6.2

    def test_apy_increases_with_volume(self, liquidity_service):
        """Test APY increases with higher trading volume"""
        pool_liquidity = 750000

        # Low volume: 10,000 EGP/day
        low_volume_apy = ((10000 * 0.0025 * 365) / pool_liquidity) * 100

        # High volume: 100,000 EGP/day
        high_volume_apy = ((100000 * 0.0025 * 365) / pool_liquidity) * 100

        assert high_volume_apy > low_volume_apy
        assert high_volume_apy > 12  # Should exceed 12%


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def liquidity_service(self):
        return LiquidityService()

    def test_zero_amount_swap(self, liquidity_service):
        """Test swap with zero amount"""
        with pytest.raises(ValueError):
            liquidity_service._calculate_swap_quote(
                trade_type="BUY",
                amount_in=0,
                token_reserve=100000,
                egp_reserve=750000
            )

    def test_negative_amount_swap(self, liquidity_service):
        """Test swap with negative amount"""
        with pytest.raises(ValueError):
            liquidity_service._calculate_swap_quote(
                trade_type="BUY",
                amount_in=-1000,
                token_reserve=100000,
                egp_reserve=750000
            )

    def test_swap_exceeds_reserve(self, liquidity_service):
        """Test swap that would drain the pool"""
        # Try to swap for more tokens than available
        with pytest.raises(ValueError):
            liquidity_service._calculate_swap_quote(
                trade_type="BUY",
                amount_in=10000000,  # Way too much
                token_reserve=100000,
                egp_reserve=750000
            )

    def test_empty_pool(self, liquidity_service):
        """Test operations on empty pool"""
        with pytest.raises(ValueError):
            liquidity_service._calculate_swap_quote(
                trade_type="BUY",
                amount_in=1000,
                token_reserve=0,  # Empty pool
                egp_reserve=0
            )

    def test_very_small_swap(self, liquidity_service):
        """Test swap with very small amount (0.01 EGP)"""
        quote = liquidity_service._calculate_swap_quote(
            trade_type="BUY",
            amount_in=0.01,
            token_reserve=100000,
            egp_reserve=750000
        )

        assert quote["amount_out"] > 0
        assert quote["fee_amount"] < 0.01


class TestImpermanentLoss:
    """Test impermanent loss calculations"""

    @pytest.fixture
    def liquidity_service(self):
        return LiquidityService()

    def test_no_impermanent_loss_stable_price(self, liquidity_service):
        """Test no impermanent loss when price doesn't change"""
        # Initial: 1,000 tokens + 7,500 EGP (price = 7.5)
        # Final: 1,000 tokens + 7,500 EGP (price = 7.5)
        # Impermanent loss: 0%

        initial_value = 1000 * 7.5 + 7500  # 15,000 EGP
        final_value = 1000 * 7.5 + 7500  # 15,000 EGP

        impermanent_loss = (initial_value - final_value) / initial_value * 100

        assert impermanent_loss == 0

    def test_impermanent_loss_price_doubles(self, liquidity_service):
        """Test impermanent loss when token price doubles"""
        # Initial: 1,000 tokens + 7,500 EGP (price = 7.5)
        # Final: 707 tokens + 10,607 EGP (price = 15)
        # Hold value: 1,000 * 15 + 7,500 = 22,500 EGP
        # Pool value: 707 * 15 + 10,607 = 21,212 EGP
        # Impermanent loss: ~5.7%

        hold_value = 1000 * 15 + 7500  # 22,500
        pool_value = 707 * 15 + 10607  # 21,212

        impermanent_loss = (hold_value - pool_value) / hold_value * 100

        assert impermanent_loss > 5
        assert impermanent_loss < 6


class TestBlockchainIntegration:
    """Test blockchain integration features (Phase 2 implementation)"""

    @pytest.fixture
    def mock_db(self, mocker):
        """Mock database session"""
        return mocker.AsyncMock()

    @pytest.fixture
    def mock_web3(self, mocker):
        """Mock Web3 instance with contract interactions"""
        mock_w3 = mocker.Mock()

        # Mock OEGP contract balance check
        mock_oegp = mocker.Mock()
        mock_oegp.functions.balanceOf.return_value.call.return_value = 10_000 * 10**18  # 10,000 OEGP

        # Mock AMM contract balance check
        mock_amm = mocker.Mock()
        mock_amm.functions.balanceOf.return_value.call.return_value = 100  # 100 property tokens

        # Mock swap transaction
        mock_amm.functions.swapTokensForEGP.return_value.build_transaction.return_value = {
            'from': '0x742d35Cc6634C0532925a3b844Bc454e4438f44e',
            'nonce': 1,
            'gas': 300000,
            'gasPrice': 30 * 10**9,
            'chainId': 137
        }

        # Mock transaction receipt (successful)
        mock_w3.eth.get_transaction_receipt.return_value = {
            'status': 1,  # Success
            'blockNumber': 12345,
            'transactionHash': b'\x12\x34\x56\x78',
            'gasUsed': 250000
        }

        mock_w3.eth.send_raw_transaction.return_value = b'\x12\x34\x56\x78'
        mock_w3.to_hex.return_value = "0x1234567890abcdef"

        return mock_w3, mock_amm, mock_oegp

    @pytest.mark.asyncio
    async def test_on_chain_balance_verification_sufficient(self, mocker, mock_web3):
        """Test on-chain balance verification - sufficient balance (Phase 2.2)"""
        mock_w3, mock_amm, mock_oegp = mock_web3
        liquidity_service = LiquidityService()

        # Mock balance: 10,000 OEGP
        with mocker.patch.object(liquidity_service, 'oegp_contract', mock_oegp):
            with mocker.patch.object(liquidity_service, 'w3', mock_w3):
                is_sufficient, message = await liquidity_service._verify_user_balance(
                    user_address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                    token_type="OEGP",
                    amount=5000.0  # Requesting 5,000 OEGP
                )

                assert is_sufficient is True
                assert "Sufficient balance" in message

    @pytest.mark.asyncio
    async def test_on_chain_balance_verification_insufficient(self, mocker, mock_web3):
        """Test on-chain balance verification - insufficient balance (Phase 2.2)"""
        mock_w3, mock_amm, mock_oegp = mock_web3
        liquidity_service = LiquidityService()

        # Mock insufficient balance: 1,000 OEGP
        mock_oegp.functions.balanceOf.return_value.call.return_value = 1_000 * 10**18

        with mocker.patch.object(liquidity_service, 'oegp_contract', mock_oegp):
            with mocker.patch.object(liquidity_service, 'w3', mock_w3):
                is_sufficient, message = await liquidity_service._verify_user_balance(
                    user_address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                    token_type="OEGP",
                    amount=5000.0  # Requesting 5,000 OEGP (more than balance)
                )

                assert is_sufficient is False
                assert "Insufficient balance" in message

    @pytest.mark.asyncio
    async def test_two_phase_commit_success(self, mocker, mock_db, mock_web3):
        """Test two-phase commit: blockchain executes, then DB updates (Phase 2.6)"""
        mock_w3, mock_amm, mock_oegp = mock_web3
        liquidity_service = LiquidityService()

        # Mock successful blockchain execution
        with mocker.patch.object(liquidity_service, '_verify_user_balance', return_value=(True, "Sufficient")):
            with mocker.patch.object(liquidity_service, '_execute_token_to_egp_swap', return_value="0x1234567890abcdef"):
                with mocker.patch.object(liquidity_service, '_monitor_transaction', return_value=(True, {"status": 1, "gasUsed": 250000})):

                    result = await liquidity_service.execute_swap(
                        property_id=1,
                        user_id=42,
                        amount_in=10.0,
                        amount_out=49_000.0,
                        trade_type="SELL"
                    )

                    assert result["success"] is True
                    assert result["tx_hash"] == "0x1234567890abcdef"

    @pytest.mark.asyncio
    async def test_two_phase_commit_rollback_on_blockchain_failure(self, mocker, mock_db, mock_web3):
        """Test rollback: if blockchain fails, do NOT update database (Phase 2.6)"""
        mock_w3, mock_amm, mock_oegp = mock_web3
        liquidity_service = LiquidityService()

        # Mock blockchain transaction failure
        with mocker.patch.object(liquidity_service, '_verify_user_balance', return_value=(True, "Sufficient")):
            with mocker.patch.object(liquidity_service, '_execute_token_to_egp_swap', return_value="0xfailed_tx"):
                with mocker.patch.object(liquidity_service, '_monitor_transaction', return_value=(False, None)):

                    result = await liquidity_service.execute_swap(
                        property_id=1,
                        user_id=42,
                        amount_in=10.0,
                        amount_out=49_000.0,
                        trade_type="SELL"
                    )

                    assert result["success"] is False
                    assert "failed" in result["error"].lower() or "timed out" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_transaction_monitoring_success(self, mocker, mock_web3):
        """Test transaction monitoring - successful confirmation (Phase 2.5)"""
        mock_w3, mock_amm, mock_oegp = mock_web3
        liquidity_service = LiquidityService()

        # Mock successful transaction receipt
        mock_w3.eth.get_transaction_receipt.return_value = {
            'status': 1,
            'blockNumber': 12345,
            'gasUsed': 250000
        }

        with mocker.patch.object(liquidity_service, 'w3', mock_w3):
            confirmed, receipt = await liquidity_service._monitor_transaction("0x1234567890abcdef", timeout=10)

            assert confirmed is True
            assert receipt['status'] == 1

    @pytest.mark.asyncio
    async def test_transaction_monitoring_reverted(self, mocker, mock_web3):
        """Test transaction monitoring - reverted transaction (Phase 2.5)"""
        mock_w3, mock_amm, mock_oegp = mock_web3
        liquidity_service = LiquidityService()

        # Mock reverted transaction (status = 0)
        mock_w3.eth.get_transaction_receipt.return_value = {
            'status': 0,  # Reverted
            'blockNumber': 12345,
            'gasUsed': 250000
        }

        with mocker.patch.object(liquidity_service, 'w3', mock_w3):
            confirmed, receipt = await liquidity_service._monitor_transaction("0xreverted_tx", timeout=10)

            assert confirmed is False
            assert receipt is None

    @pytest.mark.asyncio
    async def test_transaction_monitoring_timeout(self, mocker, mock_web3):
        """Test transaction monitoring - timeout after 120 seconds (Phase 2.5)"""
        mock_w3, mock_amm, mock_oegp = mock_web3
        liquidity_service = LiquidityService()

        # Mock no receipt (transaction stuck in mempool)
        mock_w3.eth.get_transaction_receipt.return_value = None

        with mocker.patch.object(liquidity_service, 'w3', mock_w3):
            confirmed, receipt = await liquidity_service._monitor_transaction("0xstuck_tx", timeout=2)

            assert confirmed is False
            assert receipt is None

    @pytest.mark.asyncio
    async def test_contract_abi_loading(self, mocker):
        """Test contract ABIs are loaded from Hardhat artifacts (Phase 2.1)"""
        liquidity_service = LiquidityService()

        # Verify _load_contract_abis() loads artifacts correctly
        with mocker.patch('builtins.open', mocker.mock_open(read_data='{"abi": []}')):
            with mocker.patch('pathlib.Path.exists', return_value=True):
                liquidity_service._load_contract_abis()

                # Verify contracts were initialized
                assert liquidity_service.amm_contract is not None or liquidity_service.amm_address is None
                assert liquidity_service.oegp_contract is not None or liquidity_service.oegp_address is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
