"""
Unit Tests for AI Tools
------------------------
Tests individual AI tools in isolation.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ai_engine.tools.search import search_properties
from app.ai_engine.tools.valuation import get_ai_valuation
from app.ai_engine.tools.roi_calculator import calculate_roi_projection
from app.ai_engine.tools.payment_calculator import calculate_payment_plan
from app.ai_engine.tools.comparison import compare_properties
from app.ai_engine.tools.blockchain_verification import verify_property_blockchain
from app.ai_engine.tools.viewing_scheduler import schedule_viewing
from app.ai_engine.tools.reservation_generator import generate_reservation_link


# ---------------------------------------------------------------------------
# TEST: PROPERTY SEARCH TOOL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_properties_semantic():
    """Test semantic search returns relevant properties"""

    result = await search_properties(
        query="3-bedroom apartment in New Cairo under 5M",
        limit=10
    )

    assert result["status"] == "success"
    assert "properties" in result
    assert isinstance(result["properties"], list)

    # Should return properties (assuming database has data)
    if len(result["properties"]) > 0:
        property_sample = result["properties"][0]

        # Verify property structure
        assert "id" in property_sample
        assert "title" in property_sample
        assert "price" in property_sample
        assert "location" in property_sample

        # Verify similarity threshold (if included)
        if "similarity" in property_sample:
            assert property_sample["similarity"] >= 0.7  # 70% threshold


@pytest.mark.asyncio
async def test_search_properties_threshold():
    """Test search respects 70% similarity threshold"""

    result = await search_properties(
        query="Luxury penthouse with pool",
        limit=5
    )

    assert result["status"] == "success"

    # All returned properties should meet threshold
    for prop in result["properties"]:
        if "similarity" in prop:
            assert prop["similarity"] >= 0.70, \
                f"Property {prop['id']} has similarity {prop['similarity']} < 0.70"


@pytest.mark.asyncio
async def test_search_properties_no_results():
    """Test search handles no results gracefully"""

    result = await search_properties(
        query="castle on the moon for 100 EGP",  # Absurd query
        limit=10
    )

    assert result["status"] == "success"
    assert "properties" in result
    assert isinstance(result["properties"], list)
    # Empty list is valid response


@pytest.mark.asyncio
async def test_search_properties_filters():
    """Test search with specific filters"""

    result = await search_properties(
        query="apartment",
        limit=10,
        min_price=3000000,
        max_price=5000000,
        bedrooms=3,
        location="New Cairo"
    )

    assert result["status"] == "success"

    # Verify filters were applied
    for prop in result["properties"]:
        assert prop["price"] >= 3000000
        assert prop["price"] <= 5000000
        if "bedrooms" in prop:
            assert prop["bedrooms"] == 3


# ---------------------------------------------------------------------------
# TEST: VALUATION TOOL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_valuation_tool_below_market():
    """Test valuation identifies property below market average"""

    # Mock property data
    with patch("app.ai_engine.tools.valuation.get_property_by_id") as mock_get_property:
        mock_get_property.return_value = {
            "id": 123,
            "title": "Test Property",
            "price": 4000000,
            "bedrooms": 3,
            "location": "New Cairo",
            "area_sqm": 150
        }

        with patch("app.ai_engine.tools.valuation.get_market_average") as mock_market:
            mock_market.return_value = 4500000  # Market average higher

            result = await get_ai_valuation(
                property_id=123,
                listed_price=4000000,
                user_query="Is 4M a good price?"
            )

            assert result["status"] == "success"
            assert "verdict" in result
            assert result["verdict"] == "EXCELLENT_DEAL"  # Below market
            assert result["price_vs_market_percent"] < 0  # Negative = below
            assert abs(result["price_vs_market_percent"]) >= 10  # ~11% below


@pytest.mark.asyncio
async def test_valuation_tool_above_market():
    """Test valuation identifies overpriced property"""

    with patch("app.ai_engine.tools.valuation.get_property_by_id") as mock_get_property:
        mock_get_property.return_value = {
            "id": 456,
            "price": 6000000,
            "bedrooms": 3,
            "location": "6th of October",
            "area_sqm": 180
        }

        with patch("app.ai_engine.tools.valuation.get_market_average") as mock_market:
            mock_market.return_value = 5000000  # Market average lower

            result = await get_ai_valuation(
                property_id=456,
                listed_price=6000000,
                user_query="Is 6M fair?"
            )

            assert result["status"] == "success"
            assert result["verdict"] == "OVERPRICED"
            assert result["price_vs_market_percent"] > 0  # Positive = above
            assert result["price_vs_market_percent"] == 20  # 20% above


@pytest.mark.asyncio
async def test_valuation_tool_fair_price():
    """Test valuation identifies fair market price"""

    with patch("app.ai_engine.tools.valuation.get_property_by_id") as mock_get_property:
        mock_get_property.return_value = {
            "id": 789,
            "price": 5000000,
            "bedrooms": 2,
            "location": "Maadi",
            "area_sqm": 120
        }

        with patch("app.ai_engine.tools.valuation.get_market_average") as mock_market:
            mock_market.return_value = 5100000  # Close to market

            result = await get_ai_valuation(
                property_id=789,
                listed_price=5000000,
                user_query="Fair price?"
            )

            assert result["status"] == "success"
            assert result["verdict"] == "FAIR_PRICE"
            assert abs(result["price_vs_market_percent"]) <= 5  # Within ±5%


@pytest.mark.asyncio
async def test_valuation_tool_invalid_property():
    """Test valuation handles invalid property ID"""

    result = await get_ai_valuation(
        property_id=999999,
        listed_price=5000000,
        user_query="Is this good?"
    )

    assert result["status"] == "error"
    assert "not found" in result["message"].lower()


# ---------------------------------------------------------------------------
# TEST: ROI CALCULATOR TOOL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_roi_projection_tool():
    """Test ROI calculator returns accurate projections"""

    result = await calculate_roi_projection(
        property_id=123,
        purchase_price=5000000,
        appreciation_rate=8.0,  # 8% annual appreciation
        rental_yield=6.0,  # 6% rental yield
        years=[5, 10, 20]
    )

    assert result["status"] == "success"
    assert "projections" in result

    projections = result["projections"]
    assert len(projections) == 3  # 5, 10, 20 years

    # Verify 5-year projection
    proj_5yr = projections[0]
    assert proj_5yr["year"] == 5
    assert "property_value" in proj_5yr
    assert "total_rental_income" in proj_5yr
    assert "total_return" in proj_5yr
    assert "roi_percent" in proj_5yr

    # Verify math: 5M * (1.08^5) ≈ 7.35M
    expected_value_5yr = 5000000 * (1.08 ** 5)
    assert abs(proj_5yr["property_value"] - expected_value_5yr) < 10000  # Within 10K

    # Verify rental income: 5M * 0.06 * 5 years = 1.5M
    expected_rental_5yr = 5000000 * 0.06 * 5
    assert abs(proj_5yr["total_rental_income"] - expected_rental_5yr) < 10000

    # Verify ROI is positive
    assert proj_5yr["roi_percent"] > 0


@pytest.mark.asyncio
async def test_roi_projection_negative_scenario():
    """Test ROI calculator handles market downturn"""

    result = await calculate_roi_projection(
        property_id=123,
        purchase_price=5000000,
        appreciation_rate=-3.0,  # Market downturn
        rental_yield=5.0,
        years=[5]
    )

    assert result["status"] == "success"

    proj = result["projections"][0]

    # Property value should decrease
    assert proj["property_value"] < 5000000

    # But rental income should still be positive
    assert proj["total_rental_income"] > 0

    # ROI might be negative
    # (no assertion, just check it returns value)
    assert "roi_percent" in proj


# ---------------------------------------------------------------------------
# TEST: PAYMENT CALCULATOR TOOL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_payment_calculator_tool():
    """Test payment calculator returns correct installments"""

    result = await calculate_payment_plan(
        property_price=5000000,
        down_payment_percent=20,
        interest_rate=8.5,  # CBE rate
        years=20
    )

    assert result["status"] == "success"
    assert "down_payment" in result
    assert "loan_amount" in result
    assert "monthly_payment" in result
    assert "total_interest" in result
    assert "total_paid" in result

    # Verify down payment
    assert result["down_payment"] == 1000000  # 20% of 5M

    # Verify loan amount
    assert result["loan_amount"] == 4000000  # 80% of 5M

    # Verify monthly payment is reasonable
    assert result["monthly_payment"] > 0
    assert result["monthly_payment"] < 50000  # Sanity check

    # Verify total paid = down payment + (monthly * months)
    expected_total = result["down_payment"] + (result["monthly_payment"] * 20 * 12)
    assert abs(result["total_paid"] - expected_total) < 100  # Rounding tolerance


@pytest.mark.asyncio
async def test_payment_calculator_different_terms():
    """Test payment calculator with different loan terms"""

    # 10-year loan
    result_10yr = await calculate_payment_plan(
        property_price=4000000,
        down_payment_percent=25,
        interest_rate=9.0,
        years=10
    )

    # 20-year loan
    result_20yr = await calculate_payment_plan(
        property_price=4000000,
        down_payment_percent=25,
        interest_rate=9.0,
        years=20
    )

    # 10-year should have higher monthly but less total interest
    assert result_10yr["monthly_payment"] > result_20yr["monthly_payment"]
    assert result_10yr["total_interest"] < result_20yr["total_interest"]


@pytest.mark.asyncio
async def test_payment_calculator_validation():
    """Test payment calculator validates input"""

    # Test invalid down payment (over 100%)
    result = await calculate_payment_plan(
        property_price=5000000,
        down_payment_percent=150,  # Invalid
        interest_rate=8.5,
        years=20
    )

    assert result["status"] == "error"
    assert "down payment" in result["message"].lower()


# ---------------------------------------------------------------------------
# TEST: COMPARISON TOOL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_compare_properties_tool():
    """Test property comparison returns statistical analysis"""

    result = await compare_properties(
        property_ids=[101, 102, 103]
    )

    assert result["status"] == "success"
    assert "properties" in result
    assert len(result["properties"]) == 3

    # Verify comparison includes statistical metrics
    assert "comparison_summary" in result
    summary = result["comparison_summary"]

    assert "best_value" in summary  # Property with best price/sqm
    assert "highest_roi" in summary  # Best investment
    assert "price_range" in summary  # Min-max prices

    # Verify each property has comparison data
    for prop in result["properties"]:
        assert "price_per_sqm" in prop
        assert "roi_estimate" in prop


@pytest.mark.asyncio
async def test_compare_properties_invalid_ids():
    """Test comparison handles invalid property IDs"""

    result = await compare_properties(
        property_ids=[999991, 999992, 999993]  # Non-existent
    )

    # Should return error or empty list
    assert result["status"] in ["success", "error"]

    if result["status"] == "success":
        assert len(result["properties"]) == 0


# ---------------------------------------------------------------------------
# TEST: BLOCKCHAIN VERIFICATION TOOL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_blockchain_verification_tool():
    """Test blockchain verification checks on-chain availability"""

    with patch("app.ai_engine.tools.blockchain_verification.check_onchain_availability") as mock_check:
        mock_check.return_value = {
            "available": True,
            "units_left": 3,
            "last_verified": datetime.now().isoformat()
        }

        result = await verify_property_blockchain(
            property_id=123
        )

        assert result["status"] == "success"
        assert "available" in result
        assert result["available"] == True
        assert result["units_left"] == 3
        assert "last_verified" in result


@pytest.mark.asyncio
async def test_blockchain_verification_unavailable():
    """Test blockchain verification when property sold out"""

    with patch("app.ai_engine.tools.blockchain_verification.check_onchain_availability") as mock_check:
        mock_check.return_value = {
            "available": False,
            "units_left": 0,
            "last_verified": datetime.now().isoformat()
        }

        result = await verify_property_blockchain(
            property_id=456
        )

        assert result["status"] == "success"
        assert result["available"] == False
        assert result["units_left"] == 0


@pytest.mark.asyncio
async def test_blockchain_verification_service_down():
    """Test blockchain verification handles service failures"""

    with patch("app.ai_engine.tools.blockchain_verification.check_onchain_availability") as mock_check:
        mock_check.side_effect = Exception("Blockchain node unreachable")

        result = await verify_property_blockchain(
            property_id=123
        )

        # Should return error but not crash
        assert result["status"] == "error"
        assert "blockchain" in result["message"].lower() or "unavailable" in result["message"].lower()


# ---------------------------------------------------------------------------
# TEST: VIEWING SCHEDULER TOOL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_schedule_viewing_tool():
    """Test viewing scheduler creates viewing request"""

    result = await schedule_viewing(
        property_id=123,
        user_name="Ahmed Mohamed",
        phone_number="+201234567890",
        preferred_date="2024-02-15",
        preferred_time="10:00 AM"
    )

    assert result["status"] == "success"
    assert "viewing_id" in result
    assert "confirmation_message" in result

    # Verify confirmation message is bilingual
    assert any(arabic_char in result["confirmation_message"] for arabic_char in "أبتثج")


@pytest.mark.asyncio
async def test_schedule_viewing_validation():
    """Test viewing scheduler validates input"""

    # Test invalid phone number
    result = await schedule_viewing(
        property_id=123,
        user_name="Ahmed",
        phone_number="invalid",
        preferred_date="2024-02-15",
        preferred_time="10:00 AM"
    )

    assert result["status"] == "error"
    assert "phone" in result["message"].lower()


# ---------------------------------------------------------------------------
# TEST: RESERVATION GENERATOR TOOL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_reservation_link_tool():
    """Test reservation link generator creates secure link"""

    result = await generate_reservation_link(
        property_id=123,
        user_id="user-789",
        session_id="session-456"
    )

    assert result["status"] == "success"
    assert "reservation_link" in result
    assert "expires_at" in result
    assert "validity_hours" in result

    # Verify link format
    link = result["reservation_link"]
    assert link.startswith("https://") or link.startswith("http://")
    assert "reserve" in link
    assert len(link) > 50  # Should have token

    # Verify expiration
    assert result["validity_hours"] == 1  # 1-hour validity


@pytest.mark.asyncio
async def test_generate_reservation_link_hot_lead_only():
    """Test reservation link requires hot lead qualification"""

    # Mock lead score check
    with patch("app.ai_engine.tools.reservation_generator.is_hot_lead") as mock_lead_check:
        mock_lead_check.return_value = False  # Not qualified

        result = await generate_reservation_link(
            property_id=123,
            user_id="user-cold",
            session_id="session-cold"
        )

        assert result["status"] == "error"
        assert "not qualified" in result["message"].lower() or "hot lead" in result["message"].lower()


# ---------------------------------------------------------------------------
# TEST: MARKET ANALYSIS TOOL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_market_analysis_tool():
    """Test market analysis returns trend data"""

    from app.ai_engine.tools.market_analysis import analyze_market_trends

    result = await analyze_market_trends(
        location="New Cairo",
        property_type="apartment",
        timeframe="1year"
    )

    assert result["status"] == "success"
    assert "trends" in result
    assert "average_price_change_percent" in result
    assert "demand_indicator" in result

    # Verify trend data
    trends = result["trends"]
    assert len(trends) > 0  # Should have historical data

    # Verify demand indicator is valid
    assert result["demand_indicator"] in ["HIGH", "MEDIUM", "LOW"]


# ---------------------------------------------------------------------------
# TEST: DEVELOPER TRACK RECORD TOOL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_developer_track_record_tool():
    """Test developer track record analysis"""

    from app.ai_engine.tools.developer_analysis import get_developer_track_record

    result = await get_developer_track_record(
        developer_name="Ora Developers"
    )

    assert result["status"] == "success"
    assert "developer_name" in result
    assert "track_record" in result

    track_record = result["track_record"]
    assert "on_time_delivery_rate" in track_record
    assert "total_projects" in track_record
    assert "reputation_score" in track_record

    # Verify scores are in valid range
    assert 0 <= track_record["on_time_delivery_rate"] <= 100
    assert 0 <= track_record["reputation_score"] <= 5


# ---------------------------------------------------------------------------
# TEST: TOOL ERROR HANDLING
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tool_handles_database_errors():
    """Test tools handle database errors gracefully"""

    with patch("app.ai_engine.tools.search.get_db_session") as mock_db:
        mock_db.side_effect = Exception("Database connection failed")

        result = await search_properties(
            query="test query",
            limit=10
        )

        # Should return error, not crash
        assert result["status"] == "error"
        assert "database" in result["message"].lower() or "error" in result["message"].lower()


@pytest.mark.asyncio
async def test_tool_handles_missing_dependencies():
    """Test tools handle missing data gracefully"""

    # Search for property with missing location data
    result = await get_ai_valuation(
        property_id=999,
        listed_price=5000000,
        user_query="Is this fair?"
    )

    # Should handle missing data gracefully
    assert result["status"] in ["success", "error"]


# ---------------------------------------------------------------------------
# RUN TESTS
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
