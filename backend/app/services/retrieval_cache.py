"""
L5 — Retrieval cache + freshness invalidator.

Two roles in one module:

1. Caching layer the orchestrator (property_retrieval.retrieve) checks
   before doing any SQL work. Keyed by the canonical StructuredQuery
   hash so semantically identical prompts collide.

2. Invalidator hook for the scraper — when repository.upsert_properties
   updates a row whose content_hash changed, we drop the cached search
   results so the next chat turn sees the new price.

Pure Redis. Zero API cost. Degrades gracefully to the in-memory fallback
that cache.RedisClient already provides.
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict
from typing import Optional

from app.services.cache import cache
from app.services.property_retrieval import (
    DecisionAugmentedHit,
    RankedHit,
    RetrievalResponse,
    canonical_query_hash,
)
from app.services.zero_token_intent import StructuredQuery

logger = logging.getLogger(__name__)


# Tunables (env-overridable for ops without redeploy)
SEARCH_CACHE_TTL_S = int(os.getenv("RETRIEVAL_CACHE_TTL", "300"))     # 5 min
DICT_CACHE_TTL_S = int(os.getenv("RETRIEVAL_DICT_TTL", "3600"))      # 1 hr

# Key prefixes — single tier, easy to scan/flush per type.
PFX_SEARCH = "search:result:"
PFX_DICT = "retrieval:dict:"
PFX_COMPOUND_MEAN = "retrieval:compound_mean:"
INDEX_KEY = "retrieval:search_keys_by_property"   # SADD per property_id


# ─────────────────────────────────────────────────────────────────────────────
# Hot-path: cache get / set on the search result
# ─────────────────────────────────────────────────────────────────────────────

def get_cached_response(
    structured_query: StructuredQuery, ref_property_id: Optional[int] = None,
) -> Optional[RetrievalResponse]:
    """
    Looks up a previously-cached RetrievalResponse by canonical hash.
    Returns None on miss. Never raises (best-effort).
    """
    try:
        key = PFX_SEARCH + canonical_query_hash(structured_query, ref_property_id)
        payload = cache.get_json(key)
        if not payload:
            return None
        # Deserialize
        sq = StructuredQuery(**payload["structured_query"])
        hits = [DecisionAugmentedHit(**h) for h in payload["hits"]]
        reserve = [RankedHit(**r) for r in payload["reserve"]]
        diagnostics = payload.get("diagnostics", {})
        diagnostics["cache_hit"] = True
        return RetrievalResponse(
            structured_query=sq,
            hits=hits,
            reserve=reserve,
            diagnostics=diagnostics,
        )
    except Exception as exc:
        logger.debug("[retrieval_cache] get miss/error: %s", exc)
        return None


def set_cached_response(
    structured_query: StructuredQuery,
    response: RetrievalResponse,
    ref_property_id: Optional[int] = None,
) -> None:
    """
    Caches a RetrievalResponse for SEARCH_CACHE_TTL_S seconds. Also indexes
    the property_ids included in this result so the invalidator can drop
    every cached search that mentions a changed property.
    """
    try:
        key = PFX_SEARCH + canonical_query_hash(structured_query, ref_property_id)
        payload = {
            "structured_query": asdict(structured_query),
            "hits": [asdict(h) for h in response.hits],
            "reserve": [asdict(r) for r in response.reserve],
            "diagnostics": response.diagnostics,
            "cached_at": time.time(),
        }
        cache.set_json(key, payload, ttl=SEARCH_CACHE_TTL_S)

        # Reverse index — property_id → set of search keys that contain it
        property_ids: set[int] = set()
        for h in response.hits:
            property_ids.add(h.property_id)
        for r in response.reserve:
            property_ids.add(r.property_id)
        if property_ids and cache.redis is not None:
            for pid in property_ids:
                cache.redis.sadd(f"{INDEX_KEY}:{pid}", key)
                # Auto-expire the index entry too so it doesn't grow forever
                cache.redis.expire(f"{INDEX_KEY}:{pid}", SEARCH_CACHE_TTL_S * 2)
    except Exception as exc:
        logger.debug("[retrieval_cache] set failed: %s", exc)


# ─────────────────────────────────────────────────────────────────────────────
# Dictionary cache (compound + developer names for L1 lookup)
# ─────────────────────────────────────────────────────────────────────────────

def get_dict(name: str) -> Optional[list[str]]:
    """name in {'compounds','developers','locations'}."""
    try:
        return cache.get_json(PFX_DICT + name)
    except Exception:
        return None


def set_dict(name: str, values: list[str]) -> None:
    try:
        cache.set_json(PFX_DICT + name, values, ttl=DICT_CACHE_TTL_S)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Freshness invalidator — called by repository.upsert_properties on hash diff
# ─────────────────────────────────────────────────────────────────────────────

def invalidate_property(property_id: int) -> int:
    """
    Drops every cached search result that includes this property_id.
    Returns the number of keys dropped (best-effort; 0 on Redis-down).
    """
    if cache.redis is None:
        return 0
    try:
        index_key = f"{INDEX_KEY}:{property_id}"
        keys = cache.redis.smembers(index_key)
        dropped = 0
        for k in keys:
            if cache.redis.delete(k):
                dropped += 1
        cache.redis.delete(index_key)
        if dropped:
            logger.info("[retrieval_cache] invalidated %d search keys for property %s", dropped, property_id)
        return dropped
    except Exception as exc:
        logger.warning("[retrieval_cache] invalidate_property %s failed: %s", property_id, exc)
        return 0


def invalidate_compound(compound_name: str) -> None:
    """Drops the compound mean cache entry; called when a compound's price profile shifts."""
    if cache.redis is None or not compound_name:
        return
    try:
        cache.redis.delete(PFX_COMPOUND_MEAN + compound_name)
    except Exception:
        pass


def publish_property_changed(property_id: int, hash_old: Optional[str], hash_new: str) -> None:
    """
    Fan-out a Redis pubsub event so any subscribers (this module's invalidator,
    plus future workers like the embedding refresh job) react.

    The repository.upsert_properties path calls this synchronously after each
    row whose content_hash flipped. Cost: 1 PUBLISH per changed row (μs).
    """
    if cache.redis is None:
        return
    try:
        cache.redis.publish(
            "scraper:property_changed",
            json.dumps({
                "property_id": property_id,
                "hash_old": hash_old,
                "hash_new": hash_new,
                "ts": time.time(),
            }),
        )
    except Exception as exc:
        logger.debug("[retrieval_cache] publish failed: %s", exc)


# Sync convenience for the upsert path — drops cache + publishes in one call.
def on_property_changed(property_id: int, hash_old: Optional[str], hash_new: str) -> None:
    invalidate_property(property_id)
    publish_property_changed(property_id, hash_old, hash_new)
