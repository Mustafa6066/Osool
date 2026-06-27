"""
Anomaly Detector — Scrape Data Integrity Guard
-----------------------------------------------
Compares incoming scrape batch statistics against historical baselines.
If median price per area deviates > 30% from recent runs, HALTS the upsert
and triggers alerts (Sentry + Discord webhook).

Prevents corrupted data from reaching the vector database.
"""

import os
import json
import logging
import statistics
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from collections import defaultdict

import httpx

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Statistical anomaly detection for property scrape batches.
    Compares per-area medians against a rolling baseline.
    """

    DEVIATION_THRESHOLD = float(os.getenv("ANOMALY_STRICT_THRESHOLD", "0.30"))  # broad-market refresh
    # Curated/segment feeds (Nawy Now, per-area) run HIGHER than the broad market by
    # design AND share source="nawy" with it — so lenient mode does NOT get a
    # segment-isolated baseline. Instead it (a) flags only a DROP (the
    # down-payment-as-price corruption signature; an expected premium spike is
    # tolerated) and (b) uses a high threshold. Tune via env if a real feed trips it. [I12]
    LENIENT_THRESHOLD = float(os.getenv("ANOMALY_LENIENT_THRESHOLD", "0.65"))
    MIN_SAMPLES_PER_AREA = 3     # need ≥3 incoming props to compute a batch median
    MIN_BASELINE_SAMPLES = 5     # don't trust a baseline computed from < 5 rows [I16]
    BASELINE_WINDOW_DAYS = 45    # baseline = recent market only, not all-time [I16]

    def __init__(self):
        self._baseline_cache: Dict[str, List[float]] = {}

    async def check_batch(
        self,
        incoming_properties: List[Dict],
        session: Any,
        source: Optional[str] = None,
        lenient: bool = False,
    ) -> Dict[str, Any]:
        """
        Compare incoming batch medians against a RECENT, SAME-SOURCE DB baseline.

        lenient=True (curated/segment feeds, e.g. Nawy Now or per-area scrapes):
        uses a higher deviation threshold so the feed's legitimate divergence from
        the broad market is tolerated, while a uniformly-corrupt batch
        (down-payment-as-price) is still caught — instead of bypassing the guard
        entirely (the old behavior, which left the highest-volume feed unprotected). [I12]

        Returns: {"safe": bool, "anomalies": [...], "area_stats": {...}, "mode": str}
        """
        threshold = self.LENIENT_THRESHOLD if lenient else self.DEVIATION_THRESHOLD

        # Group incoming by canonical area. I15: location only — after I14 it is
        # always set ("Unknown" at worst); the old `or compound` fallback created a
        # mismatched bucket that never aligned with the location-keyed baseline.
        area_prices: Dict[str, List[float]] = defaultdict(list)
        for prop in incoming_properties:
            area = (prop.get("location") or "unknown").strip().lower()
            price = prop.get("price", 0)
            if isinstance(price, (int, float)) and price > 0:
                area_prices[area].append(float(price))

        anomalies = []
        area_stats = {}

        for area, prices in area_prices.items():
            if len(prices) < self.MIN_SAMPLES_PER_AREA:
                continue
            if area == "unknown":
                continue  # never baseline-compare the catch-all bucket

            incoming_median = statistics.median(prices)
            area_stats[area] = {
                "count": len(prices),
                "median": incoming_median,
                "min": min(prices),
                "max": max(prices),
            }

            baseline_median = await self._get_baseline_median(area, session, source)
            if baseline_median is None or baseline_median <= 0:
                # No trustworthy baseline yet (first run / too few recent same-source
                # samples). Allow through, but LOG it so a silently-skipped guard is
                # observable (I13 intent). Caveat: if a BULK corrupt batch slips
                # through here it can poison the next run's live-table baseline — the
                # real fix is an immutable per-run baseline (ScrapeRunStats, deferred).
                logger.info("[anomaly] no baseline for '%s' (src=%s) — allowed through", area, source)
                continue

            drop_dev = (baseline_median - incoming_median) / baseline_median  # +ve = a drop
            if lenient:
                # Lenient (curated/segment) mode: a premium feed running HIGH is
                # expected, so only a DROP is suspicious (down-payment-as-price).
                triggered = drop_dev > threshold
                dev = drop_dev
                direction = "DROP"
            else:
                dev = abs(incoming_median - baseline_median) / baseline_median
                triggered = dev > threshold
                direction = "DROP" if incoming_median < baseline_median else "SPIKE"

            if triggered:
                anomaly = {
                    "area": area,
                    "direction": direction,
                    "deviation_pct": round(dev * 100, 1),
                    "incoming_median": incoming_median,
                    "baseline_median": baseline_median,
                    "property_count": len(prices),
                }
                anomalies.append(anomaly)
                logger.error(
                    f"🚨 ANOMALY [{'lenient' if lenient else 'strict'} src={source}]: "
                    f"{area} — {direction} {anomaly['deviation_pct']}% "
                    f"(incoming: {incoming_median:,.0f}, baseline: {baseline_median:,.0f})"
                )

        return {
            "safe": len(anomalies) == 0,
            "anomalies": anomalies,
            "area_stats": area_stats,
            "mode": "lenient" if lenient else "strict",
        }

    async def _get_baseline_median(
        self, area: str, session: Any, source: Optional[str] = None
    ) -> Optional[float]:
        """
        Median price for an area from RECENT, SAME-SOURCE DB rows.

        I15: exact (case-insensitive) zone equality, not a substring LIKE that
             conflated "zayed"→{Sheikh Zayed, New Zayed} and "cairo"→{New Cairo, …}.
        I16: restricted to a recent window + a minimum sample floor, so a single
             stale row cannot define the baseline. NOTE: window+floor do NOT stop a
             BULK corrupt batch (≥ MIN_BASELINE_SAMPLES rows) that slipped through on
             a no-baseline run from poisoning a future baseline — that needs the
             deferred immutable per-run baseline (ScrapeRunStats).
        I12: scoped to the same source when given, so the baseline excludes other
             feeds (e.g. Aqarmap). NOTE: Nawy Now and broad Nawy share source="nawy",
             so this does NOT isolate the curated segment — lenient mode's drops-only
             rule + threshold do that, not this scope.
        """
        try:
            from datetime import timedelta

            from sqlalchemy import and_, func, select

            from app.models import Property

            cutoff = datetime.now(timezone.utc) - timedelta(days=self.BASELINE_WINDOW_DAYS)
            conds = [
                Property.is_available == True,  # noqa: E712
                func.lower(Property.location) == area,
                Property.price > 0,
                Property.scraped_at >= cutoff,
            ]
            if source:
                conds.append(Property.source == source)

            result = await session.execute(
                select(
                    func.percentile_cont(0.5).within_group(Property.price),
                    func.count(),
                ).where(and_(*conds))
            )
            # Aggregate (no GROUP BY) always returns exactly one (median, count) row;
            # an empty match yields (NULL, 0), handled by the checks below.
            median, count = result.one()
            if not median or count < self.MIN_BASELINE_SAMPLES:
                return None  # too few recent same-source samples to trust a baseline
            return float(median)
        except Exception as e:
            logger.warning(f"Baseline query failed for {area}: {e}")
            return None

    async def save_run_stats(
        self,
        run_id: str,
        area_stats: Dict,
        session: Any,
    ) -> None:
        """Persist scrape run statistics for future baseline lookups."""
        try:
            from app.models import ScrapeRunStats
            stats_record = ScrapeRunStats(
                run_id=run_id,
                stats_json=json.dumps(area_stats, ensure_ascii=False),
                created_at=datetime.now(timezone.utc),
            )
            session.add(stats_record)
            await session.commit()
            logger.info(f"📊 Saved run stats for {len(area_stats)} areas (run={run_id})")
        except ImportError:
            # ScrapeRunStats model not yet created — use DB baseline only
            logger.debug("ScrapeRunStats model not available; skipping stats persistence")
        except Exception as e:
            logger.warning(f"Failed to save run stats: {e}")
            try:
                await session.rollback()
            except Exception:
                pass


async def send_alert(
    title: str,
    message: str,
    severity: str = "warning",
) -> None:
    """
    Send alert to Sentry and Discord webhook.
    """
    # Sentry alert
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("alert_type", "scraper_anomaly")
            scope.set_tag("severity", severity)
            scope.set_extra("details", message)
            level = "error" if severity == "critical" else "warning"
            sentry_sdk.capture_message(f"[Scraper] {title}", level=level)
    except Exception as e:
        logger.debug(f"Sentry alert skipped: {e}")

    # Discord webhook
    discord_url = os.getenv("DISCORD_ALERT_WEBHOOK_URL")
    if discord_url:
        try:
            color = 0xFF0000 if severity == "critical" else 0xFFA500
            payload = {
                "embeds": [{
                    "title": f"🚨 Osool Scraper Alert: {title}",
                    "description": message[:2000],
                    "color": color,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "footer": {"text": f"Severity: {severity}"},
                }]
            }
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(discord_url, json=payload)
                if resp.status_code < 300:
                    logger.info(f"📢 Discord alert sent: {title}")
                else:
                    logger.warning(f"Discord webhook returned {resp.status_code}")
        except Exception as e:
            logger.warning(f"Discord alert failed: {e}")


# Singleton
anomaly_detector = AnomalyDetector()
