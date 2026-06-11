"""
Osool Backend — Billing Tests
------------------------------
Tests the monetization wiring: subscription/report purchase initiation,
webhook tier activation, idempotency, and the expiry sweep semantics.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException


def _make_user(tier="free", user_id=42):
    user = MagicMock()
    user.id = user_id
    user.email = "buyer@osool.com"
    user.full_name = "Test Buyer"
    user.phone_number = "+201234567890"
    user.subscription_tier = tier
    return user


def _paymob_ok(order_id=777):
    return {
        "order_id": order_id,
        "payment_key": "pk_test",
        "iframe_url": f"https://accept.paymob.com/api/acceptance/iframes/1?payment_token=pk_test",
    }


class TestSubscribeEndpoint:
    @pytest.mark.asyncio
    async def test_rejects_when_payments_disabled(self):
        from app.api import billing_endpoints

        with patch.object(billing_endpoints.config, "PAYMENTS_ENABLED", False):
            with pytest.raises(HTTPException) as exc:
                await billing_endpoints.subscribe(
                    current_user=_make_user(), db=AsyncMock()
                )
        assert exc.value.status_code == 503

    @pytest.mark.asyncio
    async def test_rejects_existing_premium(self):
        from app.api import billing_endpoints

        with patch.object(billing_endpoints.config, "PAYMENTS_ENABLED", True):
            with pytest.raises(HTTPException) as exc:
                await billing_endpoints.subscribe(
                    current_user=_make_user(tier="premium"), db=AsyncMock()
                )
        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_creates_pending_subscription_and_typed_transaction(self):
        from app.api import billing_endpoints
        from app.models import Subscription, Transaction

        db = AsyncMock()
        added = []
        db.add = MagicMock(side_effect=added.append)
        no_sub = MagicMock()
        no_sub.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=no_sub)

        with patch.object(billing_endpoints.config, "PAYMENTS_ENABLED", True), \
             patch.object(
                 billing_endpoints.paymob_service, "initiate_payment",
                 new=AsyncMock(return_value=_paymob_ok()),
             ):
            result = await billing_endpoints.subscribe(
                current_user=_make_user(), db=db
            )

        assert result["order_id"] == "777"
        assert "iframe_url" in result
        txns = [a for a in added if isinstance(a, Transaction)]
        subs = [a for a in added if isinstance(a, Subscription)]
        assert len(txns) == 1 and len(subs) == 1
        assert txns[0].transaction_type == "subscription"
        assert txns[0].property_id is None
        assert subs[0].status == "pending"
        assert subs[0].paymob_order_id == "777"
        db.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_paymob_failure_propagates_as_502(self):
        from app.api import billing_endpoints

        db = AsyncMock()
        no_sub = MagicMock()
        no_sub.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=no_sub)

        with patch.object(billing_endpoints.config, "PAYMENTS_ENABLED", True), \
             patch.object(
                 billing_endpoints.paymob_service, "initiate_payment",
                 new=AsyncMock(return_value={"error": "gateway down"}),
             ):
            with pytest.raises(HTTPException) as exc:
                await billing_endpoints.subscribe(current_user=_make_user(), db=db)
        assert exc.value.status_code == 502


class TestReportPurchase:
    @pytest.mark.asyncio
    async def test_creates_pending_report(self):
        from app.api import billing_endpoints
        from app.api.billing_endpoints import ReportPurchaseRequest
        from app.models import PaidReport, Transaction

        db = AsyncMock()
        added = []
        db.add = MagicMock(side_effect=added.append)

        with patch.object(billing_endpoints.config, "PAYMENTS_ENABLED", True), \
             patch.object(
                 billing_endpoints.paymob_service, "initiate_payment",
                 new=AsyncMock(return_value=_paymob_ok(order_id=888)),
             ):
            result = await billing_endpoints.purchase_report(
                req=ReportPurchaseRequest(
                    report_type="valuation",
                    params={"budget_min": 3_000_000, "areas": ["New Cairo"]},
                ),
                current_user=_make_user(),
                db=db,
            )

        assert result["order_id"] == "888"
        reports = [a for a in added if isinstance(a, PaidReport)]
        txns = [a for a in added if isinstance(a, Transaction)]
        assert len(reports) == 1 and len(txns) == 1
        assert txns[0].transaction_type == "report"
        assert reports[0].status == "pending"
        params = json.loads(reports[0].input_params_json)
        assert params["budget_min"] == 3_000_000


class TestSubscriptionWebhook:
    """Webhook branch: subscription payment activates Pro tier."""

    def _request(self, order_id=777):
        request = MagicMock()
        request.query_params = {"hmac": "ok"}
        request.json = AsyncMock(return_value={
            "obj": {
                "id": 1,
                "order": {"id": order_id},
                "amount_cents": 29900,
                "success": True,
                "pending": False,
            }
        })
        return request

    @pytest.mark.asyncio
    async def test_subscription_payment_activates_premium(self):
        from app.api.endpoints import paymob_webhook

        user = _make_user(tier="free")
        tx = MagicMock()
        tx.id = 9
        tx.user_id = user.id
        tx.user = user
        tx.status = "pending"
        tx.transaction_type = "subscription"
        tx.amount = 299.0
        tx.property_id = None

        subscription = MagicMock()
        subscription.status = "pending"

        tx_result = MagicMock()
        tx_result.scalar_one_or_none.return_value = tx
        sub_result = MagicMock()
        sub_result.scalar_one_or_none.return_value = subscription

        db = AsyncMock()
        db.execute = AsyncMock(side_effect=[tx_result, sub_result])
        db.commit = AsyncMock()

        with patch("app.api.endpoints.paymob_service") as svc, \
             patch("app.services.email_service.email_service") as mail:
            svc.verify_hmac.return_value = True
            mail.send_subscription_confirmation = MagicMock(return_value=True)
            result = await paymob_webhook(self._request(), db=db)

        assert result == {"status": "success", "type": "subscription"}
        assert tx.status == "paid"
        assert subscription.status == "active"
        assert subscription.current_period_end is not None
        assert user.subscription_tier == "premium"
        db.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_report_payment_queues_generation(self):
        from app.api.endpoints import paymob_webhook

        tx = MagicMock()
        tx.id = 10
        tx.user_id = 42
        tx.user = _make_user()
        tx.status = "pending"
        tx.transaction_type = "report"
        tx.property_id = None

        paid_report = MagicMock()
        paid_report.id = 5
        paid_report.status = "pending"

        tx_result = MagicMock()
        tx_result.scalar_one_or_none.return_value = tx
        rep_result = MagicMock()
        rep_result.scalar_one_or_none.return_value = paid_report

        db = AsyncMock()
        db.execute = AsyncMock(side_effect=[tx_result, rep_result])

        with patch("app.api.endpoints.paymob_service") as svc, \
             patch(
                 "app.services.paid_report_service.generate_and_deliver_report",
                 new=AsyncMock(return_value=True),
             ) as gen:
            svc.verify_hmac.return_value = True
            result = await paymob_webhook(self._request(order_id=888), db=db)

        assert result == {"status": "success", "type": "report"}
        assert paid_report.status == "paid"

    @pytest.mark.asyncio
    async def test_legacy_property_webhook_unchanged(self):
        """Regression: transactions without a type behave as property payments."""
        from app.api.endpoints import paymob_webhook

        tx = MagicMock()
        tx.id = 11
        tx.user_id = 42
        tx.user = _make_user()
        tx.status = "pending"
        tx.transaction_type = None  # legacy row
        tx.property_id = 3
        tx.amount = 100_000.0

        prop = MagicMock()
        prop.id = 3
        prop.is_available = True
        prop.location = "Sheikh Zayed"

        tx_result = MagicMock()
        tx_result.scalar_one_or_none.return_value = tx
        prop_result = MagicMock()
        prop_result.scalar_one_or_none.return_value = prop

        db = AsyncMock()
        db.execute = AsyncMock(side_effect=[tx_result, prop_result])

        with patch("app.api.endpoints.paymob_service") as svc, \
             patch("app.services.portfolio_engine.create_portfolio_entry", new=AsyncMock()):
            svc.verify_hmac.return_value = True
            result = await paymob_webhook(self._request(order_id=555), db=db)

        assert result["status"] == "success"
        assert tx.status == "paid"
        assert prop.is_available is False


class TestBillingStatus:
    @pytest.mark.asyncio
    async def test_status_shape_for_free_user(self):
        from app.api import billing_endpoints

        no_sub = MagicMock()
        no_sub.scalar_one_or_none.return_value = None
        no_reports = MagicMock()
        no_reports.scalars.return_value.all.return_value = []

        db = AsyncMock()
        db.execute = AsyncMock(side_effect=[no_sub, no_reports])

        result = await billing_endpoints.billing_status(
            current_user=_make_user(tier="free"), db=db
        )
        assert result["tier"] == "free"
        assert result["subscription"] is None
        assert result["reports"] == []
