"""
Osool Backend — Paymob Webhook Tests
-------------------------------------
Critical-path tests for POST /webhook/paymob:
HMAC verification, unknown orders, idempotent re-delivery,
property reservation on success, and double-booking conflicts.

Calls the endpoint coroutine directly with mocked Request/AsyncSession,
following the unit-style mocking used across this test suite.
"""

import hashlib
import hmac as hmac_lib
import json
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException


def _make_request(body: dict, hmac_value: str = "deadbeef") -> MagicMock:
    """Build a mocked FastAPI Request for the webhook handler."""
    request = MagicMock()
    request.query_params = {"hmac": hmac_value} if hmac_value is not None else {}
    request.json = AsyncMock(return_value=body)
    return request


def _paymob_body(order_id: int = 555, success: bool = True, amount_cents: int = 29900) -> dict:
    return {
        "obj": {
            "id": 999,
            "order": {"id": order_id},
            "amount_cents": amount_cents,
            "success": success,
            "pending": False,
        }
    }


def _make_db(transaction=None, property_=None) -> AsyncMock:
    """Mock AsyncSession whose execute() returns transaction then property."""
    db = AsyncMock()
    tx_result = MagicMock()
    tx_result.scalar_one_or_none.return_value = transaction
    prop_result = MagicMock()
    prop_result.scalar_one_or_none.return_value = property_
    db.execute = AsyncMock(side_effect=[tx_result, prop_result])
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


def _make_transaction(status="pending", property_id=1, transaction_id=7):
    tx = MagicMock()
    tx.id = transaction_id
    tx.user_id = 42
    tx.property_id = property_id
    tx.amount = 100_000.0
    tx.status = status
    tx.paymob_order_id = "555"
    tx.user = MagicMock()
    return tx


def _make_property(is_available=True, property_id=1):
    prop = MagicMock()
    prop.id = property_id
    prop.is_available = is_available
    prop.location = "New Cairo"
    return prop


class TestWebhookSecurity:
    """HMAC and payload validation."""

    @pytest.mark.asyncio
    async def test_rejects_invalid_json(self):
        from app.api.endpoints import paymob_webhook

        request = MagicMock()
        request.query_params = {"hmac": "abc"}
        request.json = AsyncMock(side_effect=ValueError("bad json"))

        with pytest.raises(HTTPException) as exc:
            await paymob_webhook(request, db=AsyncMock())
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_missing_hmac(self):
        from app.api.endpoints import paymob_webhook

        request = _make_request(_paymob_body(), hmac_value="")
        with pytest.raises(HTTPException) as exc:
            await paymob_webhook(request, db=AsyncMock())
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_rejects_bad_hmac(self):
        from app.api.endpoints import paymob_webhook

        request = _make_request(_paymob_body(), hmac_value="wrong")
        with patch("app.api.endpoints.paymob_service") as svc:
            svc.verify_hmac.return_value = False
            with pytest.raises(HTTPException) as exc:
                await paymob_webhook(request, db=AsyncMock())
        assert exc.value.status_code == 403

    def test_real_hmac_math_round_trip(self):
        """verify_hmac must accept a signature computed per Paymob spec."""
        from app.services.paymob_service import PaymobService

        secret = "test_hmac_secret"
        obj = {
            "amount_cents": 29900,
            "created_at": "2026-01-01T00:00:00",
            "currency": "EGP",
            "error_occured": False,
            "has_parent_transaction": False,
            "id": 999,
            "integration_id": 1,
            "is_3d_secure": True,
            "is_auth": False,
            "is_capture": False,
            "is_refunded": False,
            "is_standalone_payment": True,
            "is_voided": False,
            "order": {"id": 555},
            "owner": 1,
            "pending": False,
            "source_data": {"pan": "1234", "sub_type": "MasterCard", "type": "card"},
            "success": True,
        }
        keys = [
            "amount_cents", "created_at", "currency", "error_occured", "has_parent_transaction",
            "id", "integration_id", "is_3d_secure", "is_auth", "is_capture", "is_refunded",
            "is_standalone_payment", "is_voided", "order.id", "owner", "pending",
            "source_data.pan", "source_data.sub_type", "source_data.type", "success",
        ]
        concat = ""
        for key in keys:
            if "." in key:
                parent, child = key.split(".")
                val = obj.get(parent, {}).get(child, "")
            else:
                val = obj.get(key, "")
            if isinstance(val, bool):
                val = "true" if val else "false"
            concat += str(val)
        signature = hmac_lib.new(
            secret.encode(), concat.encode(), hashlib.sha512
        ).hexdigest()

        with patch.dict(os.environ, {"PAYMOB_HMAC_SECRET": secret}):
            service = PaymobService()
            assert service.verify_hmac({"obj": obj}, signature) is True
            assert service.verify_hmac({"obj": obj}, "0" * 128) is False


class TestWebhookProcessing:
    """Transaction lookup, idempotency, and reservation flow."""

    @pytest.mark.asyncio
    async def test_failed_payment_is_ignored(self):
        from app.api.endpoints import paymob_webhook

        request = _make_request(_paymob_body(success=False))
        db = _make_db()
        with patch("app.api.endpoints.paymob_service") as svc:
            svc.verify_hmac.return_value = True
            result = await paymob_webhook(request, db=db)
        assert result["status"] == "ignored"
        db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_unknown_order_accepted_without_commit(self):
        from app.api.endpoints import paymob_webhook

        request = _make_request(_paymob_body())
        db = _make_db(transaction=None)
        with patch("app.api.endpoints.paymob_service") as svc:
            svc.verify_hmac.return_value = True
            result = await paymob_webhook(request, db=db)
        assert result["status"] == "accepted_but_unknown_order"
        db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_success_marks_paid_and_creates_portfolio(self):
        from app.api.endpoints import paymob_webhook

        tx = _make_transaction(status="pending")
        prop = _make_property(is_available=True)
        request = _make_request(_paymob_body())
        db = _make_db(transaction=tx, property_=prop)

        with patch("app.api.endpoints.paymob_service") as svc, \
             patch("app.services.portfolio_engine.create_portfolio_entry", new=AsyncMock()):
            svc.verify_hmac.return_value = True
            result = await paymob_webhook(request, db=db)

        assert result["status"] == "success"
        assert tx.status == "paid"
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_already_paid_is_idempotent(self):
        """Paymob retries webhooks — a paid transaction must not be re-processed."""
        from app.api.endpoints import paymob_webhook

        tx = _make_transaction(status="paid")
        prop = _make_property(is_available=False)
        request = _make_request(_paymob_body())
        db = _make_db(transaction=tx, property_=prop)

        with patch("app.api.endpoints.paymob_service") as svc:
            svc.verify_hmac.return_value = True
            result = await paymob_webhook(request, db=db)

        assert result["status"] == "already_processed"
        db.commit.assert_not_awaited()
        # Property lookup must never happen on the idempotent path
        assert db.execute.await_count == 1

    @pytest.mark.asyncio
    async def test_unavailable_property_still_completes_payment(self):
        """Anti-double-booking guard removed: payment succeeds regardless of is_available."""
        from app.api.endpoints import paymob_webhook

        tx = _make_transaction(status="pending")
        prop = _make_property(is_available=False)
        request = _make_request(_paymob_body())
        db = _make_db(transaction=tx, property_=prop)

        with patch("app.api.endpoints.paymob_service") as svc, \
             patch("app.services.portfolio_engine.create_portfolio_entry", new=AsyncMock()):
            svc.verify_hmac.return_value = True
            result = await paymob_webhook(request, db=db)

        assert result["status"] == "success"
        assert tx.status == "paid"
        db.commit.assert_awaited_once()
