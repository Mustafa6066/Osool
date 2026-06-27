"""
Ingestion adapter — funnels spider output into the existing pipeline.

Reuses untouched:
  - app.ingestion.scraper_schemas.validate_raw_batch (input gate)
  - app.ingestion.deterministic_normalizer.normalize_properties / normalize_unit_list
  - app.ingestion.repository.upsert_properties (differential hash upsert)

Publishes a Redis alert to scraper:health:alerts when the null-rate
breaches the threshold defined in scraper_schemas.ScrapeHealthReport.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as aioredis

from app.ingestion.deterministic_normalizer import (
    NormalizationResult,
    normalize_properties,
    normalize_unit_list,
)
from app.ingestion.repository import UpsertResult, upsert_properties
from app.ingestion.scraper_schemas import validate_raw_batch
from settings import HEALTH_ALERT_KEEP, HEALTH_ALERT_KEY, REDIS_URL

logger = logging.getLogger(__name__)


@dataclass
class FlushResult:
    site: str
    run_id: str
    upserted: UpsertResult
    valid_count: int
    rejected_count: int
    alert_sent: bool


async def flush(
    raw_properties: list[dict],
    site: str,
    skip_anomaly_check: bool = False,
    run_id: str | None = None,
) -> FlushResult:
    """
    Validate → normalize → upsert one batch of raw spider output.

    `raw_properties` shape:
      - For nawy: list of envelope dicts where each envelope is a __NEXT_DATA__
        blob marked with _nawy_compound_envelope=True.
      - For aqarmap: list of flat unit dicts.

    skip_anomaly_check: pass True for narrow per-area scrapes where the
        incoming batch's median price legitimately diverges from the
        broad-market baseline (per-compound new-developer pricing, niche
        property segments). The anomaly detector compares against the
        whole-market historical median and otherwise halts the upsert.
    """
    # I5: callers (on-demand worker, per-area cron) pass the source's current
    # stale-safe run_id so refreshed rows are not delisted by the next sweep. A
    # fresh id is minted only when no anchor exists yet (then no sweep runs).
    run_id = run_id or str(uuid.uuid4())

    # Split envelopes vs flat units so we can call the correct normalizer for each.
    envelopes = [p for p in raw_properties if p.get("_nawy_compound_envelope")]
    flat_units = [p for p in raw_properties if not p.get("_nawy_compound_envelope")]

    # Aqarmap path (and any flat-unit producer): validate at the raw stage.
    if flat_units:
        valid_units, report = validate_raw_batch(flat_units)
    else:
        valid_units, report = [], None

    # Normalize
    normalized = []

    if envelopes:
        for env in envelopes:
            try:
                res: NormalizationResult = await normalize_properties(env)
                normalized.extend(res.properties)
            except Exception as exc:
                logger.exception("[ingestion] envelope normalize failed: %s", exc)

    if valid_units:
        res = normalize_unit_list(valid_units, source_url=f"{site}-batch")
        normalized.extend(res.properties)

    logger.info(
        "[ingestion] %s run=%s → %d normalized properties (from %d envelopes + %d flat units)",
        site, run_id[:8], len(normalized), len(envelopes), len(flat_units),
    )

    if not normalized:
        return FlushResult(
            site=site,
            run_id=run_id,
            upserted=UpsertResult(),
            valid_count=0,
            rejected_count=(report.rejected if report else 0),
            alert_sent=False,
        )

    # Attribute rows to their real feed (I22 / I31) so source-scoped stale-
    # marking and per-source price history are correct. `site` is already the
    # canonical 'nawy' | 'aqarmap'.
    upsert_result = await upsert_properties(
        normalized, run_id=run_id, skip_anomaly_check=skip_anomaly_check, source=site
    )

    alert_sent = False
    if report and report.needs_alert:
        alert_sent = await _push_health_alert(site, run_id, report)

    return FlushResult(
        site=site,
        run_id=run_id,
        upserted=upsert_result,
        valid_count=len(normalized),
        rejected_count=(report.rejected if report else 0),
        alert_sent=alert_sent,
    )


async def _push_health_alert(site: str, run_id: str, report: Any) -> bool:
    """LPUSH a JSON alert and trim to HEALTH_ALERT_KEEP. Best-effort."""
    payload = {
        "site": site,
        "run_id": run_id,
        "summary": report.summary,
        "null_rates": {
            "price": report.null_rate_price,
            "title": report.null_rate_title,
            "location": report.null_rate_location,
            "area": report.null_rate_area,
        },
        "rejected": report.rejected,
        "total_raw": report.total_raw,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        client = aioredis.from_url(REDIS_URL, decode_responses=True)
        async with client:
            await client.lpush(HEALTH_ALERT_KEY, json.dumps(payload))
            await client.ltrim(HEALTH_ALERT_KEY, 0, HEALTH_ALERT_KEEP - 1)
        logger.error("[ingestion] HEALTH ALERT pushed for %s: %s", site, report.summary)
        return True
    except Exception as exc:
        logger.error("[ingestion] failed to push health alert: %s", exc)
        return False


async def dry_run_print(raw_properties: list[dict], site: str) -> None:
    """Print what would be upserted without touching the DB."""
    print(f"\n──── DRY RUN: {site} ({len(raw_properties)} raw units) ────")
    envelopes = [p for p in raw_properties if p.get("_nawy_compound_envelope")]
    flat_units = [p for p in raw_properties if not p.get("_nawy_compound_envelope")]

    for env in envelopes:
        res = await normalize_properties(env)
        for prop in res.properties[:5]:
            print(json.dumps(prop.model_dump(), default=str, indent=2))

    if flat_units:
        valid_units, report = validate_raw_batch(flat_units)
        res = normalize_unit_list(valid_units, source_url=f"{site}-dryrun")
        for prop in res.properties[:5]:
            print(json.dumps(prop.model_dump(), default=str, indent=2))
        if report:
            print(f"\nHealth: {report.summary}")
