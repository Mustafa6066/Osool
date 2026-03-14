"""
Osool Backend — Cache Service Tests
-------------------------------------
Tests for RedisClient with memory fallback (F2 fix).
Covers: initialization, TTL, eviction, session helpers.
"""

import time
import pytest
from unittest.mock import patch, MagicMock


class TestRedisClientInitialization:
    """Test F2: _memory_fallback is always initialized."""

    def test_memory_fallback_exists_when_redis_connects(self):
        """F2: _memory_fallback must exist even when Redis connects successfully."""
        with patch("app.services.cache.redis") as mock_redis:
            mock_client = MagicMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.ping.return_value = True

            from app.services.cache import RedisClient
            client = RedisClient()

            assert hasattr(client, "_memory_fallback")
            assert isinstance(client._memory_fallback, dict)
            assert client.redis is not None

    def test_memory_fallback_exists_when_redis_fails(self):
        """F2: _memory_fallback must exist when Redis connection fails."""
        with patch("app.services.cache.redis") as mock_redis:
            mock_redis.from_url.side_effect = Exception("Connection refused")

            from app.services.cache import RedisClient
            client = RedisClient()

            assert hasattr(client, "_memory_fallback")
            assert isinstance(client._memory_fallback, dict)
            assert client.redis is None

    def test_redis_none_after_connection_failure(self):
        """After Redis failure, self.redis should be None."""
        with patch("app.services.cache.redis") as mock_redis:
            mock_redis.from_url.return_value = MagicMock()
            mock_redis.from_url.return_value.ping.side_effect = Exception("Timeout")

            from app.services.cache import RedisClient
            client = RedisClient()

            assert client.redis is None


class TestMemoryFallbackOperations:
    """Test in-memory cache operations (when Redis is unavailable)."""

    @pytest.fixture
    def cache_client(self):
        """Create a RedisClient with Redis deliberately unavailable."""
        with patch("app.services.cache.redis") as mock_redis:
            mock_redis.from_url.side_effect = Exception("No Redis")
            from app.services.cache import RedisClient
            client = RedisClient()
            return client

    def test_set_and_get_json(self, cache_client):
        """Test basic set/get with memory fallback."""
        cache_client.set_json("key1", {"name": "test"}, ttl=60)
        result = cache_client.get_json("key1")

        assert result == {"name": "test"}

    def test_get_nonexistent_key_returns_none(self, cache_client):
        """Test getting a key that doesn't exist."""
        result = cache_client.get_json("nonexistent")
        assert result is None

    def test_ttl_expiration(self, cache_client):
        """Test that entries expire after TTL."""
        cache_client.set_json("expiring", {"data": "temp"}, ttl=1)

        # Should exist immediately
        assert cache_client.get_json("expiring") is not None

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache_client.get_json("expiring") is None

    def test_overwrite_existing_key(self, cache_client):
        """Test overwriting a key with new value."""
        cache_client.set_json("key", {"v": 1})
        cache_client.set_json("key", {"v": 2})

        result = cache_client.get_json("key")
        assert result == {"v": 2}

    def test_multiple_keys(self, cache_client):
        """Test storing and retrieving multiple keys."""
        cache_client.set_json("a", {"val": 1})
        cache_client.set_json("b", {"val": 2})
        cache_client.set_json("c", {"val": 3})

        assert cache_client.get_json("a") == {"val": 1}
        assert cache_client.get_json("b") == {"val": 2}
        assert cache_client.get_json("c") == {"val": 3}


class TestCacheEviction:
    """Test memory fallback eviction when over capacity."""

    def test_evicts_oldest_when_over_limit(self):
        """Test that old entries are evicted when exceeding MAX_ENTRIES."""
        with patch("app.services.cache.redis") as mock_redis:
            mock_redis.from_url.side_effect = Exception("No Redis")
            with patch("app.services.cache._MAX_MEMORY_ENTRIES", 10):
                from app.services.cache import RedisClient
                client = RedisClient()

                # Add 12 entries (over the limit of 10)
                for i in range(12):
                    client.set_json(f"key_{i}", {"v": i}, ttl=3600)

                # Eviction should have been triggered
                assert len(client._memory_fallback) <= 10


class TestCacheSessionHelpers:
    """Test session-specific cache helpers."""

    @pytest.fixture
    def cache_client(self):
        with patch("app.services.cache.redis") as mock_redis:
            mock_redis.from_url.side_effect = Exception("No Redis")
            from app.services.cache import RedisClient
            return RedisClient()

    def test_store_and_get_session_results(self, cache_client):
        """Test storing and retrieving search results."""
        results = [{"id": 1, "title": "Villa"}, {"id": 2, "title": "Apartment"}]
        cache_client.store_session_results("sess123", results)

        retrieved = cache_client.get_session_results("sess123")
        assert len(retrieved) == 2
        assert retrieved[0]["title"] == "Villa"

    def test_get_empty_session_results(self, cache_client):
        """Test getting results for non-existent session."""
        result = cache_client.get_session_results("nonexistent")
        assert result == []

    def test_set_and_get_lead_score(self, cache_client):
        """Test lead scoring cache."""
        cache_client.set_lead_score("sess123", 85)
        score = cache_client.get_lead_score("sess123")
        assert score == 85

    def test_get_lead_score_nonexistent(self, cache_client):
        """Test lead score for non-existent session."""
        score = cache_client.get_lead_score("nonexistent")
        assert score is None


class TestCacheRedisMode:
    """Test cache operations when Redis IS connected."""

    def test_set_json_calls_redis_setex(self):
        """When Redis is connected, set_json should call redis.setex."""
        with patch("app.services.cache.redis") as mock_redis:
            mock_client = MagicMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.ping.return_value = True

            from app.services.cache import RedisClient
            client = RedisClient()
            client.set_json("key", {"v": 1}, ttl=300)

            mock_client.setex.assert_called_once()

    def test_get_json_calls_redis_get(self):
        """When Redis is connected, get_json should call redis.get."""
        with patch("app.services.cache.redis") as mock_redis:
            mock_client = MagicMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.ping.return_value = True
            mock_client.get.return_value = '{"v": 1}'

            from app.services.cache import RedisClient
            client = RedisClient()
            result = client.get_json("key")

            assert result == {"v": 1}
            mock_client.get.assert_called_once_with("key")

    def test_get_json_returns_none_when_key_missing(self):
        """Redis returns None for missing key → get_json returns None."""
        with patch("app.services.cache.redis") as mock_redis:
            mock_client = MagicMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.ping.return_value = True
            mock_client.get.return_value = None

            from app.services.cache import RedisClient
            client = RedisClient()
            result = client.get_json("missing")

            assert result is None

    def test_redis_exception_during_get_returns_none(self):
        """If Redis raises during get, return None gracefully."""
        with patch("app.services.cache.redis") as mock_redis:
            mock_client = MagicMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.ping.return_value = True
            mock_client.get.side_effect = Exception("Redis down")

            from app.services.cache import RedisClient
            client = RedisClient()
            result = client.get_json("key")

            assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
