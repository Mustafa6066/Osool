"""
Social Proof Service
-----------------------
Track anonymized activity for social proof signals.
Powered by Redis counters with 24h TTL.
"""

import time
import logging
from typing import Dict, Any

from app.services.cache import cache

logger = logging.getLogger(__name__)

# Thresholds for signal generation
_ANALYSIS_THRESHOLD = 3
_VIEW_THRESHOLD = 5
_AREA_ACTIVITY_THRESHOLD = 10


class SocialProofService:
    """Track and serve anonymized social proof signals."""

    PREFIX_PROP_VIEWS = "sp:views:"
    PREFIX_PROP_ANALYZES = "sp:analyzes:"
    PREFIX_AREA_ACTIVITY = "sp:area:"
    TTL_24H = 86400

    def _increment(self, key: str) -> None:
        """Increment a counter in Redis or memory fallback."""
        try:
            if cache.redis:
                cache.redis.incr(key)
                cache.redis.expire(key, self.TTL_24H)
            else:
                entry = cache._memory_fallback.get(key)
                current = entry.get("value", 0) if isinstance(entry, dict) else 0
                cache._memory_fallback[key] = {
                    "value": current + 1,
                    "expires_at": time.time() + self.TTL_24H,
                }
                # Periodically clean up expired entries to prevent memory leak
                if len(cache._memory_fallback) > 200:
                    self._cleanup_expired()
        except Exception as e:
            logger.warning("Social proof increment error for %s: %s", key, e)

    def _get_count(self, key: str) -> int:
        """Get a counter value from Redis or memory fallback."""
        try:
            if cache.redis:
                return int(cache.redis.get(key) or 0)
            else:
                entry = cache._memory_fallback.get(key)
                if not isinstance(entry, dict):
                    return 0
                if entry.get("expires_at", 0) < time.time():
                    # Expired — remove it
                    cache._memory_fallback.pop(key, None)
                    return 0
                return entry.get("value", 0)
        except Exception as e:
            logger.warning("Social proof get error for %s: %s", key, e)
            return 0

    def _cleanup_expired(self) -> None:
        """Remove expired entries from memory fallback."""
        now = time.time()
        expired = [k for k, v in cache._memory_fallback.items()
                   if isinstance(v, dict) and v.get("expires_at", 0) < now]
        for k in expired:
            del cache._memory_fallback[k]

    def track_property_view(self, property_id: int) -> None:
        self._increment(f"{self.PREFIX_PROP_VIEWS}{property_id}")

    def track_property_analysis(self, property_id: int) -> None:
        self._increment(f"{self.PREFIX_PROP_ANALYZES}{property_id}")

    def track_area_activity(self, area: str) -> None:
        self._increment(f"{self.PREFIX_AREA_ACTIVITY}{area}")

    def get_property_signals(self, property_id: int) -> Dict[str, Any]:
        """Get social proof signals for a property."""
        views = self._get_count(f"{self.PREFIX_PROP_VIEWS}{property_id}")
        analyzes = self._get_count(f"{self.PREFIX_PROP_ANALYZES}{property_id}")

        signals: Dict[str, Any] = {}
        if analyzes >= _ANALYSIS_THRESHOLD:
            signals["analysis_count"] = {
                "text_en": f"{analyzes} investors analyzed this property today",
                "text_ar": f"{analyzes} مستثمرين حللوا العقار ده النهاردة",
                "count": analyzes,
                "type": "hot",
            }
        elif views >= _VIEW_THRESHOLD:
            signals["view_count"] = {
                "text_en": f"{views} investors viewed this property today",
                "text_ar": f"{views} مستثمرين شافوا العقار ده النهاردة",
                "count": views,
                "type": "warm",
            }
        return signals

    def get_area_signals(self, area: str) -> Dict[str, Any]:
        """Get social proof signals for an area."""
        activity = self._get_count(f"{self.PREFIX_AREA_ACTIVITY}{area}")
        if activity >= _AREA_ACTIVITY_THRESHOLD:
            return {
                "area_activity": {
                    "text_en": f"{area} is trending — {activity} searches today",
                    "text_ar": f"{area} ترند — {activity} بحث النهاردة",
                    "count": activity,
                    "type": "trending",
                }
            }
        return {}


# Singleton
social_proof = SocialProofService()
