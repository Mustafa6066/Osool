"""
Osool Backend — Ingestion Validation & Price Event Tests
---------------------------------------------------------
Tests the upsert validation gate (reject zero-price / location-less records)
and per-property price event capture added to the differential upsert.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.ingestion.deterministic_normalizer import NormalizedProperty
from app.ingestion.repository import compute_content_hash, upsert_properties


def _norm_prop(**overrides) -> NormalizedProperty:
    defaults = dict(
        title="Test Apartment",
        description="Nice unit",
        type="Apartment",
        location="New Cairo",
        compound="Test Compound",
        developer="Test Dev",
        price=5_000_000.0,
        price_per_sqm=33_000.0,
        size_sqm=150,
        bedrooms=3,
        bathrooms=2,
        finishing="Fully Finished",
        delivery_date="2027",
        down_payment_percentage=10,
        installment_years=8,
        monthly_installment=45_000.0,
        image_url="https://example.com/img.jpg",
        nawy_url="https://www.nawy.com/property/test-1",
        nawy_reference="REF-1",
        sale_type="developer_sale",
        is_nawy_now=False,
        is_delivered=False,
        is_cash_only=False,
        land_area=None,
        maintenance_fee_pct=None,
        delivery_payment=None,
    )
    defaults.update(overrides)
    return NormalizedProperty(**defaults)


class TestContentHash:
    def test_hash_stable_for_same_signal(self):
        assert compute_content_hash(_norm_prop()) == compute_content_hash(_norm_prop())

    def test_hash_changes_on_price(self):
        assert compute_content_hash(_norm_prop()) != compute_content_hash(
            _norm_prop(price=5_500_000.0)
        )

    def test_hash_ignores_cosmetic_fields(self):
        a = compute_content_hash(_norm_prop(title="A", description="x"))
        b = compute_content_hash(_norm_prop(title="B", description="y"))
        assert a == b


def _mock_session_factory(execute_results):
    """Builds an AsyncSessionLocal replacement yielding a mocked session."""
    session = AsyncMock()
    session.execute = AsyncMock(side_effect=execute_results)
    session.commit = AsyncMock()

    factory = MagicMock()
    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    factory.return_value = ctx
    return factory, session


class TestValidationGate:
    @pytest.mark.asyncio
    async def test_rejects_zero_price_and_missing_location(self):
        props = [
            _norm_prop(price=0.0, nawy_url="https://www.nawy.com/property/bad-1"),
            _norm_prop(location="", nawy_url="https://www.nawy.com/property/bad-2"),
        ]
        # All records rejected → upsert returns before touching the DB
        result = await upsert_properties(props, run_id="run-test")
        assert result.errors == 2
        assert result.inserted == 0 and result.updated == 0
        assert any("non-positive price" in d for d in result.error_details)
        assert any("missing location" in d for d in result.error_details)

    @pytest.mark.asyncio
    async def test_valid_records_pass_the_gate(self):
        prop = _norm_prop()
        prefetch = MagicMock()
        prefetch.__iter__ = MagicMock(return_value=iter([]))
        factory, session = _mock_session_factory([prefetch, MagicMock()])

        with patch("app.ingestion.repository.AsyncSessionLocal", factory), \
             patch("app.ingestion.repository._flush_batch", new=AsyncMock()) as flush:
            result = await upsert_properties([prop], run_id="run-test")

        assert result.errors == 0
        assert result.inserted == 1
        flush.assert_awaited()


class TestPriceEventCapture:
    @pytest.mark.asyncio
    async def test_price_change_records_event(self):
        url = "https://www.nawy.com/property/test-1"
        old = _norm_prop(price=5_000_000.0)
        new = _norm_prop(price=4_500_000.0)  # 10% drop

        prefetch_row = MagicMock()
        prefetch_row.nawy_url = url
        prefetch_row.content_hash = compute_content_hash(old)
        prefetch_row.id = 77
        prefetch_row.price = 5_000_000.0
        prefetch = MagicMock()
        prefetch.__iter__ = MagicMock(return_value=iter([prefetch_row]))

        session = AsyncMock()
        session.execute = AsyncMock(
            side_effect=[prefetch, MagicMock(), MagicMock(), MagicMock()]
        )
        session.commit = AsyncMock()
        factory = MagicMock()
        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=session)
        ctx.__aexit__ = AsyncMock(return_value=False)
        factory.return_value = ctx

        with patch("app.ingestion.repository.AsyncSessionLocal", factory), \
             patch("app.ingestion.repository._flush_batch", new=AsyncMock()):
            result = await upsert_properties([new], run_id="run-2")

        assert result.updated == 1
        # Second execute call is the price-event insert (after the prefetch)
        assert session.execute.await_count >= 2
        insert_stmt = session.execute.await_args_list[-1].args[0]
        assert insert_stmt.table.name == "property_price_events"

    @pytest.mark.asyncio
    async def test_unchanged_price_records_no_event(self):
        url = "https://www.nawy.com/property/test-1"
        same = _norm_prop(price=5_000_000.0, finishing="Furnished")  # hash changes, price same

        prefetch_row = MagicMock()
        prefetch_row.nawy_url = url
        prefetch_row.content_hash = compute_content_hash(_norm_prop(price=5_000_000.0))
        prefetch_row.id = 77
        prefetch_row.price = 5_000_000.0
        prefetch = MagicMock()
        prefetch.__iter__ = MagicMock(return_value=iter([prefetch_row]))

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[prefetch, MagicMock()])
        session.commit = AsyncMock()
        factory = MagicMock()
        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=session)
        ctx.__aexit__ = AsyncMock(return_value=False)
        factory.return_value = ctx

        with patch("app.ingestion.repository.AsyncSessionLocal", factory), \
             patch("app.ingestion.repository._flush_batch", new=AsyncMock()):
            result = await upsert_properties([same], run_id="run-3")

        assert result.updated == 1
        # Only the prefetch execute — no price-event insert
        for call in session.execute.await_args_list[1:]:
            stmt = call.args[0]
            table = getattr(getattr(stmt, "table", None), "name", "")
            assert table != "property_price_events"
