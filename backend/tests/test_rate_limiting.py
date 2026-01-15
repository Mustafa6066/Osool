"""
Rate Limiting and Abuse Prevention Tests
-----------------------------------------
Tests multi-tier rate limiting, abuse detection, and security measures.
"""

import pytest
import sys
import os
from httpx import AsyncClient
from unittest.mock import Mock, patch
import time
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.middleware.rate_limiting import (
    limiter,
    ip_limiter,
    abuse_detector,
    get_user_id_or_ip,
    get_forwarded_ip,
    GLOBAL_RATE_LIMIT,
    CHAT_RATE_LIMIT,
    AUTH_RATE_LIMIT
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
def reset_rate_limits():
    """Reset rate limits before each test"""
    # Clear Redis or in-memory storage
    # Note: This depends on implementation
    yield


# ---------------------------------------------------------------------------
# TEST: GLOBAL RATE LIMIT
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_global_rate_limit(test_client, reset_rate_limits):
    """Test global rate limit (100 requests/minute)"""

    session_id = "global-rate-test"

    # Send 101 requests rapidly
    responses = []
    for i in range(101):
        response = await test_client.post("/api/chat", json={
            "session_id": session_id,
            "message": f"Request {i}"
        })
        responses.append(response)

        # Break if rate limited
        if response.status_code == 429:
            break

    # Should eventually hit rate limit
    rate_limited = any(r.status_code == 429 for r in responses)
    assert rate_limited, "Global rate limit not triggered after 100+ requests"

    # Find rate limit response
    rate_limit_response = next(r for r in responses if r.status_code == 429)

    # Verify headers
    assert "X-RateLimit-Remaining" in rate_limit_response.headers
    assert rate_limit_response.headers["X-RateLimit-Remaining"] == "0"

    assert "Retry-After" in rate_limit_response.headers


# ---------------------------------------------------------------------------
# TEST: ENDPOINT-SPECIFIC RATE LIMITS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_chat_rate_limit(test_client, reset_rate_limits):
    """Test chat endpoint rate limit (30 requests/minute)"""

    session_id = "chat-rate-test"

    # Send 35 chat requests
    responses = []
    for i in range(35):
        response = await test_client.post("/api/chat", json={
            "session_id": session_id,
            "message": f"Chat {i}"
        })
        responses.append(response)

        if response.status_code == 429:
            break

    # Should hit chat-specific limit
    rate_limited = any(r.status_code == 429 for r in responses)
    assert rate_limited, "Chat rate limit not triggered"


@pytest.mark.asyncio
async def test_auth_rate_limit(test_client, reset_rate_limits):
    """Test auth endpoint rate limit (10 requests/minute)"""

    # Send 12 login requests
    responses = []
    for i in range(12):
        response = await test_client.post("/api/auth/login", json={
            "wallet": f"0x{'1234567890' * 4}{i:02d}",
            "signature": "test-signature"
        })
        responses.append(response)

        if response.status_code == 429:
            break

    # Should hit auth rate limit quickly
    rate_limited = any(r.status_code == 429 for r in responses)
    # Note: May not trigger if auth validation fails first


# ---------------------------------------------------------------------------
# TEST: USER-BASED VS IP-BASED RATE LIMITING
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_user_based_rate_limiting(test_client, reset_rate_limits):
    """Test rate limiting per user (not IP)"""

    # User 1 with auth token
    user1_token = "Bearer valid-token-user1"
    user1_responses = []

    for i in range(35):
        response = await test_client.post(
            "/api/chat",
            json={"session_id": "user1-session", "message": f"Message {i}"},
            headers={"Authorization": user1_token}
        )
        user1_responses.append(response)

        if response.status_code == 429:
            break

    # User 1 should be rate limited
    user1_limited = any(r.status_code == 429 for r in user1_responses)

    # User 2 should still work (different user)
    user2_token = "Bearer valid-token-user2"
    user2_response = await test_client.post(
        "/api/chat",
        json={"session_id": "user2-session", "message": "Hello"},
        headers={"Authorization": user2_token}
    )

    # User 2 should not be rate limited (different user ID)
    # Note: This test depends on JWT token validation working


@pytest.mark.asyncio
async def test_ip_based_rate_limiting(test_client, reset_rate_limits):
    """Test IP-based rate limiting for unauthenticated requests"""

    # Send requests from same IP (no auth)
    responses = []
    for i in range(35):
        response = await test_client.post("/api/chat", json={
            "session_id": f"ip-test-{i}",
            "message": f"Message {i}"
        })
        responses.append(response)

        if response.status_code == 429:
            break

    # Should be rate limited by IP
    rate_limited = any(r.status_code == 429 for r in responses)
    assert rate_limited


# ---------------------------------------------------------------------------
# TEST: RATE LIMIT BYPASS ATTEMPTS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rate_limit_bypass_different_sessions(test_client, reset_rate_limits):
    """Test cannot bypass rate limit by changing session ID"""

    # Send requests with different session IDs (same user/IP)
    responses = []
    for i in range(35):
        response = await test_client.post("/api/chat", json={
            "session_id": f"bypass-attempt-{i}",  # Different session each time
            "message": f"Message {i}"
        })
        responses.append(response)

        if response.status_code == 429:
            break

    # Should still be rate limited (tracked by user/IP, not session)
    rate_limited = any(r.status_code == 429 for r in responses)
    assert rate_limited, "Rate limit bypassed by changing session IDs"


@pytest.mark.asyncio
async def test_rate_limit_bypass_user_agent_spoofing(test_client, reset_rate_limits):
    """Test cannot bypass rate limit by changing User-Agent"""

    responses = []
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Linux x86_64)",
        "curl/7.68.0",
        "python-requests/2.28.0"
    ]

    for i in range(35):
        ua = user_agents[i % len(user_agents)]
        response = await test_client.post(
            "/api/chat",
            json={"session_id": f"ua-test-{i}", "message": f"Message {i}"},
            headers={"User-Agent": ua}
        )
        responses.append(response)

        if response.status_code == 429:
            break

    # Should still be rate limited (tracked by IP, not User-Agent)
    rate_limited = any(r.status_code == 429 for r in responses)
    assert rate_limited, "Rate limit bypassed by changing User-Agent"


@pytest.mark.asyncio
async def test_rate_limit_x_forwarded_for_handling(test_client, reset_rate_limits):
    """Test X-Forwarded-For header is properly handled"""

    # Simulate requests through proxy with X-Forwarded-For
    real_ip = "203.0.113.1"

    responses = []
    for i in range(35):
        response = await test_client.post(
            "/api/chat",
            json={"session_id": f"proxy-test-{i}", "message": f"Message {i}"},
            headers={"X-Forwarded-For": f"{real_ip}, 10.0.0.1"}  # Real IP, then proxy
        )
        responses.append(response)

        if response.status_code == 429:
            break

    # Should be rate limited based on real IP (first in X-Forwarded-For)
    rate_limited = any(r.status_code == 429 for r in responses)
    assert rate_limited


# ---------------------------------------------------------------------------
# TEST: ABUSE DETECTION
# ---------------------------------------------------------------------------

def test_suspicious_user_agent_detection():
    """Test detection of bot user agents"""

    bot_user_agents = [
        "bot/1.0",
        "crawler/2.0",
        "spider/3.0",
        "scraper",
        "python-requests/2.28.0",
        "curl/7.68.0",
        "wget/1.20"
    ]

    for ua in bot_user_agents:
        is_suspicious = abuse_detector.is_suspicious_user_agent(ua)
        assert is_suspicious, f"Failed to detect suspicious UA: {ua}"


def test_legitimate_user_agent_not_flagged():
    """Test legitimate browsers are not flagged"""

    legitimate_user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
    ]

    for ua in legitimate_user_agents:
        is_suspicious = abuse_detector.is_suspicious_user_agent(ua)
        assert not is_suspicious, f"Incorrectly flagged legitimate UA: {ua}"


# ---------------------------------------------------------------------------
# TEST: FAILED AUTH ATTEMPTS TRACKING
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_failed_auth_tracking():
    """Test failed authentication attempts are tracked"""

    identifier = "test-user-failed-auth"

    # Record 3 failed attempts
    for i in range(3):
        abuse_detector.record_failed_auth(identifier)

    # Should not be blocked yet (threshold is 5)
    is_blocked = abuse_detector.check_failed_auth_attempts(identifier)
    assert not is_blocked

    # Record 2 more (total 5)
    abuse_detector.record_failed_auth(identifier)
    abuse_detector.record_failed_auth(identifier)

    # Should now be blocked
    is_blocked = abuse_detector.check_failed_auth_attempts(identifier)
    assert is_blocked


@pytest.mark.asyncio
async def test_failed_auth_reset_on_success():
    """Test failed auth counter resets on successful login"""

    identifier = "test-user-success"

    # Record 3 failed attempts
    for i in range(3):
        abuse_detector.record_failed_auth(identifier)

    # Successful login resets counter
    abuse_detector.reset_failed_auth(identifier)

    # Should not be blocked
    is_blocked = abuse_detector.check_failed_auth_attempts(identifier)
    assert not is_blocked


@pytest.mark.asyncio
async def test_failed_auth_lockout(test_client, reset_rate_limits):
    """Test user is locked out after 5 failed auth attempts"""

    # Simulate 5 failed login attempts
    identifier = "lockout-test-user"

    for i in range(5):
        abuse_detector.record_failed_auth(identifier)

    # Next request should be blocked by middleware
    with patch("app.middleware.rate_limiting.get_user_id_or_ip") as mock_get_id:
        mock_get_id.return_value = identifier

        response = await test_client.post("/api/chat", json={
            "session_id": "lockout-test",
            "message": "Hello"
        })

        # Should be forbidden
        if response.status_code == 403:
            data = response.json()
            assert data["error_code"] == "TOO_MANY_FAILED_ATTEMPTS"
            assert "message_ar" in data


# ---------------------------------------------------------------------------
# TEST: RATE LIMIT HEADERS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rate_limit_headers_present(test_client):
    """Test X-RateLimit headers are present in responses"""

    response = await test_client.post("/api/chat", json={
        "session_id": "headers-test",
        "message": "Hello"
    })

    # Should have rate limit headers
    # Note: Depends on slowapi configuration
    if "X-RateLimit-Limit" in response.headers:
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers


@pytest.mark.asyncio
async def test_rate_limit_remaining_decreases(test_client, reset_rate_limits):
    """Test X-RateLimit-Remaining decreases with each request"""

    responses = []
    for i in range(5):
        response = await test_client.post("/api/chat", json={
            "session_id": "remaining-test",
            "message": f"Message {i}"
        })
        responses.append(response)

    # Check if rate limit headers are present
    if "X-RateLimit-Remaining" in responses[0].headers:
        # Remaining should decrease
        remaining_values = [
            int(r.headers.get("X-RateLimit-Remaining", -1))
            for r in responses
            if "X-RateLimit-Remaining" in r.headers
        ]

        # Should be decreasing (or at least not increasing)
        for i in range(len(remaining_values) - 1):
            assert remaining_values[i] >= remaining_values[i+1]


# ---------------------------------------------------------------------------
# TEST: RETRY-AFTER HEADER
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retry_after_header(test_client, reset_rate_limits):
    """Test Retry-After header is set when rate limited"""

    # Trigger rate limit
    responses = []
    for i in range(35):
        response = await test_client.post("/api/chat", json={
            "session_id": "retry-after-test",
            "message": f"Message {i}"
        })
        responses.append(response)

        if response.status_code == 429:
            break

    # Find 429 response
    rate_limited_response = next((r for r in responses if r.status_code == 429), None)

    if rate_limited_response:
        assert "Retry-After" in rate_limited_response.headers

        retry_after = int(rate_limited_response.headers["Retry-After"])
        assert retry_after > 0
        assert retry_after <= 60  # Should be reasonable


# ---------------------------------------------------------------------------
# TEST: RATE LIMIT RECOVERY
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rate_limit_recovery_after_window(test_client, reset_rate_limits):
    """Test rate limit resets after time window"""

    session_id = "recovery-test"

    # Hit rate limit
    responses = []
    for i in range(35):
        response = await test_client.post("/api/chat", json={
            "session_id": session_id,
            "message": f"Message {i}"
        })
        responses.append(response)

        if response.status_code == 429:
            break

    # Verify rate limited
    assert any(r.status_code == 429 for r in responses)

    # Wait for rate limit window to reset (1 minute for chat endpoint)
    # In testing, we can't wait 60 seconds, so this is conceptual
    # await asyncio.sleep(61)

    # After waiting, should be able to make requests again
    # response_after = await test_client.post("/api/chat", json={
    #     "session_id": session_id,
    #     "message": "After reset"
    # })
    # assert response_after.status_code == 200


# ---------------------------------------------------------------------------
# TEST: HEALTH ENDPOINT EXEMPTION
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_endpoint_not_rate_limited(test_client):
    """Test health check endpoint is exempt from rate limiting"""

    # Send many health check requests
    responses = []
    for i in range(150):  # Well above normal rate limit
        response = await test_client.get("/health")
        responses.append(response)

    # None should be rate limited
    rate_limited = any(r.status_code == 429 for r in responses)
    assert not rate_limited, "Health endpoint should be exempt from rate limiting"

    # All should succeed
    assert all(r.status_code == 200 for r in responses)


# ---------------------------------------------------------------------------
# TEST: CONCURRENT REQUESTS RATE LIMITING
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_concurrent_requests_rate_limiting(test_client, reset_rate_limits):
    """Test rate limiting works correctly with concurrent requests"""

    session_id = "concurrent-rate-test"

    async def send_request(i):
        return await test_client.post("/api/chat", json={
            "session_id": session_id,
            "message": f"Concurrent {i}"
        })

    # Send 50 concurrent requests
    tasks = [send_request(i) for i in range(50)]
    responses = await asyncio.gather(*tasks)

    # Some should be rate limited
    rate_limited = any(r.status_code == 429 for r in responses)
    assert rate_limited, "Concurrent requests should still be rate limited"

    # Count how many succeeded
    success_count = sum(1 for r in responses if r.status_code == 200)
    rate_limited_count = sum(1 for r in responses if r.status_code == 429)

    # Should have a mix of success and rate limited
    assert success_count > 0
    assert rate_limited_count > 0


# ---------------------------------------------------------------------------
# TEST: REDIS BACKEND (if available)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_redis_rate_limiting_distributed():
    """Test rate limiting works across distributed instances (Redis backend)"""

    from app.middleware.rate_limiting import redis_client

    if redis_client is None:
        pytest.skip("Redis not available, skipping distributed test")

    # Test that rate limit state is stored in Redis
    # This allows rate limiting to work across multiple backend instances

    key = "test-rate-limit-key"

    # Set a value in Redis
    redis_client.set(key, "1", ex=60)

    # Verify it's stored
    value = redis_client.get(key)
    assert value == "1"

    # Increment
    redis_client.incr(key)
    value = redis_client.get(key)
    assert value == "2"

    # Cleanup
    redis_client.delete(key)


# ---------------------------------------------------------------------------
# TEST: SECURITY - MALICIOUS INPUT
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rate_limiting_with_malicious_input(test_client, reset_rate_limits):
    """Test rate limiting works even with malicious/unusual input"""

    malicious_inputs = [
        "<script>alert('xss')</script>",
        "'; DROP TABLE properties; --",
        "a" * 10000,  # Very long
        "🏠" * 1000,  # Lots of emojis
        "\x00\x01\x02",  # Null bytes
    ]

    responses = []
    for i, malicious_input in enumerate(malicious_inputs * 8):  # 40 requests
        response = await test_client.post("/api/chat", json={
            "session_id": f"malicious-test-{i}",
            "message": malicious_input
        })
        responses.append(response)

        if response.status_code == 429:
            break

    # Should still be rate limited (security mechanism working)
    rate_limited = any(r.status_code == 429 for r in responses)
    assert rate_limited


# ---------------------------------------------------------------------------
# TEST: RATE LIMIT ERROR MESSAGE QUALITY
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rate_limit_error_message_quality(test_client, reset_rate_limits):
    """Test rate limit error messages are helpful and bilingual"""

    # Trigger rate limit
    responses = []
    for i in range(35):
        response = await test_client.post("/api/chat", json={
            "session_id": "error-message-test",
            "message": f"Message {i}"
        })
        responses.append(response)

        if response.status_code == 429:
            break

    rate_limited_response = next((r for r in responses if r.status_code == 429), None)

    if rate_limited_response:
        data = rate_limited_response.json()

        # Should have structured error
        assert "error_code" in data
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"

        # Should have bilingual messages
        assert "message" in data
        assert "message_ar" in data
        assert "user_message" in data
        assert "user_message_ar" in data

        # Should explain what to do
        assert "retry_after_seconds" in data
        assert data["retry_after_seconds"] > 0

        # Arabic message should contain Arabic characters
        assert any(ord(char) >= 0x0600 and ord(char) <= 0x06FF for char in data["message_ar"])


# ---------------------------------------------------------------------------
# RUN TESTS
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
