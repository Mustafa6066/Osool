"""
Deterministic local-router tests for the zero-token chat path.
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.ai_engine.local_router import local_router


def test_local_router_returns_local_success_payload():
    prop = SimpleNamespace(
        id=1,
        title="Best Deal",
        location="New Cairo",
        compound="Taj City",
        developer="XYZ",
        price=7_200_000,
        price_per_sqm=45_000,
        size_sqm=160,
        bedrooms=3,
        sale_type="Resale",
        installment_years=7,
        down_payment=10,
        image_url="https://example.com/image.jpg",
        osool_score=88,
        bargain_percentage=13.4,
    )

    result_set = MagicMock()
    result_set.scalars.return_value.all.return_value = [prop]
    db = AsyncMock()
    db.execute.return_value = result_set

    response = asyncio.run(
        local_router.process_query_async(
            query="I need an apartment in New Cairo for 8 million and 3 rooms",
            session_count=1,
            db=db,
        )
    )

    assert response["type"] == "success"
    assert response["response_type"] == "free_local"
    assert response["show_upsell"] is False
    assert response["cta_actions"] == []
    assert len(response["properties"]) == 1
    assert "Osool Rating" in response["text"]


def test_local_router_returns_upsell_metadata_for_complex_query():
    db = MagicMock()

    response = asyncio.run(
        local_router.process_query_async(
            query="What is the ROI and inflation hedge outlook?",
            session_count=1,
            db=db,
        )
    )

    assert response["type"] == "upsell"
    assert response["response_type"] == "free_local"
    assert response["show_upsell"] is True
    assert response["upsell_reason"] == "complex_forecasting"
    assert len(response["cta_actions"]) == 2
