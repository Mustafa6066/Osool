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

    DEVIATION_THRESHOLD = 0.30  # 30% — flag as anomaly
    MIN_SAMPLES_PER_AREA = 3   # Need at least 3 props to compute meaningful median

    def __init__(self):
        self._baseline_cache: Dict[str, List[float]] = {}

    async def check_batch(
        self,
        incoming_properties: List[Dict],
        session: Any,
    ) -> Dict[str, Any]:
        """
        Compare incoming batch medians against DB baselines.

        Returns:
            {
                "safe": True/False,
                "anomalies": [...],
                "area_stats": {...},
            }
        """
        # Group incoming by area
        area_prices: Dict[str, List[float]] = defaultdict(list)
        for prop in incoming_properties:
            area = (prop.get("location") or prop.get("compound") or "unknown").strip().lower()
            price = prop.get("price", 0)
            if isinstance(price, (int, float)) and price > 0:
                area_prices[area].append(float(price))

        anomalies = []
        area_stats = {}

        for area, prices in area_prices.items():
            if len(prices) < self.MIN_SAMPLES_PER_AREA:
                continue

            incoming_median = statistics.median(prices)
            area_stats[area] = {
                "count": len(prices),
                "median": incoming_median,
                "min": min(prices),
                "max": max(prices),
            }

            # Get baseline from DB
            baseline_median = await self._get_baseline_median(area, session)
            if baseline_median is None or baseline_median <= 0:
                continue  # No baseline yet — first run, allow through

            deviation = abs(incoming_median - baseline_median) / baseline_median

            if deviation > self.DEVIATION_THRESHOLD:
                direction = "DROP" if incoming_median < baseline_median else "SPIKE"
                anomaly = {
                    "area": area,
                    "direction": direction,
                    "deviation_pct": round(deviation * 100, 1),
                    "incoming_median": incoming_median,
                    "baseline_median": baseline_median,
                    "property_count": len(prices),
                }
                anomalies.append(anomaly)
                logger.error(
                    f"🚨 ANOMALY: {area} — {direction} {anomaly['deviation_pct']}% "
                    f"(incoming: {incoming_median:,.0f}, baseline: {baseline_median:,.0f})"
                )

        return {
            "safe": len(anomalies) == 0,
            "anomalies": anomalies,
            "area_stats": area_stats,
        }

    async def _get_baseline_median(self, area: str, session: Any) -> Optional[float]:
        """Get the median price for an area from existing DB properties."""
        try:
            from sqlalchemy import select, func
            from app.models import Property

            result = await session.execute(
                select(func.percentile_cont(0.5).within_group(Property.price))
                .filter(
                    Property.is_available == True,
                    func.lower(Property.location).contains(area),
                    Property.price > 0,
                )
            )
            median = result.scalar_one_or_none()
            return float(median) if median else None
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
