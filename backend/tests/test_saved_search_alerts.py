"""
Osool Backend — Saved-Search Alerts Tests
------------------------------------------
The daily Pro-only alert sweep: premium owners get digest emails for new
matches / price drops; free users' searches are skipped entirely.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import saved_search_alerts


def _search(user_tier: str, search_id: int = 1):
    search = MagicMock()
    search.id = search_id
    search.name = "شقق التجمع"
    search.filters_json = json.dumps({"location": "New Cairo", "budget_max": 6_000_000})
    search.is_active = True
    search.last_checked_at = None
    search.match_count = 0

    user = MagicMock()
    user.id = 42
    user.email = "buyer@osool.com"
    user.subscription_tier = user_tier
    return search, user


def _prop(prop_id=1, price=5_000_000.0):
    prop = MagicMock()
    prop.id = prop_id
    prop.title = "Test Apartment"
    prop.compound = "Test Compound"
    prop.location = "New Cairo"
    prop.price = price
    prop.size_sqm = 150
    return prop


def _session_factory(rows, new_props, drops):
    session = AsyncMock()
    rows_result = MagicMock()
    rows_result.all.return_value = rows
    session.execute = AsyncMock(return_value=rows_result)
    session.commit = AsyncMock()

    factory = MagicMock()
    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    factory.return_value = ctx
    return factory, session


class TestSavedSearchAlerts:
    @pytest.mark.asyncio
    async def test_premium_user_gets_alert_email(self):
        search, user = _search("premium")
        factory, _ = _session_factory([(search, user)], [_prop()], [])

        email_mock = MagicMock()
        with patch.object(saved_search_alerts, "AsyncSessionLocal", factory), \
             patch.object(
                 saved_search_alerts, "_new_matches",
                 new=AsyncMock(return_value=[_prop()]),
             ), \
             patch.object(
                 saved_search_alerts, "_price_drops", new=AsyncMock(return_value=[])
             ), \
             patch("app.services.email_service.email_service", email_mock):
            summary = await saved_search_alerts.run_saved_search_alerts()

        assert summary["searches_checked"] == 1
        assert summary["alerts_sent"] == 1
        email_mock._send_email.assert_called_once()
        assert search.match_count == 1
        assert search.last_checked_at is not None

    @pytest.mark.asyncio
    async def test_free_user_search_is_skipped(self):
        search, user = _search("free")
        factory, _ = _session_factory([(search, user)], [], [])

        email_mock = MagicMock()
        with patch.object(saved_search_alerts, "AsyncSessionLocal", factory), \
             patch("app.services.email_service.email_service", email_mock):
            summary = await saved_search_alerts.run_saved_search_alerts()

        assert summary["skipped_free"] == 1
        assert summary["searches_checked"] == 0
        email_mock._send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_matches_sends_nothing(self):
        search, user = _search("premium")
        factory, _ = _session_factory([(search, user)], [], [])

        email_mock = MagicMock()
        with patch.object(saved_search_alerts, "AsyncSessionLocal", factory), \
             patch.object(saved_search_alerts, "_new_matches", new=AsyncMock(return_value=[])), \
             patch.object(saved_search_alerts, "_price_drops", new=AsyncMock(return_value=[])), \
             patch("app.services.email_service.email_service", email_mock):
            summary = await saved_search_alerts.run_saved_search_alerts()

        assert summary["alerts_sent"] == 0
        email_mock._send_email.assert_not_called()
        # last_checked_at still advances so the window doesn't grow unbounded
        assert search.last_checked_at is not None

    @pytest.mark.asyncio
    async def test_price_drop_appears_in_email_body(self):
        search, user = _search("premium")
        event = MagicMock()
        event.old_price = 5_000_000.0
        event.new_price = 4_400_000.0
        event.pct_change = -0.12
        drops = [(_prop(price=4_400_000.0), event)]
        factory, _ = _session_factory([(search, user)], [], drops)

        email_mock = MagicMock()
        with patch.object(saved_search_alerts, "AsyncSessionLocal", factory), \
             patch.object(saved_search_alerts, "_new_matches", new=AsyncMock(return_value=[])), \
             patch.object(saved_search_alerts, "_price_drops", new=AsyncMock(return_value=drops)), \
             patch("app.services.email_service.email_service", email_mock):
            await saved_search_alerts.run_saved_search_alerts()

        _, _, html = email_mock._send_email.call_args.args
        assert "12" in html       # the drop percentage
        assert "wa.me" in html    # WhatsApp share deep link
