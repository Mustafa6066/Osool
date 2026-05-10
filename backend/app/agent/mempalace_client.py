"""
MemPalace async HTTP client for the Osool Platform backend.

Wraps the MemPalace sidecar (FastAPI/ChromaDB at MEMPALACE_URL).
All methods degrade gracefully — they log warnings and return empty
results if the sidecar is unreachable, so the main app never breaks.

Usage:
    from app.agent.mempalace_client import recall, remember, walk

    hits = await recall("user:u123", "sea-view compound price")
    await remember("user:u123", "lead-history", "user asked about sea-view", score=0.9)
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_MEMPALACE_URL = os.getenv("MEMPALACE_URL", "http://localhost:8100")
_TIMEOUT = httpx.Timeout(5.0)


def _client() -> httpx.AsyncClient:
    """Lazily create a short-lived client (no keep-alive pool needed here)."""
    return httpx.AsyncClient(base_url=_MEMPALACE_URL, timeout=_TIMEOUT)


async def recall(
    wing: str,
    query: str,
    k: int = 5,
    room: str | None = None,
) -> list[dict[str, Any]]:
    """
    Semantic search over a memory wing.

    Args:
        wing:  e.g. "user:u123" or "segment:high-net-worth"
        query: natural-language query
        k:     max results
        room:  optional room filter within the wing

    Returns:
        List of memory dicts with keys: id, text, score, metadata
    """
    payload: dict[str, Any] = {"wing": wing, "query": query, "k": k}
    if room:
        payload["room"] = room

    try:
        async with _client() as c:
            resp = await c.post("/mcp/recall", json=payload)
            resp.raise_for_status()
            return resp.json().get("hits", [])
    except Exception as exc:  # noqa: BLE001
        logger.warning("MemPalace recall failed: %s", exc)
        return []


async def remember(
    wing: str,
    room: str,
    text: str,
    **metadata: Any,
) -> str | None:
    """
    Store a memory in a wing/room.

    Args:
        wing:     e.g. "user:u123"
        room:     e.g. "lead-history", "chat", "search-queries"
        text:     the text to embed and store
        **metadata: arbitrary JSON-serialisable key/value pairs

    Returns:
        The drawer ID (UUID) assigned by MemPalace, or None on failure.
    """
    payload: dict[str, Any] = {"wing": wing, "room": room, "text": text, **metadata}

    try:
        async with _client() as c:
            resp = await c.post("/mcp/remember", json=payload)
            resp.raise_for_status()
            return resp.json().get("id")
    except Exception as exc:  # noqa: BLE001
        logger.warning("MemPalace remember failed: %s", exc)
        return None


async def walk(
    wing: str,
    room: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Chronological listing of memories in a wing/room (no embedding needed).

    Returns:
        List of memory dicts, newest-first.
    """
    try:
        async with _client() as c:
            resp = await c.get(
                "/mcp/walk",
                params={"wing": wing, "room": room, "limit": limit},
            )
            resp.raise_for_status()
            return resp.json().get("items", [])
    except Exception as exc:  # noqa: BLE001
        logger.warning("MemPalace walk failed: %s", exc)
        return []
