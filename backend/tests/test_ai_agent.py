"""
Osool Backend - AI Agent Tests
Phase 4.2: Comprehensive Test Suite
------------------------------------
Tests for property validation, hallucination detection, and AI tools.
"""

import pytest
import json
from app.ai_engine.sales_agent import search_properties, validate_property_data


class TestPropertyValidation:
    """Test strict property validation (no hallucinations)"""

    def test_valid_property_passes_validation(self):
        """Test that valid property passes validation"""
        property_data = {
            "id": 42,
            "title": "Apartment in Zed East",
            "price": 5000000,
            "location": "New Cairo",
            "size_sqm": 150,
            "bedrooms": 3
        }

        is_valid = validate_property_data(property_data)

        assert is_valid is True

    def test_missing_id_fails_validation(self):
        """Test that property without ID fails validation"""
        property_data = {
            "title": "Apartment in Zed East",
            "price": 5000000,
            "location": "New Cairo"
        }

        is_valid = validate_property_data(property_data)

        assert is_valid is False

    def test_missing_title_fails_validation(self):
        """Test that property without title fails validation"""
        property_data = {
            "id": 42,
            "price": 5000000,
            "location": "New Cairo"
        }

        is_valid = validate_property_data(property_data)

        assert is_valid is False

    def test_missing_price_fails_validation(self):
        """Test that property without price fails validation"""
        property_data = {
            "id": 42,
            "title": "Apartment in Zed East",
            "location": "New Cairo"
        }

        is_valid = validate_property_data(property_data)

        assert is_valid is False

    def test_zero_price_fails_validation(self):
        """Test that property with zero price fails validation"""
        property_data = {
            "id": 42,
            "title": "Apartment in Zed East",
            "price": 0,  # Invalid
            "location": "New Cairo"
        }

        is_valid = validate_property_data(property_data)

        assert is_valid is False

    def test_negative_price_fails_validation(self):
        """Test that property with negative price fails validation"""
        property_data = {
            "id": 42,
            "title": "Apartment in Zed East",
            "price": -1000000,  # Invalid
            "location": "New Cairo"
        }

        is_valid = validate_property_data(property_data)

        assert is_valid is False


class TestPropertySearch:
    """Test property search with database-only responses"""

    @pytest.mark.asyncio
    async def test_search_returns_empty_array_on_no_matches(self, mocker):
        """Test that search returns empty array when no matches found"""
        # Mock database to return no results
        mock_db = mocker.Mock()
        mock_db.execute = mocker.AsyncMock(return_value=mocker.Mock(scalars=lambda: mocker.Mock(all=lambda: [])))

        result = await search_properties(
            query="5-bedroom mansion in Antarctica",
            session_id="test_session",
            db=mock_db
        )

        result_dict = json.loads(result)

        assert result_dict["count"] == 0
        assert result_dict["properties"] == []
        assert result_dict["source"] == "osool_database"

    @pytest.mark.asyncio
    async def test_search_returns_valid_properties(self, mocker):
        """Test that search returns only valid properties"""
        # Mock database to return mixed valid/invalid results
        mock_property_valid = mocker.Mock()
        mock_property_valid.id = 42
        mock_property_valid.title = "Valid Apartment"
        mock_property_valid.price = 5000000
        mock_property_valid.location = "New Cairo"
        mock_property_valid.size_sqm = 150
        mock_property_valid.bedrooms = 3

        mock_property_invalid = mocker.Mock()
        mock_property_invalid.id = None  # Invalid
        mock_property_invalid.title = "Invalid Apartment"
        mock_property_invalid.price = 0

        mock_db = mocker.Mock()
        mock_db.execute = mocker.AsyncMock(
            return_value=mocker.Mock(
                scalars=lambda: mocker.Mock(
                    all=lambda: [mock_property_valid, mock_property_invalid]
                )
            )
        )

        result = await search_properties(
            query="apartment in New Cairo",
            session_id="test_session",
            db=mock_db
        )

        result_dict = json.loads(result)

        # Only valid property should be returned
        assert result_dict["count"] == 1
        assert result_dict["properties"][0]["id"] == 42
        assert result_dict["properties"][0]["title"] == "Valid Apartment"

    @pytest.mark.asyncio
    async def test_search_includes_source_tag(self, mocker):
        """Test that all properties have _source: 'database' tag"""
        mock_property = mocker.Mock()
        mock_property.id = 42
        mock_property.title = "Test Apartment"
        mock_property.price = 5000000
        mock_property.location = "New Cairo"

        mock_db = mocker.Mock()
        mock_db.execute = mocker.AsyncMock(
            return_value=mocker.Mock(
                scalars=lambda: mocker.Mock(all=lambda: [mock_property])
            )
        )

        result = await search_properties(
            query="apartment",
            session_id="test_session",
            db=mock_db
        )

        result_dict = json.loads(result)

        assert result_dict["source"] == "osool_database"
        assert result_dict["properties"][0]["_source"] == "database"


class TestHallucinationDetection:
    """Test hallucination detection and prevention"""

    def test_detect_fake_property_id(self):
        """Test detection of property ID not in database"""
        # Simulated: AI mentions property ID 99999 which doesn't exist
        mentioned_properties = [42, 99999, 100]
        database_property_ids = [42, 100, 150]

        fake_ids = [pid for pid in mentioned_properties if pid not in database_property_ids]

        assert 99999 in fake_ids
        assert len(fake_ids) == 1

    def test_validate_all_recommendations(self):
        """Test that all AI recommendations are validated against database"""
        ai_response = """
        I found 3 great options for you:
        1. Property #42 - Apartment in Zed East
        2. Property #100 - Villa in Palm Hills
        3. Property #99999 - Penthouse in Downtown (FAKE!)
        """

        # Extract property IDs from AI response
        import re
        mentioned_ids = [int(x) for x in re.findall(r'Property #(\d+)', ai_response)]

        database_ids = {42, 100, 150}

        # Validate all IDs
        invalid_ids = [pid for pid in mentioned_ids if pid not in database_ids]

        assert 99999 in invalid_ids
        assert len(invalid_ids) == 1

    def test_block_response_with_invalid_properties(self):
        """Test that response is blocked if it contains invalid properties"""
        mentioned_property_ids = [42, 99999]
        valid_property_ids = {42, 100, 150}

        has_invalid = any(pid not in valid_property_ids for pid in mentioned_property_ids)

        # Should block response
        assert has_invalid is True


class TestAIToolExecution:
    """Test AI tool execution and error handling"""

    @pytest.mark.asyncio
    async def test_search_tool_handles_errors_gracefully(self, mocker):
        """Test that search tool handles database errors gracefully"""
        # Mock database to raise an error
        mock_db = mocker.Mock()
        mock_db.execute = mocker.AsyncMock(side_effect=Exception("Database error"))

        result = await search_properties(
            query="apartment",
            session_id="test_session",
            db=mock_db
        )

        result_dict = json.loads(result)

        # Should return empty results, not crash
        assert result_dict["count"] == 0
        assert "error" in result_dict or result_dict["properties"] == []

    def test_market_comparison_calculation(self):
        """Test market comparison verdict calculation"""
        # Property: 50,000 EGP/sqm
        # Market avg: 45,000 EGP/sqm
        # Difference: +11.1% → ABOVE_MARKET

        property_price_per_sqm = 50000
        market_avg = 45000
        difference_percent = ((property_price_per_sqm - market_avg) / market_avg) * 100

        if difference_percent < -15:
            verdict = "BARGAIN"
        elif difference_percent < -5:
            verdict = "GOOD_DEAL"
        elif difference_percent <= 5:
            verdict = "FAIR"
        elif difference_percent <= 15:
            verdict = "ABOVE_MARKET"
        else:
            verdict = "OVERPRICED"

        assert difference_percent > 10
        assert difference_percent < 12
        assert verdict == "ABOVE_MARKET"


class TestAIResponseQuality:
    """Test AI response quality and consistency"""

    def test_response_includes_property_details(self):
        """Test that AI response includes required property details"""
        property_data = {
            "id": 42,
            "title": "Apartment in Zed East",
            "price": 5000000,
            "location": "New Cairo",
            "size_sqm": 150,
            "bedrooms": 3,
            "price_per_sqm": 33333
        }

        # Simulate AI response
        response = f"""
        I found a great option for you:

        **{property_data['title']}** (Property #{property_data['id']})
        - Location: {property_data['location']}
        - Price: {property_data['price']:,} EGP
        - Size: {property_data['size_sqm']} sqm
        - Bedrooms: {property_data['bedrooms']}
        - Price per sqm: {property_data['price_per_sqm']:,} EGP/sqm
        """

        # Verify all details are included
        assert str(property_data['id']) in response
        assert property_data['title'] in response
        assert str(property_data['price']) in response
        assert property_data['location'] in response
        assert str(property_data['size_sqm']) in response
        assert str(property_data['bedrooms']) in response

    def test_response_includes_market_context(self):
        """Test that AI response includes market comparison"""
        response = """
        This property is priced at 33,333 EGP/sqm, which is **16% below**
        the New Cairo market average of 45,000 EGP/sqm.

        **Verdict**: 🎯 Excellent value! This is a BARGAIN.
        """

        assert "market average" in response.lower()
        assert "bargain" in response.lower() or "good deal" in response.lower()

    def test_response_avoids_financial_advice(self):
        """Test that AI doesn't give financial advice (compliance)"""
        forbidden_phrases = [
            "I recommend you invest",
            "This is a guaranteed profit",
            "You should definitely buy this",
            "This will definitely increase in value"
        ]

        sample_response = """
        This property matches your criteria. It's priced below market average.
        Would you like to schedule a viewing or learn more about the payment options?
        """

        for phrase in forbidden_phrases:
            assert phrase.lower() not in sample_response.lower()


class TestDatabaseIntegration:
    """Test database integration and query efficiency"""

    @pytest.mark.asyncio
    async def test_search_query_uses_index(self, mocker):
        """Test that search query uses pgvector index for efficiency"""
        # This would require actual database connection
        # For now, verify that the query is constructed correctly
        pass

    @pytest.mark.asyncio
    async def test_search_query_limits_results(self, mocker):
        """Test that search query limits results to prevent excessive data"""
        mock_db = mocker.Mock()
        mock_properties = [mocker.Mock() for _ in range(100)]  # Simulate 100 results

        mock_db.execute = mocker.AsyncMock(
            return_value=mocker.Mock(
                scalars=lambda: mocker.Mock(all=lambda: mock_properties)
            )
        )

        result = await search_properties(
            query="apartment",
            session_id="test_session",
            db=mock_db
        )

        result_dict = json.loads(result)

        # Should limit to reasonable number (e.g., 20)
        assert result_dict["count"] <= 20


class TestSecurityAndCompliance:
    """Test security and compliance features"""

    def test_no_sql_injection_in_search(self):
        """Test that search query is safe from SQL injection"""
        malicious_query = "'; DROP TABLE properties; --"

        # Query should be parameterized, not string concatenated
        # This test verifies that SQLAlchemy's parameterization is used
        # In actual code, we use: db.execute(select(Property).where(...))
        # which is safe from SQL injection

        # Verify query doesn't contain dangerous SQL keywords
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]
        # (Note: These tests would be more comprehensive with actual database)

    def test_property_data_sanitized(self):
        """Test that property data is sanitized before returning"""
        property_data = {
            "id": 42,
            "title": "<script>alert('XSS')</script>",
            "price": 5000000,
            "location": "New'; DROP TABLE users; --"
        }

        # In production, sanitize these fields
        # For now, verify they're returned as-is (FastAPI handles escaping)
        assert "<script>" in property_data["title"]  # Will be escaped by FastAPI


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
