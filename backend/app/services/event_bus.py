"""
Event Bus - Redis Pub/Sub for Real-Time Notifications
------------------------------------------------------
Channels:
- property.price_change  → Price drop/increase alerts
- property.new_listing   → New property matching saved search
- search.match           → Saved search found new results
- user.achievement       → Badge unlocked, level up, XP awarded
- user.xp               → XP gain events (for toast notifications)
"""

import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class EventBus:
    """Async Redis Pub/Sub event bus for real-time notifications."""

    def __init__(self):
        self._redis = None
        self._pubsub = None

    async def _get_redis(self):
        """Lazy-init async Redis connection."""
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(REDIS_URL, decode_responses=True)
                await self._redis.ping()
                logger.info("EventBus: Redis connected")
            except Exception as e:
                logger.warning(f"EventBus: Redis unavailable ({e}), events will be dropped")
                self._redis = None
        return self._redis

    async def publish(self, channel: str, data: Dict[str, Any]) -> bool:
        """Publish an event to a channel."""
        redis = await self._get_redis()
        if not redis:
            return False
        try:
            payload = json.dumps({
                **data,
                "timestamp": datetime.utcnow().isoformat(),
                "channel": channel,
            }, ensure_ascii=False, default=str)
            await redis.publish(channel, payload)
            logger.debug(f"EventBus: Published to {channel}")
            return True
        except Exception as e:
            logger.error(f"EventBus: Publish failed on {channel}: {e}")
            return False

    async def subscribe(self, *channels: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribe to channels and yield events as they arrive."""
        redis = await self._get_redis()
        if not redis:
            return

        pubsub = redis.pubsub()
        await pubsub.subscribe(*channels)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        yield data
                    except json.JSONDecodeError:
                        continue
        finally:
            await pubsub.unsubscribe(*channels)
            await pubsub.close()

    # ─── Convenience Publishers ─────────────────────────────────

    async def emit_xp_awarded(self, user_id: int, xp: int, total_xp: int, action: str):
        """Emit XP gain event."""
        await self.publish("user.xp", {
            "user_id": user_id,
            "awarded": xp,
            "total": total_xp,
            "action": action,
        })

    async def emit_achievement_unlocked(
        self, user_id: int, key: str, title_en: str, title_ar: str, xp_reward: int
    ):
        """Emit achievement unlock event."""
        await self.publish("user.achievement", {
            "user_id": user_id,
            "key": key,
            "title_en": title_en,
            "title_ar": title_ar,
            "xp_reward": xp_reward,
        })

    async def emit_level_up(self, user_id: int, new_level: str, new_level_ar: str):
        """Emit level-up event."""
        await self.publish("user.achievement", {
            "user_id": user_id,
            "type": "level_up",
            "new_level": new_level,
            "new_level_ar": new_level_ar,
        })

    async def emit_price_change(self, property_id: int, old_price: float, new_price: float, location: str):
        """Emit property price change event."""
        await self.publish("property.price_change", {
            "property_id": property_id,
            "old_price": old_price,
            "new_price": new_price,
            "change_pct": round((new_price - old_price) / old_price * 100, 2),
            "location": location,
        })

    async def emit_search_match(self, user_id: int, search_id: int, matches: int):
        """Emit saved search match event."""
        await self.publish("search.match", {
            "user_id": user_id,
            "search_id": search_id,
            "new_matches": matches,
        })


# Singleton
event_bus = EventBus()
