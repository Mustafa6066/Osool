"""
Canonical property → embedding-text builder. [audit X2]

THE single source of truth for the text that gets embedded for a Property's
semantic-search vector. Three paths used to build this text independently and had
DIVERGED:

  * ingest_data_postgres.create_embedding_text  — newline, Title-case, WITH price
  * services/embedding_backfill._build_embedding_text — newline, Title-case, WITH price
  * scripts/embed_backfill._canonical_text       — pipe, lowercase, NO price, desc[:600]

So the *same* row embedded to a *different* vector depending on which path touched it,
quietly degrading semantic recall (query vectors match an inconsistent corpus).

This module unifies them on the **scripts/embed_backfill format** (pipe-joined,
lowercase labels, no price). Going forward EVERY path emits identical text, so the
corpus stops diverging.

NOTE on existing rows: the live corpus is currently HETEROGENEOUS. repository.py stores
embedding=NULL at scrape time, but the daily APScheduler cron (scheduler.py
daily_embedding_backfill) populates them via the IN-PROCESS backfill
(services/embedding_backfill), whose format X2 just CHANGED (it was newline+Title-case+
price). So pre-X2 rows are in the old format and won't converge until they naturally
churn. A ONE-TIME full re-embed (`UPDATE properties SET embedding = NULL`, then let the
backfill repopulate) is required to make the whole corpus consistent — X2 alone only
fixes go-forward.

Raw price/payment numerics are intentionally excluded: they add token noise without
helping semantic match, and budget is handled by SQL filters in the hybrid query.

Accepts a Property ORM object OR a dict (snake_case, or the legacy camelCase used by
ingest_data_postgres) — field access is normalized via _first(), so all three callers
produce byte-identical text for the same row.
"""
from __future__ import annotations

from typing import Any


def _first(src: Any, *names: str):
    """First non-None / non-empty value among `names`, read from an ORM obj or dict."""
    for n in names:
        v = src.get(n) if isinstance(src, dict) else getattr(src, n, None)
        if v is not None and v != "":
            return v
    return None


def build_property_embedding_text(src: Any) -> str:
    """
    Stable embedding text for one property. Identifying fields first, then descriptive.
    Empty fields are skipped; the description is capped at 600 chars to bound token cost.
    Output format (pipe-joined, lowercase labels) matches the live backfill corpus.
    """
    parts: list[str] = []

    def add(label: str, *names: str) -> None:
        v = _first(src, *names)
        if v is None:
            return
        s = str(v).strip()
        if s:
            parts.append(f"{label}: {s}")

    add("title", "title")
    add("type", "type")
    add("compound", "compound")
    add("developer", "developer")
    add("location", "location")
    add("size_sqm", "size_sqm", "area")
    add("bedrooms", "bedrooms")
    add("bathrooms", "bathrooms")
    add("finishing", "finishing")
    add("delivery_date", "delivery_date", "deliveryDate")
    if _first(src, "is_nawy_now", "isNawyNow"):
        parts.append("tag: nawy_now (instant delivery)")
    if _first(src, "is_delivered", "isDelivered"):
        parts.append("tag: delivered")
    add("sale_type", "sale_type", "saleType")
    desc = _first(src, "description")
    if desc:
        s = str(desc).strip()
        if s:
            parts.append(f"description: {s[:600]}")
    return " | ".join(parts)
