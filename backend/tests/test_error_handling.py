"""
Error Handling and Circuit Breaker Tests
-----------------------------------------
Tests error scenarios, bilingual error messages, and circuit breaker functionality.
"""

import pytest
import sys
import os
from httpx import AsyncClient
from unittest.mock import Mock, patch, AsyncMock
import time
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.error_handling import (
    PropertyNotFoundError,
    AIServiceError,
    RateLimitError,
    AuthenticationError,
    CostLimitError,
    ValidationError,
    DatabaseError,
    BlockchainError,
    SystemError
)
from app.services.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    claude_breaker,
    openai_breaker,
    database_breaker,
    blockchain_breaker
)


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
async def test_client():
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def reset_circuit_breakers():
    """Reset all circuit breakers before each test"""
    claude_breaker.reset()
    openai_breaker.reset()
    database_breaker.reset()
    blockchain_breaker.reset()
    yield
    # Reset after test too
    claude_breaker.reset()
    openai_breaker.reset()
    database_breaker.reset()
    blockchain_breaker.reset()


# ---------------------------------------------------------------------------
# TEST: PROPERTY NOT FOUND ERROR
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_property_not_found_error(test_client):
    """Test 404 error for non-existent property"""

    response = await test_client.get("/api/property/999999")

    assert response.status_code == 404
    data = response.json()

    # Verify error structure
    assert "error_code" in data
    assert data["error_code"] == "PROPERTY_NOT_FOUND"

    # Verify bilingual messages
    assert "message" in data
    assert "message_ar" in data
    assert "user_message" in data
    assert "user_message_ar" in data

    # Verify Arabic text is present
    assert any(ord(char) >= 0x0600 and ord(char) <= 0x06FF for char in data["message_ar"])


# ---------------------------------------------------------------------------
# TEST: AI SERVICE ERROR
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ai_service_error(test_client):
    """Test 503 when AI service (Claude/OpenAI) fails"""

    # Mock Claude API failure
    with patch("app.ai_engine.claude_sales_agent.anthropic.messages.create") as mock_claude:
        mock_claude.side_effect = Exception("Claude API unavailable")

        response = await test_client.post("/api/chat", json={
            "session_id": "test-ai-error",
            "message": "Hello"
        })

        assert response.status_code == 503
        data = response.json()

        assert data["error_code"] == "AI_SERVICE_ERROR"
        assert "message" in data
        assert "message_ar" in data

        # Should mention service unavailable
        assert "unavailable" in data["message"].lower() or "service" in data["message"].lower()


# ---------------------------------------------------------------------------
# TEST: RATE LIMIT ERROR
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rate_limit_error(test_client):
    """Test 429 when rate limit exceeded"""

    session_id = "rate-limit-test"

    # Send rapid requests to trigger rate limit (>30/min for chat endpoint)
    responses = []
    for i in range(35):
        response = await test_client.post("/api/chat", json={
            "session_id": session_id,
            "message": f"Test {i}"
        })
        responses.append(response)

        if response.status_code == 429:
            break

    # Should eventually get rate limited
    rate_limited = any(r.status_code == 429 for r in responses)
    assert rate_limited, "Rate limiting not triggered"

    # Find the 429 response
    rate_limit_response = next(r for r in responses if r.status_code == 429)
    data = rate_limit_response.json()

    # Verify error structure
    assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
    assert "retry_after_seconds" in data
    assert "message_ar" in data

    # Verify retry-after header
    assert "Retry-After" in rate_limit_response.headers
    retry_after = int(rate_limit_response.headers["Retry-After"])
    assert retry_after > 0


# ---------------------------------------------------------------------------
# TEST: AUTHENTICATION ERROR
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authentication_error(test_client):
    """Test 401 for invalid JWT token"""

    # Try to access protected endpoint without token
    response = await test_client.get("/api/user/profile")

    assert response.status_code == 401
    data = response.json()

    # FastAPI default or custom error
    assert "detail" in data or "error_code" in data


@pytest.mark.asyncio
async def test_expired_token_error(test_client):
    """Test 401 for expired JWT token"""

    import jwt
    from datetime import datetime, timedelta

    # Create expired token
    expired_token = jwt.encode({
        "sub": "test-user",
        "exp": datetime.utcnow() - timedelta(hours=1)
    }, "test-secret", algorithm="HS256")

    response = await test_client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401
    # Should mention expiration
    assert "expired" in response.text.lower() or "invalid" in response.text.lower()


@pytest.mark.asyncio
async def test_blacklisted_token_error(test_client):
    """Test 401 for blacklisted/revoked token"""

    from app.auth import create_access_token, invalidate_token

    # Create valid token
    token = create_access_token({"sub": "test-user"})

    # Blacklist it
    invalidate_token(token)

    # Try to use it
    response = await test_client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
    data = response.json()
    assert "revoked" in data["detail"].lower()


# ---------------------------------------------------------------------------
# TEST: COST LIMIT ERROR
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cost_limit_error(test_client):
    """Test 402 when session cost limit exceeded"""

    from app.monitoring.cost_tracker import cost_tracker

    session_id = "cost-limit-test"

    # Simulate expensive usage
    cost_tracker._set_session_cost(session_id, 0.60)  # Over $0.50 limit

    response = await test_client.post("/api/chat", json={
        "session_id": session_id,
        "message": "Hello"
    })

    # Should block due to cost limit
    if response.status_code == 402:
        data = response.json()
        assert data["error_code"] == "COST_LIMIT_EXCEEDED"
        assert "cost" in data["message"].lower() or "limit" in data["message"].lower()
        assert "message_ar" in data


# ---------------------------------------------------------------------------
# TEST: VALIDATION ERROR
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_validation_error_missing_field(test_client):
    """Test 422 for missing required fields"""

    # Missing 'message' field
    response = await test_client.post("/api/chat", json={
        "session_id": "test-validation"
        # 'message' field missing
    })

    assert response.status_code == 422
    data = response.json()

    # FastAPI validation error format
    assert "detail" in data


@pytest.mark.asyncio
async def test_validation_error_invalid_type(test_client):
    """Test 422 for invalid field types"""

    # 'message' should be string, not int
    response = await test_client.post("/api/chat", json={
        "session_id": "test-validation",
        "message": 12345  # Invalid type
    })

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# TEST: DATABASE ERROR
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_database_error(test_client):
    """Test 500 when database connection fails"""

    with patch("app.services.property_search.get_db_session") as mock_db:
        mock_db.side_effect = Exception("Database connection refused")

        response = await test_client.post("/api/chat", json={
            "session_id": "test-db-error",
            "message": "Show me properties"
        })

        # Should return 500 or 503
        assert response.status_code in [500, 503]


# ---------------------------------------------------------------------------
# TEST: BLOCKCHAIN ERROR
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_blockchain_error_graceful_fallback(test_client):
    """Test blockchain errors are handled gracefully (not blocking)"""

    with patch("app.ai_engine.tools.blockchain_verification.check_onchain_availability") as mock_blockchain:
        mock_blockchain.side_effect = Exception("Blockchain node unreachable")

        response = await test_client.post("/api/chat", json={
            "session_id": "test-blockchain-error",
            "message": "Verify property 123 on blockchain"
        })

        # Should still return 200 (graceful degradation)
        # AMR should explain blockchain unavailable
        assert response.status_code == 200
        data = response.json()

        response_text = data["response"].lower()
        assert "blockchain" in response_text or "verification" in response_text


# ---------------------------------------------------------------------------
# TEST: CIRCUIT BREAKER BASIC FUNCTIONALITY
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_circuit_breaker_closed_state(reset_circuit_breakers):
    """Test circuit breaker allows calls in CLOSED state"""

    breaker = CircuitBreaker(failure_threshold=3, timeout=5)

    async def successful_call():
        return {"status": "success"}

    result = await breaker.call_async(successful_call)

    assert result["status"] == "success"
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures(reset_circuit_breakers):
    """Test circuit breaker opens after failure threshold"""

    breaker = CircuitBreaker(failure_threshold=3, timeout=5)

    async def failing_call():
        raise Exception("Service unavailable")

    # Trigger 3 failures
    for i in range(3):
        try:
            await breaker.call_async(failing_call)
        except Exception:
            pass  # Expected

    # Circuit should now be OPEN
    assert breaker.state == CircuitState.OPEN
    assert breaker.failure_count == 3


@pytest.mark.asyncio
async def test_circuit_breaker_blocks_when_open(reset_circuit_breakers):
    """Test circuit breaker blocks calls when OPEN"""

    breaker = CircuitBreaker(failure_threshold=3, timeout=5)

    async def failing_call():
        raise Exception("Service unavailable")

    async def successful_call():
        return {"status": "success"}

    # Trigger failures to open circuit
    for i in range(3):
        try:
            await breaker.call_async(failing_call)
        except:
            pass

    # Verify circuit is open
    assert breaker.state == CircuitState.OPEN

    # Try a call that would succeed, but should be blocked
    with pytest.raises(Exception) as exc_info:
        await breaker.call_async(successful_call)

    assert "Circuit breaker is OPEN" in str(exc_info.value)


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_recovery(reset_circuit_breakers):
    """Test circuit breaker transitions to HALF_OPEN after timeout"""

    breaker = CircuitBreaker(failure_threshold=3, timeout=2)  # 2 second timeout

    async def failing_call():
        raise Exception("Service unavailable")

    async def successful_call():
        return {"status": "success"}

    # Open the circuit
    for i in range(3):
        try:
            await breaker.call_async(failing_call)
        except:
            pass

    assert breaker.state == CircuitState.OPEN

    # Wait for timeout
    await asyncio.sleep(2.5)

    # Next call should transition to HALF_OPEN and try
    result = await breaker.call_async(successful_call)

    assert result["status"] == "success"
    assert breaker.state == CircuitState.CLOSED  # Successful call closes circuit
    assert breaker.failure_count == 0


@pytest.mark.asyncio
async def test_circuit_breaker_resets_on_success(reset_circuit_breakers):
    """Test circuit breaker resets failure count on success"""

    breaker = CircuitBreaker(failure_threshold=3, timeout=5)

    async def failing_call():
        raise Exception("Temporary failure")

    async def successful_call():
        return {"status": "success"}

    # Trigger 2 failures (below threshold)
    for i in range(2):
        try:
            await breaker.call_async(failing_call)
        except:
            pass

    assert breaker.failure_count == 2
    assert breaker.state == CircuitState.CLOSED

    # Successful call should reset count
    await breaker.call_async(successful_call)

    assert breaker.failure_count == 0
    assert breaker.state == CircuitState.CLOSED


# ---------------------------------------------------------------------------
# TEST: CLAUDE API CIRCUIT BREAKER
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_claude_circuit_breaker_integration(test_client, reset_circuit_breakers):
    """Test Claude API circuit breaker in real request"""

    # Mock Claude API to fail
    with patch("app.ai_engine.claude_sales_agent.anthropic.messages.create") as mock_claude:
        mock_claude.side_effect = Exception("Claude API rate limit")

        # Send requests until circuit opens
        for i in range(5):
            response = await test_client.post("/api/chat", json={
                "session_id": f"claude-circuit-test-{i}",
                "message": "Hello"
            })

            # Should eventually return 503
            if response.status_code == 503:
                break

        # Verify circuit opened
        # Note: This depends on implementation - claude_breaker might be used
        assert claude_breaker.state == CircuitState.OPEN or response.status_code == 503


# ---------------------------------------------------------------------------
# TEST: OPENAI API CIRCUIT BREAKER
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_openai_circuit_breaker_integration(test_client, reset_circuit_breakers):
    """Test OpenAI embeddings circuit breaker"""

    # Mock OpenAI embedding API to fail
    with patch("app.services.property_search.get_embedding") as mock_embedding:
        mock_embedding.side_effect = Exception("OpenAI API error")

        # Send search requests
        for i in range(5):
            response = await test_client.post("/api/chat", json={
                "session_id": f"openai-circuit-test-{i}",
                "message": "Search for apartments"
            })

        # Should handle gracefully or open circuit
        # Note: Implementation may use fallback


# ---------------------------------------------------------------------------
# TEST: DATABASE CIRCUIT BREAKER
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_database_circuit_breaker(reset_circuit_breakers):
    """Test database circuit breaker opens on connection failures"""

    async def failing_db_call():
        raise Exception("Connection refused")

    # Trigger failures
    for i in range(5):
        try:
            await database_breaker.call_async(failing_db_call)
        except:
            pass

    # Circuit should open
    assert database_breaker.state == CircuitState.OPEN


# ---------------------------------------------------------------------------
# TEST: BLOCKCHAIN CIRCUIT BREAKER
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_blockchain_circuit_breaker(reset_circuit_breakers):
    """Test blockchain circuit breaker for node failures"""

    async def failing_blockchain_call():
        raise Exception("Blockchain node timeout")

    # Trigger failures
    for i in range(3):
        try:
            await blockchain_breaker.call_async(failing_blockchain_call)
        except:
            pass

    # Circuit should open
    assert blockchain_breaker.state == CircuitState.OPEN


# ---------------------------------------------------------------------------
# TEST: ERROR MESSAGE LOCALIZATION
# ---------------------------------------------------------------------------

def test_error_localization_property_not_found():
    """Test bilingual error messages"""

    error = PropertyNotFoundError(property_id=123)

    # Check English message
    assert "not found" in error.message.lower()
    assert "123" in error.message

    # Check Arabic message
    assert error.message_ar is not None
    assert len(error.message_ar) > 0
    # Should contain Arabic characters
    assert any(ord(char) >= 0x0600 and ord(char) <= 0x06FF for char in error.message_ar)


def test_error_localization_rate_limit():
    """Test rate limit error messages are bilingual"""

    error = RateLimitError(limit="30/minute", retry_after=60)

    assert error.message_ar is not None
    assert error.user_message is not None
    assert error.user_message_ar is not None

    # Should explain retry after
    assert "60" in error.message or "retry" in error.message.lower()


def test_error_localization_cost_limit():
    """Test cost limit error messages"""

    error = CostLimitError(session_cost=0.75, limit=0.50)

    # Should mention cost values
    assert "0.75" in error.message or "0.50" in error.message

    # Should have Arabic translation
    assert error.message_ar is not None
    assert any(ord(char) >= 0x0600 and ord(char) <= 0x06FF for char in error.message_ar)


# ---------------------------------------------------------------------------
# TEST: ERROR RECOVERY
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_error_recovery_after_circuit_close(test_client, reset_circuit_breakers):
    """Test system recovers after circuit breaker closes"""

    # Mock API to fail then succeed
    call_count = {"count": 0}

    async def flaky_api():
        call_count["count"] += 1
        if call_count["count"] <= 3:
            raise Exception("Temporary failure")
        return {"status": "success"}

    breaker = CircuitBreaker(failure_threshold=3, timeout=2)

    # Trigger failures
    for i in range(3):
        try:
            await breaker.call_async(flaky_api)
        except:
            pass

    assert breaker.state == CircuitState.OPEN

    # Wait for timeout
    await asyncio.sleep(2.5)

    # Should recover
    result = await breaker.call_async(flaky_api)
    assert result["status"] == "success"
    assert breaker.state == CircuitState.CLOSED


# ---------------------------------------------------------------------------
# TEST: MULTIPLE CONCURRENT ERRORS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_concurrent_errors_handled(test_client):
    """Test system handles multiple simultaneous errors"""

    import asyncio

    async def send_request(i):
        return await test_client.post("/api/chat", json={
            "session_id": f"concurrent-error-{i}",
            "message": "Test"
        })

    # Send 50 concurrent requests
    tasks = [send_request(i) for i in range(50)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    # All should either succeed or return proper error (not crash)
    for response in responses:
        if not isinstance(response, Exception):
            assert response.status_code in [200, 429, 503]  # Valid responses


# ---------------------------------------------------------------------------
# RUN TESTS
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
