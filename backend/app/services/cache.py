import os
import redis
import json
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class RedisClient:
    def __init__(self):
        try:
            self.redis = redis.from_url(REDIS_URL, decode_responses=True)
            self.redis.ping()
            print("✅ [Cache] Redis Connected")
        except Exception as e:
            print(f"⚠️ [Cache] Redis Connection Failed: {e}. using Memory Fallback.")
            self.redis = None
            self._memory_fallback = {}

    def set_json(self, key: str, value: dict, ttl: int = 3600):
        """Stores a dict as JSON string with TTL."""
        try:
            if self.redis:
                self.redis.setex(key, ttl, json.dumps(value))
            else:
                self._memory_fallback[key] = value # No TTL in fallback
        except Exception as e:
            print(f"❌ Redis Set Error: {e}")

    def get_json(self, key: str) -> dict:
        """Retrieves and parses JSON string."""
        try:
            if self.redis:
                data = self.redis.get(key)
                return json.loads(data) if data else None
            else:
                return self._memory_fallback.get(key)
        except Exception as e:
            print(f"❌ Redis Get Error: {e}")
            return None

    def store_session_results(self, session_id: str, results: list):
        """Specific helper for Agent Search Results."""
        key = f"search:{session_id}"
        video = {"results": results}
        self.set_json(key, video, ttl=3600)

    def get_session_results(self, session_id: str) -> list:
        """Specific helper for Agent Search Results."""
        key = f"search:{session_id}"
        data = self.get_json(key)
        return data.get("results", []) if data else []

# Singleton
cache = RedisClient()
