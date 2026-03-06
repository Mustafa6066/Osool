import os
import time
import redis
import json
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Max entries in memory fallback before eviction
_MAX_MEMORY_ENTRIES = 500


class RedisClient:
    def __init__(self):
        self._memory_fallback: dict = {}  # {key: {"value": ..., "expires_at": float}}
        try:
            self.redis = redis.from_url(REDIS_URL, decode_responses=True)
            self.redis.ping()
            print("✅ [Cache] Redis Connected")
        except Exception as e:
            print(f"⚠️ [Cache] Redis Connection Failed: {e}. using Memory Fallback.")
            self.redis = None

    def set_json(self, key: str, value: dict, ttl: int = 3600):
        """Stores a dict as JSON string with TTL."""
        try:
            if self.redis:
                self.redis.setex(key, ttl, json.dumps(value))
            else:
                # Memory fallback WITH TTL + eviction
                self._memory_fallback[key] = {
                    "value": value,
                    "expires_at": time.time() + ttl,
                }
                # Evict oldest entries if over limit
                if len(self._memory_fallback) > _MAX_MEMORY_ENTRIES:
                    self._evict_expired()
        except Exception as e:
            print(f"❌ Redis Set Error: {e}")

    def get_json(self, key: str) -> dict:
        """Retrieves and parses JSON string."""
        try:
            if self.redis:
                data = self.redis.get(key)
                return json.loads(data) if data else None
            else:
                entry = self._memory_fallback.get(key)
                if not entry:
                    return None
                # Check TTL expiration
                if entry.get("expires_at", 0) < time.time():
                    del self._memory_fallback[key]
                    return None
                return entry.get("value")
        except Exception as e:
            print(f"❌ Redis Get Error: {e}")
            return None

    def _evict_expired(self):
        """Remove expired entries + oldest entries if still over limit."""
        now = time.time()
        # Remove expired
        expired_keys = [
            k for k, v in self._memory_fallback.items()
            if v.get("expires_at", 0) < now
        ]
        for k in expired_keys:
            del self._memory_fallback[k]

        # If still over limit, remove oldest half
        if len(self._memory_fallback) > _MAX_MEMORY_ENTRIES:
            sorted_keys = sorted(
                self._memory_fallback.keys(),
                key=lambda k: self._memory_fallback[k].get("expires_at", 0)
            )
            for k in sorted_keys[:len(sorted_keys) // 2]:
                del self._memory_fallback[k]

    def store_session_results(self, session_id: str, results: list):
        """Specific helper for Agent Search Results."""
        key = f"search:{session_id}"
        results_dict = {"results": results}
        self.set_json(key, results_dict, ttl=3600)

    def get_session_results(self, session_id: str) -> list:
        """Specific helper for Agent Search Results."""
        key = f"search:{session_id}"
        data = self.get_json(key)
        return data.get("results", []) if data else []

    def set_lead_score(self, session_id: str, score: int, ttl: int = 3600):
        """Stores lead score for session."""
        key = f"score:{session_id}"
        self.set_json(key, {"score": score}, ttl=ttl)

    def get_lead_score(self, session_id: str) -> int:
        """Retrieves lead score for session."""
        key = f"score:{session_id}"
        data = self.get_json(key)
        return data.get("score") if data else None

    def set(self, key: str, value, ttl: int = 3600):
        """Generic set — wraps any value in a dict for set_json compatibility."""
        self.set_json(key, {"_v": value}, ttl=ttl)

    def get(self, key: str):
        """Generic get — unwraps value stored by set()."""
        data = self.get_json(key)
        if data is None:
            return None
        # Support both wrapped (_v) and direct dict values
        return data.get("_v", data)

    def delete(self, key: str):
        """Delete a key from cache."""
        try:
            if self.redis:
                self.redis.delete(key)
            else:
                self._memory_fallback.pop(key, None)
        except Exception as e:
            print(f"❌ Redis Delete Error: {e}")


# Singleton
cache = RedisClient()
