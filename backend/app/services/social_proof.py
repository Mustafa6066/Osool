"""
Social Proof Service
-----------------------
Track anonymized activity for social proof signals.
Powered by Redis counters with 24h TTL.

Signals:
- "5 investors analyzed this property today"
- "This property's Osool Score is in the top 10%"
- "3 saved searches match this property"
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.cache import cache

logger = logging.getLogger(__name__)


class SocialProofService:
    """Track and serve anonymized social proof signals."""

    # Redis key prefixes
    PREFIX_PROP_VIEWS = "sp:views:"       # Per property daily views
    PREFIX_PROP_ANALYZES = "sp:analyzes:"  # Per property daily analyses
    PREFIX_AREA_ACTIVITY = "sp:area:"      # Per area daily activity
    TTL_24H = 86400  # 24 hours

    def track_property_view(self, property_id: int):
        """Track a property view (non-blocking)."""
        try:
            key = f"{self.PREFIX_PROP_VIEWS}{property_id}"
            if cache.redis:
                cache.redis.incr(key)
                cache.redis.expire(key, self.TTL_24H)
            else:
                import time
                entry = cache._memory_fallback.get(key)
                current = entry.get("value", 0) if isinstance(entry, dict) else 0
                cache._memory_fallback[key] = {
                    "value": current + 1,
                    "expires_at": time.time() + self.TTL_24H,
                }
        except Exception as e:
            logger.debug(f"Social proof track error: {e}")

    def track_property_analysis(self, property_id: int):
        """Track an in-depth analysis of a property."""
        try:
            key = f"{self.PREFIX_PROP_ANALYZES}{property_id}"
            if cache.redis:
                cache.redis.incr(key)
                cache.redis.expire(key, self.TTL_24H)
            else:
                import time
                entry = cache._memory_fallback.get(key)
                current = entry.get("value", 0) if isinstance(entry, dict) else 0
                cache._memory_fallback[key] = {
                    "value": current + 1,
                    "expires_at": time.time() + self.TTL_24H,
                }
        except Exception as e:
            logger.debug(f"Social proof track error: {e}")

    def track_area_activity(self, area: str):
        """Track activity in an area."""
        try:
            key = f"{self.PREFIX_AREA_ACTIVITY}{area}"
            if cache.redis:
                cache.redis.incr(key)
                cache.redis.expire(key, self.TTL_24H)
            else:
                import time
                entry = cache._memory_fallback.get(key)
                current = entry.get("value", 0) if isinstance(entry, dict) else 0
                cache._memory_fallback[key] = {
                    "value": current + 1,
                    "expires_at": time.time() + self.TTL_24H,
                }
        except Exception as e:
            logger.debug(f"Social proof track error: {e}")

    def get_property_signals(self, property_id: int) -> Dict[str, Any]:
        """Get social proof signals for a property."""
        try:
            views_key = f"{self.PREFIX_PROP_VIEWS}{property_id}"
            analyzes_key = f"{self.PREFIX_PROP_ANALYZES}{property_id}"

            if cache.redis:
                views = int(cache.redis.get(views_key) or 0)
                analyzes = int(cache.redis.get(analyzes_key) or 0)
            else:
                entry = cache._memory_fallback.get(views_key)
                views = entry.get("value", 0) if isinstance(entry, dict) else 0
                entry = cache._memory_fallback.get(analyzes_key)
                analyzes = entry.get("value", 0) if isinstance(entry, dict) else 0

            signals = {}

            if analyzes >= 3:
                signals["analysis_count"] = {
                    "text_en": f"{analyzes} investors analyzed this property today",
                    "text_ar": f"{analyzes} مستثمرين حللوا العقار ده النهاردة",
                    "count": analyzes,
                    "type": "hot",
                }
            elif views >= 5:
                signals["view_count"] = {
                    "text_en": f"{views} investors viewed this property today",
                    "text_ar": f"{views} مستثمرين شافوا العقار ده النهاردة",
                    "count": views,
                    "type": "warm",
                }

            return signals

        except Exception as e:
            logger.debug(f"Social proof get error: {e}")
            return {}

    def get_area_signals(self, area: str) -> Dict[str, Any]:
        """Get social proof signals for an area."""
        try:
            key = f"{self.PREFIX_AREA_ACTIVITY}{area}"
            if cache.redis:
                activity = int(cache.redis.get(key) or 0)
            else:
                entry = cache._memory_fallback.get(key)
                activity = entry.get("value", 0) if isinstance(entry, dict) else 0

            if activity >= 10:
                return {
                    "area_activity": {
                        "text_en": f"{area} is trending — {activity} searches today",
                        "text_ar": f"{area} ترند — {activity} بحث النهاردة",
                        "count": activity,
                        "type": "trending",
                    }
                }
            return {}

        except Exception as e:
            logger.debug(f"Social proof area error: {e}")
            return {}


# Singleton
social_proof = SocialProofService()
