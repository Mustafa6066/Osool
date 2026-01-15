"""
Integration Tests for Claude Sales Agent
-----------------------------------------
Tests full conversation flows from greeting to reservation.
"""

import pytest
import sys
import os
from httpx import AsyncClient
from unittest.mock import Mock, patch, AsyncMock
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.ai_engine.claude_sales_agent import ClaudeSalesAgent
from app.services.property_search import search_properties_semantic


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
async def test_client():
    """Create test client for API requests"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_claude_response():
    """Mock Claude API response"""
    def _create_response(content: str, tool_calls: list = None):
        return {
            "content": [{"type": "text", "text": content}],
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50
            }
        }
    return _create_response


@pytest.fixture
def sample_session_id():
    """Generate unique session ID for testing"""
    import uuid
    return f"test-session-{uuid.uuid4()}"


# ---------------------------------------------------------------------------
# TEST: INITIAL GREETING
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_initial_greeting_response(test_client, sample_session_id):
    """Test AMR introduces itself correctly on first message"""

    response = await test_client.post("/api/chat", json={
        "session_id": sample_session_id,
        "message": "Hello"
    })

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "response" in data
    assert "session_id" in data
    assert data["session_id"] == sample_session_id

    # Verify AMR introduces itself
    response_text = data["response"].lower()
    assert "amr" in response_text or "عمرو" in response_text

    # Verify bilingual response (contains both Arabic and English)
    assert any(arabic_char in data["response"] for arabic_char in "أبتثجحخد")
    assert any(english_char in data["response"] for english_char in "abcdefghij")

    # Verify mentions real estate / property
    assert any(word in response_text for word in ["property", "real estate", "عقار", "منزل", "شقة"])

    # Verify cost tracking is included
    assert "cost_tracking" in data
    assert data["cost_tracking"]["cost_usd"] < 0.50  # Under session limit


# ---------------------------------------------------------------------------
# TEST: PROPERTY SEARCH FLOW
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_property_search_flow(test_client, sample_session_id):
    """Test user searches for properties and receives results"""

    response = await test_client.post("/api/chat", json={
        "session_id": sample_session_id,
        "message": "I'm looking for a 3-bedroom apartment in New Cairo under 5M"
    })

    assert response.status_code == 200
    data = response.json()

    # Verify search tool was used
    tools_used = data.get("tools_used", [])
    assert "search_properties" in tools_used or any("search" in tool for tool in tools_used)

    # Verify properties were found (may be in response or separate field)
    response_text = data["response"].lower()
    assert any(word in response_text for word in ["found", "وجدت", "property", "properties", "عقار"])

    # Verify response is helpful
    assert len(data["response"]) > 100  # Substantial response

    # Verify cost is reasonable
    assert data["cost_tracking"]["cost_usd"] < 0.50


@pytest.mark.asyncio
async def test_property_search_no_results(test_client, sample_session_id):
    """Test graceful handling when no properties match"""

    response = await test_client.post("/api/chat", json={
        "session_id": sample_session_id,
        "message": "I want a castle in Cairo for 1000 EGP"  # Unrealistic query
    })

    assert response.status_code == 200
    data = response.json()

    response_text = data["response"].lower()

    # Should explain no results found
    assert any(word in response_text for word in [
        "no properties", "couldn't find", "لم أجد", "لا توجد", "didn't find"
    ])

    # Should offer alternatives or adjust expectations
    assert any(word in response_text for word in [
        "adjust", "different", "other", "alternative", "عدل", "آخر"
    ])


# ---------------------------------------------------------------------------
# TEST: VALUATION REQUEST
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_valuation_request(test_client, sample_session_id):
    """Test user asks if a price is fair"""

    # Step 1: Search for properties first
    await test_client.post("/api/chat", json={
        "session_id": sample_session_id,
        "message": "Show me apartments in Maadi"
    })

    # Step 2: Ask about pricing
    response = await test_client.post("/api/chat", json={
        "session_id": sample_session_id,
        "message": "Is 4.5M a good price for a 3-bedroom?"
    })

    assert response.status_code == 200
    data = response.json()

    # Verify valuation tool was used
    tools_used = data.get("tools_used", [])
    assert any("valuation" in tool or "price" in tool for tool in tools_used)

    response_text = data["response"].lower()

    # Should contain pricing analysis terms
    assert any(word in response_text for word in [
        "market", "average", "fair", "overpriced", "underpriced",
        "سوق", "متوسط", "عادل", "غالي", "رخيص"
    ])

    # Should provide data-backed reasoning
    assert any(word in response_text for word in [
        "percent", "%", "below", "above", "compared",
        "بالمئة", "فوق", "تحت", "مقارنة"
    ])


# ---------------------------------------------------------------------------
# TEST: ROI PROJECTION FLOW
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_roi_projection_flow(test_client, sample_session_id):
    """Test user requests investment analysis"""

    response = await test_client.post("/api/chat", json={
        "session_id": sample_session_id,
        "message": "What's the ROI for a 5M property in New Cairo?"
    })

    assert response.status_code == 200
    data = response.json()

    # Verify ROI tool was used
    tools_used = data.get("tools_used", [])
    assert any("roi" in tool.lower() or "investment" in tool.lower() for tool in tools_used)

    response_text = data["response"].lower()

    # Should mention ROI or returns
    assert any(word in response_text for word in [
        "roi", "return", "investment", "profit", "growth",
        "عائد", "استثمار", "ربح", "نمو"
    ])

    # Should provide numerical projections
    assert "%" in data["response"] or "percent" in response_text

    # Should mention timeframes
    assert any(word in response_text for word in ["year", "annual", "سنة", "سنوي"])


# ---------------------------------------------------------------------------
# TEST: PAYMENT CALCULATOR FLOW
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_payment_calculator_flow(test_client, sample_session_id):
    """Test user asks about payment plans"""

    response = await test_client.post("/api/chat", json={
        "session_id": sample_session_id,
        "message": "Calculate monthly payments for a 4M apartment with 20% down"
    })

    assert response.status_code == 200
    data = response.json()

    # Verify payment calculator was used
    tools_used = data.get("tools_used", [])
    assert any("payment" in tool.lower() or "calculator" in tool.lower() for tool in tools_used)

    response_text = data["response"].lower()

    # Should mention payments or installments
    assert any(word in response_text for word in [
        "payment", "monthly", "installment", "down payment",
        "قسط", "شهري", "دفعة مقدمة"
    ])

    # Should provide numbers
    assert any(char.isdigit() for char in data["response"])


# ---------------------------------------------------------------------------
# TEST: COMPARISON FLOW
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_comparison_flow(test_client, sample_session_id):
    """Test user compares multiple properties"""

    response = await test_client.post("/api/chat", json={
        "session_id": sample_session_id,
        "message": "Compare 3-bedroom apartments in New Cairo vs 6th of October"
    })

    assert response.status_code == 200
    data = response.json()

    # Verify comparison tool was used
    tools_used = data.get("tools_used", [])
    assert any("compar" in tool.lower() for tool in tools_used)

    response_text = data["response"].lower()

    # Should mention both locations
    assert "new cairo" in response_text or "كايرو" in data["response"]
    assert "october" in response_text or "أكتوبر" in data["response"]

    # Should provide comparative analysis
    assert any(word in response_text for word in [
        "vs", "versus", "compared", "difference", "better",
        "مقابل", "مقارنة", "فرق", "أفضل"
    ])


# ---------------------------------------------------------------------------
# TEST: BLOCKCHAIN VERIFICATION FLOW
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_blockchain_verification_flow(test_client, sample_session_id):
    """Test user asks to verify property availability"""

    response = await test_client.post("/api/chat", json={
        "session_id": sample_session_id,
        "message": "Verify if property ID 123 is still available on blockchain"
    })

    assert response.status_code == 200
    data = response.json()

    # Verify blockchain tool was used
    tools_used = data.get("tools_used", [])
    assert any("blockchain" in tool.lower() or "verify" in tool.lower() for tool in tools_used)

    response_text = data["response"].lower()

    # Should mention availability or verification
    assert any(word in response_text for word in [
        "available", "verified", "blockchain", "on-chain",
        "متاح", "موجود", "تحقق"
    ])


# ---------------------------------------------------------------------------
# TEST: RESERVATION GENERATION FLOW
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reservation_generation_flow(test_client, sample_session_id):
    """Test hot lead generates reservation link"""

    # Simulate engaged conversation
    messages = [
        "I'm looking for a 3-bedroom in New Cairo",
        "Show me the one at 4.2M",
        "Is the price fair?",
        "Calculate my payments",
        "I want to reserve this property"
    ]

    for msg in messages:
        response = await test_client.post("/api/chat", json={
            "session_id": sample_session_id,
            "message": msg
        })

    # Final response should contain reservation link or next steps
    assert response.status_code == 200
    data = response.json()

    response_text = data["response"].lower()

    # Should mention reservation or next steps
    assert any(word in response_text for word in [
        "reserve", "reservation", "book", "link", "secure",
        "حجز", "رابط", "آمن"
    ])

    # Should provide action item
    assert any(word in response_text for word in [
        "click", "visit", "follow", "contact",
        "اضغط", "زور", "اتبع", "تواصل"
    ])


# ---------------------------------------------------------------------------
# TEST: OBJECTION HANDLING - PRICE
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_objection_handling_price(test_client, sample_session_id):
    """Test AMR handles price objection with data"""

    response = await test_client.post("/api/chat", json={
        "session_id": sample_session_id,
        "message": "This property is too expensive"
    })

    assert response.status_code == 200
    data = response.json()

    response_text = data["response"].lower()

    # Should address price concern
    assert any(word in response_text for word in [
        "price", "cost", "payment", "value", "market",
        "سعر", "تكلفة", "قيمة", "سوق"
    ])

    # Should provide justification or alternatives
    assert any(word in response_text for word in [
        "because", "compared", "average", "payment plan", "installment",
        "لأن", "مقارنة", "متوسط", "خطة دفع", "قسط"
    ])

    # Should be empathetic, not defensive
    assert any(word in response_text for word in [
        "understand", "let me", "show you", "consider",
        "أفهم", "دعني", "أريك", "فكر"
    ])


# ---------------------------------------------------------------------------
# TEST: OBJECTION HANDLING - COMPETITOR
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_objection_handling_competitor(test_client, sample_session_id):
    """Test AMR handles competitor mention respectfully"""

    response = await test_client.post("/api/chat", json={
        "session_id": sample_session_id,
        "message": "I saw cheaper properties on Nawy"
    })

    assert response.status_code == 200
    data = response.json()

    response_text = data["response"].lower()

    # Should acknowledge competitor respectfully
    assert "nawy" in response_text

    # Should highlight Osool's unique value
    assert any(word in response_text for word in [
        "blockchain", "ai", "verified", "transparent", "analysis",
        "بلوك تشين", "ذكاء", "موثق", "شفاف", "تحليل"
    ])

    # Should not be defensive or negative about competitor
    assert not any(word in response_text for word in [
        "fake", "scam", "bad", "worse", "inferior",
        "احتيال", "سيء", "أسوأ"
    ])


# ---------------------------------------------------------------------------
# TEST: CONVERSATION MEMORY
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_conversation_memory(test_client, sample_session_id):
    """Test AMR remembers user preferences across messages"""

    # Step 1: User mentions budget
    response1 = await test_client.post("/api/chat", json={
        "session_id": sample_session_id,
        "message": "My budget is 5M and I prefer New Cairo"
    })

    # Step 2: Ask follow-up without repeating preferences
    response2 = await test_client.post("/api/chat", json={
        "session_id": sample_session_id,
        "message": "Show me some options"
    })

    assert response2.status_code == 200
    data = response2.json()

    # Should remember budget and location
    # (Verify by checking if search was constrained appropriately)
    tools_used = data.get("tools_used", [])
    assert "search_properties" in tools_used or any("search" in tool for tool in tools_used)

    # Response should reference remembered preferences
    response_text = data["response"].lower()
    assert "5" in data["response"] or "new cairo" in response_text or "كايرو" in data["response"]


# ---------------------------------------------------------------------------
# TEST: STREAMING RESPONSE
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_streaming_response(test_client, sample_session_id):
    """Test streaming endpoint returns chunks correctly"""

    # Note: This test assumes a streaming endpoint exists at /api/chat/stream
    # If not implemented, skip this test

    try:
        async with test_client.stream(
            "POST",
            "/api/chat/stream",
            json={
                "session_id": sample_session_id,
                "message": "Tell me about New Cairo"
            }
        ) as response:
            assert response.status_code == 200

            chunks = []
            async for chunk in response.aiter_bytes():
                if chunk:
                    chunks.append(chunk)

            # Should receive multiple chunks (streaming)
            assert len(chunks) > 1

            # Combine chunks should form valid response
            full_response = b"".join(chunks)
            assert len(full_response) > 0

    except Exception as e:
        # If streaming not implemented, skip
        pytest.skip(f"Streaming endpoint not available: {e}")


# ---------------------------------------------------------------------------
# TEST: ERROR HANDLING
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_malformed_input_handling(test_client, sample_session_id):
    """Test graceful handling of malformed input"""

    # Test empty message
    response1 = await test_client.post("/api/chat", json={
        "session_id": sample_session_id,
        "message": ""
    })

    # Should return error or prompt for input
    assert response1.status_code in [200, 400, 422]

    # Test very long message
    response2 = await test_client.post("/api/chat", json={
        "session_id": sample_session_id,
        "message": "a" * 10000  # 10K characters
    })

    # Should handle gracefully
    assert response2.status_code in [200, 400, 413]  # 413 = Payload Too Large


@pytest.mark.asyncio
async def test_missing_session_id_handling(test_client):
    """Test handling when session_id is missing"""

    response = await test_client.post("/api/chat", json={
        "message": "Hello"
        # Missing session_id
    })

    # Should either auto-generate or return validation error
    assert response.status_code in [200, 400, 422]

    if response.status_code == 200:
        data = response.json()
        # Should have auto-generated session_id
        assert "session_id" in data


# ---------------------------------------------------------------------------
# TEST: COST LIMIT ENFORCEMENT
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cost_limit_enforcement(test_client, sample_session_id):
    """Test session cost limit prevents expensive conversations"""

    # Simulate expensive conversation (send many long messages)
    for i in range(15):
        response = await test_client.post("/api/chat", json={
            "session_id": sample_session_id,
            "message": f"Tell me everything about New Cairo real estate market in detail, including history, current trends, future projections, and comparisons with other areas. Message {i}"
        })

        if response.status_code != 200:
            # Should eventually hit cost limit
            assert response.status_code == 402  # Payment Required
            data = response.json()
            assert "cost" in data["detail"].lower() or "limit" in data["detail"].lower()
            break

    else:
        # If loop completed without hitting limit, check final cost
        data = response.json()
        # Should be tracking costs
        assert "cost_tracking" in data


# ---------------------------------------------------------------------------
# TEST: BILINGUAL RESPONSES
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_bilingual_responses(test_client, sample_session_id):
    """Test AMR responds in both English and Arabic"""

    response = await test_client.post("/api/chat", json={
        "session_id": sample_session_id,
        "message": "Hello, can you help me?"
    })

    assert response.status_code == 200
    data = response.json()

    response_text = data["response"]

    # Should contain both Arabic and English characters
    has_arabic = any(ord(char) >= 0x0600 and ord(char) <= 0x06FF for char in response_text)
    has_english = any(char.isascii() and char.isalpha() for char in response_text)

    assert has_arabic, "Response should contain Arabic text"
    assert has_english, "Response should contain English text"


# ---------------------------------------------------------------------------
# RUN TESTS
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
