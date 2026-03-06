"""
Osool Backend — Payment Service Tests
---------------------------------------
Tests for PaymentService (F4: verify_egp_deposit, F5: verify_webhook_signature).
Covers: input validation, gateway integration, dev fallback, bank transfers, HMAC verification.
"""

import os
import hmac
import hashlib
import pytest
from unittest.mock import patch, MagicMock


class TestVerifyEgpDeposit:
    """Test F4: verify_egp_deposit no longer always returns VERIFIED."""

    @pytest.fixture
    def service_dev(self):
        """Payment service in dev mode (no API key)."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development", "PAYMOB_API_KEY": "", "PAYMOB_WEBHOOK_SECRET": ""}):
            from app.services.payment_service import PaymentService
            return PaymentService()

    @pytest.fixture
    def service_prod(self):
        """Payment service in production mode (no API key — should fail)."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "PAYMOB_API_KEY": "", "PAYMOB_WEBHOOK_SECRET": ""}):
            from app.services.payment_service import PaymentService
            return PaymentService()

    @pytest.fixture
    def service_with_key(self):
        """Payment service with API key configured."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "PAYMOB_API_KEY": "test_api_key_123", "PAYMOB_WEBHOOK_SECRET": ""}):
            from app.services.payment_service import PaymentService
            svc = PaymentService()
            svc.api_key = "test_api_key_123"
            return svc

    # --- Input Validation Tests ---

    def test_rejects_empty_reference(self, service_dev):
        """Empty reference should fail."""
        from app.services.payment_service import PaymentStatus
        result = service_dev.verify_egp_deposit("", 50000)
        assert result["status"] == PaymentStatus.FAILED
        assert "Invalid reference" in result["message"]

    def test_rejects_short_reference(self, service_dev):
        """Reference shorter than 10 chars should fail."""
        from app.services.payment_service import PaymentStatus
        result = service_dev.verify_egp_deposit("EGP-123", 50000)
        assert result["status"] == PaymentStatus.FAILED

    def test_rejects_non_egp_prefix(self, service_dev):
        """Reference without EGP prefix should fail."""
        from app.services.payment_service import PaymentStatus
        result = service_dev.verify_egp_deposit("USD-1234567890", 50000)
        assert result["status"] == PaymentStatus.FAILED
        assert "EGP-prefixed" in result["message"]

    def test_rejects_amount_below_minimum(self, service_dev):
        """Amount below 10,000 EGP should fail."""
        from app.services.payment_service import PaymentStatus
        result = service_dev.verify_egp_deposit("EGP-1234567890", 5000)
        assert result["status"] == PaymentStatus.FAILED
        assert "Minimum deposit" in result["message"]

    def test_rejects_none_reference(self, service_dev):
        """None reference should fail."""
        from app.services.payment_service import PaymentStatus
        result = service_dev.verify_egp_deposit(None, 50000)
        assert result["status"] == PaymentStatus.FAILED

    # --- Dev Mode (Mock) ---

    def test_dev_mode_verifies_valid_input(self, service_dev):
        """Dev mode: valid input should return VERIFIED (mock)."""
        from app.services.payment_service import PaymentStatus
        result = service_dev.verify_egp_deposit("EGP-1234567890", 50000)
        assert result["status"] == PaymentStatus.VERIFIED
        assert "DEV" in result["message"]
        assert result["tx_id"] is not None
        assert result["verified_amount"] == 50000

    def test_dev_mode_generates_deterministic_tx_id(self, service_dev):
        """Dev mode: same reference should always produce same tx_id."""
        r1 = service_dev.verify_egp_deposit("EGP-1234567890", 50000)
        r2 = service_dev.verify_egp_deposit("EGP-1234567890", 50000)
        assert r1["tx_id"] == r2["tx_id"]

    def test_dev_mode_different_refs_different_tx_ids(self, service_dev):
        """Dev mode: different references should produce different tx_ids."""
        r1 = service_dev.verify_egp_deposit("EGP-1234567890", 50000)
        r2 = service_dev.verify_egp_deposit("EGP-0987654321", 50000)
        assert r1["tx_id"] != r2["tx_id"]

    # --- Production Mode (No Key) ---

    def test_production_fails_without_api_key(self, service_prod):
        """F4: Production mode without API key should FAIL (not mock-verify)."""
        from app.services.payment_service import PaymentStatus
        result = service_prod.verify_egp_deposit("EGP-1234567890", 50000)
        assert result["status"] == PaymentStatus.FAILED
        assert "not configured" in result["message"]

    # --- Production Mode (With Key) ---

    def test_gateway_verification_success(self, service_with_key):
        """With API key + successful gateway verification → VERIFIED."""
        from app.services.payment_service import PaymentStatus

        mock_paymob = MagicMock()
        mock_paymob.verify_transaction.return_value = True

        with patch.dict('sys.modules', {'app.services.paymob_service': MagicMock(paymob_service=mock_paymob)}):
            import sys
            result = service_with_key.verify_egp_deposit("EGP-1234567890", 50000)
            assert result["status"] == PaymentStatus.VERIFIED
            assert result["tx_id"] == "TX-EGP-1234567890"
            assert result["verified_amount"] == 50000

    def test_gateway_verification_failure(self, service_with_key):
        """With API key + failed gateway verification → FAILED."""
        from app.services.payment_service import PaymentStatus

        mock_paymob = MagicMock()
        mock_paymob.verify_transaction.return_value = False

        with patch.dict('sys.modules', {'app.services.paymob_service': MagicMock(paymob_service=mock_paymob)}):
            result = service_with_key.verify_egp_deposit("EGP-1234567890", 50000)
            assert result["status"] == PaymentStatus.FAILED
            assert result["tx_id"] is None

    def test_gateway_exception_returns_failed(self, service_with_key):
        """If gateway throws an exception → FAILED (not crash)."""
        from app.services.payment_service import PaymentStatus

        mock_paymob = MagicMock()
        mock_paymob.verify_transaction.side_effect = Exception("Gateway timeout")

        with patch.dict('sys.modules', {'app.services.paymob_service': MagicMock(paymob_service=mock_paymob)}):
            result = service_with_key.verify_egp_deposit("EGP-1234567890", 50000)
            assert result["status"] == PaymentStatus.FAILED
            assert "unavailable" in result["message"]

    # --- Boundary Values ---

    def test_minimum_valid_amount(self, service_dev):
        """Exactly 10,000 EGP should pass."""
        from app.services.payment_service import PaymentStatus
        result = service_dev.verify_egp_deposit("EGP-1234567890", 10000)
        assert result["status"] == PaymentStatus.VERIFIED

    def test_just_below_minimum_amount(self, service_dev):
        """9,999 EGP should fail."""
        from app.services.payment_service import PaymentStatus
        result = service_dev.verify_egp_deposit("EGP-1234567890", 9999)
        assert result["status"] == PaymentStatus.FAILED

    def test_exactly_10_char_reference(self, service_dev):
        """Reference with exactly 10 chars should pass."""
        from app.services.payment_service import PaymentStatus
        result = service_dev.verify_egp_deposit("EGP-123456", 50000)
        assert result["status"] == PaymentStatus.VERIFIED


class TestVerifyBankTransfer:
    """Test verify_bank_transfer."""

    @pytest.fixture
    def service(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "development", "PAYMOB_API_KEY": "", "PAYMOB_WEBHOOK_SECRET": ""}):
            from app.services.payment_service import PaymentService
            return PaymentService()

    def test_valid_bank_reference(self, service):
        """Valid BANK-prefixed reference ≥15 chars → PENDING."""
        from app.services.payment_service import PaymentStatus
        result = service.verify_bank_transfer("BANK-123456-78901")
        assert result["status"] == PaymentStatus.PENDING
        assert result["tx_id"] is not None
        assert "admin" in result["message"].lower()

    def test_short_reference_returns_pending(self, service):
        """Short reference → PENDING (manual review)."""
        from app.services.payment_service import PaymentStatus
        result = service.verify_bank_transfer("BANK-123")
        assert result["status"] == PaymentStatus.PENDING
        assert result["tx_id"] is None

    def test_non_bank_prefix(self, service):
        """Non-BANK prefix → PENDING (not recognized)."""
        from app.services.payment_service import PaymentStatus
        result = service.verify_bank_transfer("WIRE-123456-78901")
        assert result["status"] == PaymentStatus.PENDING
        assert "not recognized" in result["message"]

    def test_empty_reference(self, service):
        """Empty reference → PENDING."""
        from app.services.payment_service import PaymentStatus
        result = service.verify_bank_transfer("")
        assert result["status"] == PaymentStatus.PENDING

    def test_none_reference(self, service):
        """None reference → PENDING."""
        from app.services.payment_service import PaymentStatus
        result = service.verify_bank_transfer(None)
        assert result["status"] == PaymentStatus.PENDING


class TestVerifyWebhookSignature:
    """Test F5: verify_webhook_signature no longer always returns True."""

    @pytest.fixture
    def service_with_secret(self):
        """Service with webhook secret configured."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "PAYMOB_API_KEY": "", "PAYMOB_WEBHOOK_SECRET": "my_super_secret"}):
            from app.services.payment_service import PaymentService
            svc = PaymentService()
            svc.webhook_secret = "my_super_secret"  # Force-set for tests
            return svc

    @pytest.fixture
    def service_no_secret_dev(self):
        """Dev service without webhook secret."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development", "PAYMOB_API_KEY": "", "PAYMOB_WEBHOOK_SECRET": ""}):
            from app.services.payment_service import PaymentService
            return PaymentService()

    @pytest.fixture
    def service_no_secret_prod(self):
        """Prod service without webhook secret."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "PAYMOB_API_KEY": "", "PAYMOB_WEBHOOK_SECRET": ""}):
            from app.services.payment_service import PaymentService
            return PaymentService()

    # --- With Secret Configured ---

    def test_valid_signature_accepted(self, service_with_secret):
        """Valid HMAC signature should return True."""
        payload = b'{"obj": {"id": 123}}'
        expected_sig = hmac.new(b"my_super_secret", payload, hashlib.sha256).hexdigest()

        assert service_with_secret.verify_webhook_signature(payload, expected_sig) is True

    def test_invalid_signature_rejected(self, service_with_secret):
        """Invalid HMAC signature should return False."""
        payload = b'{"obj": {"id": 123}}'
        wrong_sig = "deadbeef" * 8  # 64 hex chars

        assert service_with_secret.verify_webhook_signature(payload, wrong_sig) is False

    def test_empty_signature_rejected(self, service_with_secret):
        """Empty signature should return False."""
        payload = b'{"obj": {"id": 123}}'
        assert service_with_secret.verify_webhook_signature(payload, "") is False

    def test_none_signature_rejected(self, service_with_secret):
        """None signature should return False."""
        payload = b'{"obj": {"id": 123}}'
        assert service_with_secret.verify_webhook_signature(payload, None) is False

    def test_tampered_payload_rejected(self, service_with_secret):
        """If payload is tampered after signing, verification should fail."""
        original_payload = b'{"obj": {"amount": 10000}}'
        sig = hmac.new(b"my_super_secret", original_payload, hashlib.sha256).hexdigest()

        tampered_payload = b'{"obj": {"amount": 99999}}'
        assert service_with_secret.verify_webhook_signature(tampered_payload, sig) is False

    # --- Without Secret ---

    def test_no_secret_dev_mode_allows(self, service_no_secret_dev):
        """F5: Dev mode without secret → allow (for testing)."""
        assert service_no_secret_dev.verify_webhook_signature(b"anything", "any_sig") is True

    def test_no_secret_prod_mode_rejects(self, service_no_secret_prod):
        """F5: Production without secret → REJECT (security)."""
        assert service_no_secret_prod.verify_webhook_signature(b"anything", "any_sig") is False

    # --- Edge Cases ---

    def test_empty_payload_with_valid_sig(self, service_with_secret):
        """Empty payload with correctly computed signature should pass."""
        payload = b""
        sig = hmac.new(b"my_super_secret", payload, hashlib.sha256).hexdigest()
        assert service_with_secret.verify_webhook_signature(payload, sig) is True

    def test_large_payload(self, service_with_secret):
        """Large payload should still verify correctly."""
        payload = b"x" * 100_000
        sig = hmac.new(b"my_super_secret", payload, hashlib.sha256).hexdigest()
        assert service_with_secret.verify_webhook_signature(payload, sig) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
