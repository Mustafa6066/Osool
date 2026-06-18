"""
Tests for the scraper health / drift guard (Bottleneck #1).

`assess_batch` is the substance (pure, no DB). Covers the failure modes the
price-only AnomalyDetector misses: empty batches, partial-break (count vs
baseline), and schema drift (required fields mostly null).
"""
from __future__ import annotations

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-minimum-32-chars-long")

import pytest  # noqa: E402

from app.ingestion.scraper_health import (  # noqa: E402
    DEFAULT_REQUIRED_FIELDS,
    assess_batch,
    record_and_alert,
)


def _unit(price=5_000_000, compound="Mountain View iCity", size=120):
    return {"price": price, "compound": compound, "size_sqm": size}


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_empty_batch_is_empty_and_blocks_downstream():
    v = assess_batch("nawy_discovery", [], min_count=5)
    assert v.status == "empty"
    assert v.should_block_downstream is True
    assert not v.healthy


def test_healthy_batch_is_ok():
    v = assess_batch("nawy_compound", [_unit(), _unit(), _unit()],
                     required_fields=DEFAULT_REQUIRED_FIELDS)
    assert v.status == "ok"
    assert v.healthy is True
    assert v.should_block_downstream is False


def test_count_far_below_baseline_is_degraded():
    v = assess_batch("nawy_discovery", ["u1", "u2"], baseline_count=100, min_count=1)
    assert v.status == "degraded"
    assert v.should_block_downstream is True
    assert any("baseline" in r for r in v.reasons)


def test_below_absolute_floor_is_degraded():
    v = assess_batch("nawy_discovery", ["u1", "u2"], min_count=5)
    assert v.status == "degraded"
    assert any("floor" in r for r in v.reasons)


def test_schema_drift_when_required_fields_mostly_null():
    # 3 of 4 units have no price -> null rate 0.75 > 0.5 threshold
    items = [
        _unit(price=0),
        _unit(price=None),
        _unit(price=None),
        _unit(price=5_000_000),
    ]
    v = assess_batch("nawy_compound", items, required_fields=("price",))
    assert v.status == "degraded"
    assert v.field_null_rates["price"] == 0.75
    assert any("schema drift" in r for r in v.reasons)


def test_zero_price_counts_as_missing():
    items = [_unit(price=0), _unit(price=0), _unit(price=0)]
    v = assess_batch("nawy_compound", items, required_fields=("price",))
    assert v.field_null_rates["price"] == 1.0
    assert v.status == "degraded"


@pytest.mark.anyio
async def test_record_and_alert_returns_verdict_without_session():
    # Best-effort glue must never raise even with no DB session / no Sentry.
    v = assess_batch("nawy_discovery", [], min_count=5)
    out = await record_and_alert(v, session=None)
    assert out is v
    assert out.status == "empty"
